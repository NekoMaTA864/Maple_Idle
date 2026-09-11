"""Safety coverage for schema-versioned, atomic Player persistence."""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from player_data import Player
from player_save import (
    SCHEMA_VERSION,
    load_player_from_file,
    migrate_save_data,
    player_to_dict,
    save_player_to_file,
    validate_save_data,
)


class TestSavePersistenceHardening(unittest.TestCase):
    def setUp(self):
        self.path = Path(SRC_DIR) / ".save_persistence_hardening_test.json"
        self._remove_test_files()

    def tearDown(self):
        self._remove_test_files()

    def _remove_test_files(self):
        for suffix in ("", ".bak", ".tmp"):
            candidate = Path(f"{self.path}{suffix}")
            if candidate.exists():
                candidate.unlink()

    def test_legacy_v0_migrates_to_v1_without_losing_existing_fields(self):
        source = Player()
        source.gold = 4321
        legacy = player_to_dict(source)
        legacy.pop("schema_version")
        legacy["unknown_legacy_field"] = {"kept": True}

        migrated = migrate_save_data(legacy)

        self.assertNotIn("schema_version", legacy)
        self.assertEqual(migrated["schema_version"], SCHEMA_VERSION)
        self.assertEqual(migrated["gold"], 4321)
        self.assertEqual(migrated["unknown_legacy_field"], {"kept": True})

        self.path.write_text(json.dumps(legacy), encoding="utf-8")
        restored = Player()
        self.assertIsNone(load_player_from_file(restored, str(self.path)))
        self.assertEqual(restored.gold, 4321)

    def test_already_v1_migration_is_a_content_noop(self):
        payload = player_to_dict(Player())

        self.assertEqual(migrate_save_data(payload), payload)

    def test_validation_rejects_unsupported_future_schema_and_malformed_core_blocks(self):
        with self.assertRaisesRegex(ValueError, "Unsupported save schema"):
            migrate_save_data({"schema_version": SCHEMA_VERSION + 1})
        with self.assertRaisesRegex(ValueError, "inventory"):
            validate_save_data({"schema_version": SCHEMA_VERSION, "inventory": {}})

    def test_load_rejects_json_root_that_is_not_a_dict_without_mutating_player(self):
        player = Player()
        player.gold = 777

        self.path.write_text("[]", encoding="utf-8")

        self.assertIsNone(load_player_from_file(player, str(self.path)))

        self.assertEqual(player.gold, 777)

    def test_load_rejects_future_schema_without_mutating_player(self):
        player = Player()
        player.gold = 777

        self.path.write_text(json.dumps({"schema_version": SCHEMA_VERSION + 1}), encoding="utf-8")

        self.assertIsNone(load_player_from_file(player, str(self.path)))

        self.assertEqual(player.gold, 777)

    def test_v1_file_round_trip_creates_schema_versioned_save(self):
        player = Player()
        player.gold = 24680

        self.assertTrue(save_player_to_file(player, str(self.path)))

        saved = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(saved["schema_version"], SCHEMA_VERSION)

        restored = Player()
        self.assertIsNone(load_player_from_file(restored, str(self.path)))
        self.assertEqual(restored.gold, 24680)

    def test_overwrite_creates_previous_backup_before_replacing_primary_save(self):
        old_player = Player()
        old_player.gold = 101
        new_player = Player()
        new_player.gold = 202

        old_payload = json.dumps(player_to_dict(old_player), indent=2, ensure_ascii=False)
        self.path.write_text(old_payload, encoding="utf-8")

        self.assertTrue(save_player_to_file(new_player, str(self.path)))

        self.assertEqual((Path(f"{self.path}.bak")).read_text(encoding="utf-8"), old_payload)
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8"))["gold"], 202)

    def test_failed_atomic_replace_keeps_primary_save_intact(self):
        player = Player()
        player.gold = 202

        old_payload = '{"legacy": "original"}'
        self.path.write_text(old_payload, encoding="utf-8")

        with patch("player_save.os.replace", side_effect=OSError("replace failed")):
            self.assertFalse(save_player_to_file(player, str(self.path)))

        self.assertEqual(self.path.read_text(encoding="utf-8"), old_payload)
        self.assertEqual(Path(f"{self.path}.bak").read_text(encoding="utf-8"), old_payload)
        self.assertFalse(Path(f"{self.path}.tmp").exists())


if __name__ == "__main__":
    unittest.main()
