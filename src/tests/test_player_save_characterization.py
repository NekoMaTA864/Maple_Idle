"""Characterization coverage for the current Player JSON persistence contract."""

import ast
import json
import os
import sys
from pathlib import Path
import unittest
from unittest.mock import mock_open, patch

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from item_system import Item
from player_data import Player
from player_save import (
    get_default_save_path,
    load_player_from_file,
    player_load_dict,
    player_to_dict,
    save_player_to_file,
)


class TestPlayerSaveCharacterization(unittest.TestCase):
    def test_new_player_default_state_and_serialized_shape(self):
        player = Player()
        data = player_to_dict(player)

        self.assertEqual(player.name, "新楓之谷遠征隊")
        self.assertEqual((player.level, player.exp, player.gold), (1, 0, 100))
        self.assertEqual((player.stat_atk, player.stat_def, player.stat_hp, player.stat_crit), (6, 6, 6, 6))
        self.assertEqual(len(player.team), 7)
        self.assertEqual(data["team_classes"], [member.class_id for member in player.team])
        self.assertEqual(data["inventory"], [])
        self.assertEqual(set(data["equipped"]), set(player.equipped))
        self.assertIn("last_save_time", data)
        self.assertEqual(data["schema_version"], 1)

    def test_round_trip_preserves_current_equipment_inventory_progression_party_skills_and_symbols(self):
        player = Player()
        player.name = "保存測試隊"
        player.level = 200
        player.exp = 54321
        player.gold = 987654
        player.stat_atk = 21
        player.stat_def = 22
        player.stat_hp = 23
        player.stat_crit = 24
        player.free_points = 7
        player.equipped["weapon"] = Item("weapon", "legendary", 200, "測試武器", {"attack": 321})
        player.inventory = [Item("ring", "epic", 150, "測試戒指", {"attack": 12})]
        player.slot_enhancements["weapon"] = 15
        player.slot_potentials["weapon"]["main"]["rank"] = "legendary"
        player.slot_scrolls["weapon"]["count"] = 2
        player.abby_scrolls = {"R": 3}
        player.cube_inventory = {"bright": 4}
        player.arc_symbols["vanishing"] = 5
        player.aut_symbols["cernium"] = 2
        player.symbol_fragments["vanishing"] = 17
        player.set_slot_class(0, "bowmaster")
        player.team[0].set_equipped_skills(player.team[0].get_available_skills()[1:4])

        restored = Player()
        player_load_dict(restored, player_to_dict(player))

        self.assertEqual((restored.name, restored.level, restored.exp, restored.gold), ("保存測試隊", 200, 54321, 987654))
        self.assertEqual((restored.stat_atk, restored.stat_def, restored.stat_hp, restored.stat_crit, restored.free_points), (21, 22, 23, 24, 7))
        self.assertEqual(restored.equipped["weapon"].base_name, "測試武器")
        self.assertEqual(restored.inventory[0].base_name, "測試戒指")
        self.assertEqual(restored.slot_enhancements["weapon"], 15)
        self.assertEqual(restored.slot_potentials["weapon"]["main"]["rank"], "legendary")
        self.assertEqual(restored.slot_scrolls["weapon"]["count"], 2)
        self.assertEqual(restored.abby_scrolls, {"R": 3})
        self.assertEqual(restored.cube_inventory, {"bright": 4})
        self.assertEqual(restored.arc_symbols["vanishing"], 5)
        self.assertEqual(restored.aut_symbols["cernium"], 2)
        self.assertEqual(restored.symbol_fragments["vanishing"], 17)
        self.assertEqual(restored.team[0].class_id, "bowmaster")
        self.assertEqual(
            [skill.skill_id for skill in restored.team[0].get_active_skills()],
            [skill.skill_id for skill in player.team[0].get_active_skills()],
        )

    def test_missing_optional_fields_keep_scalar_defaults_but_clear_saved_collections(self):
        player = Player()
        player_load_dict(player, {})

        self.assertEqual((player.name, player.level, player.exp, player.gold), ("新楓之谷遠征隊", 1, 0, 100))
        self.assertEqual(player.inventory, [])
        self.assertTrue(all(item is None for item in player.equipped.values()))
        self.assertEqual(player.abby_scrolls, {})
        self.assertEqual(player.cube_inventory, {})
        self.assertEqual(len(player.team), 7)

    def test_unknown_save_fields_are_ignored(self):
        player = Player()
        data = player_to_dict(player)
        data["unknown_future_system"] = {"version": 999, "payload": ["ignored"]}

        restored = Player()
        player_load_dict(restored, data)

        self.assertFalse(hasattr(restored, "unknown_future_system"))
        self.assertEqual(restored.level, player.level)

    def test_legacy_short_team_is_expanded_with_existing_member_type(self):
        source = Player()
        data = player_to_dict(source)
        data["team_classes"] = data["team_classes"][:5]
        restored = Player()
        restored.team = restored.team[:5]

        player_load_dict(restored, data)

        self.assertEqual(len(restored.team), 7)
        self.assertTrue(all(type(member) is type(source.team[0]) for member in restored.team))
        self.assertEqual([member.slot_idx for member in restored.team], list(range(7)))

    def test_invalid_json_file_returns_none_without_loading(self):
        player = Player()
        path = "broken.json"
        with patch("player_save.os.path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data="{not valid json")
        ):
            result = load_player_from_file(player, path)

        self.assertIsNone(result)
        self.assertEqual(player.level, 1)

    def test_default_save_path_is_src_saves_savegame_json(self):
        path = get_default_save_path()

        self.assertEqual(os.path.basename(path), "savegame.json")
        self.assertEqual(os.path.basename(os.path.dirname(path)), "saves")
        self.assertEqual(os.path.basename(os.path.dirname(os.path.dirname(path))), "src")

    def test_release_save_dir_environment_override_keeps_packaged_saves_outside_game(self):
        with patch.dict(os.environ, {"MAPLE_IDLE_SAVE_DIR": r"C:\\release\\saves"}), patch(
            "player_save.os.makedirs"
        ) as make_dirs:
            path = get_default_save_path()

        self.assertEqual(path, r"C:\\release\\saves\savegame.json")
        make_dirs.assert_called_once_with(r"C:\\release\\saves", exist_ok=True)

    def test_file_round_trip_and_player_facade_keep_current_delegation(self):
        player = Player()
        player.gold = 12345
        path = os.path.join(SRC_DIR, ".player_save_characterization_test.json")
        for suffix in ("", ".bak", ".tmp"):
            candidate = Path(f"{path}{suffix}")
            if candidate.exists():
                candidate.unlink()
        try:
            self.assertTrue(save_player_to_file(player, path))

            restored = Player()
            self.assertIsNone(load_player_from_file(restored, path))
            self.assertEqual(restored.gold, 12345)
        finally:
            for suffix in ("", ".bak", ".tmp"):
                candidate = Path(f"{path}{suffix}")
                if candidate.exists():
                    candidate.unlink()

        with patch("player_data.player_save.player_to_dict", return_value={"delegated": True}) as to_dict:
            self.assertEqual(player.to_dict(), {"delegated": True})
            to_dict.assert_called_once_with(player)

    def test_persistence_module_has_no_import_edge_back_to_player_data(self):
        save_path = os.path.join(SRC_DIR, "player_save.py")
        tree = ast.parse(Path(save_path).read_text(encoding="utf-8"))
        imported_modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.append(node.module)

        self.assertNotIn("player_data", imported_modules)


if __name__ == "__main__":
    unittest.main()
