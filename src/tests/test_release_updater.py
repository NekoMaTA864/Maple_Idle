"""Characterization and safety coverage for the portable release updater.

All downloads are local stubs: unit tests never contact GitHub.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch
import zipfile


ROOT_DIR = Path(__file__).resolve().parents[2]
UPDATER_PATH = ROOT_DIR / "launcher" / "updater.py"
UPDATER_SPEC = importlib.util.spec_from_file_location("release_updater", UPDATER_PATH)
assert UPDATER_SPEC and UPDATER_SPEC.loader
updater = importlib.util.module_from_spec(UPDATER_SPEC)
sys.modules[UPDATER_SPEC.name] = updater
UPDATER_SPEC.loader.exec_module(updater)


class _Response:
    def __init__(self, payload: object):
        self.payload = json.dumps(payload).encode("utf-8") if not isinstance(payload, bytes) else payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class TestReleaseUpdater(unittest.TestCase):
    def setUp(self):
        self.work_dir = ROOT_DIR / "src" / ".release_updater_test"
        self._remove_work_dir()
        self.work_dir.mkdir()
        self.install = self.work_dir / "MapleIdle"
        self._create_installation()

    def tearDown(self):
        self._remove_work_dir()

    def _remove_work_dir(self):
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)

    def _create_installation(self, *, version="1.0.6", runtime_version="1.0.0"):
        (self.install / "game" / "src").mkdir(parents=True)
        (self.install / "runtime").mkdir()
        (self.install / "launcher").mkdir()
        (self.install / "game" / "src" / "pyside_main.py").write_text("old entrypoint", encoding="utf-8")
        (self.install / "runtime" / "VERSION").write_text(f"{runtime_version}\n", encoding="utf-8")
        (self.install / "launcher" / "updater.py").write_text("old updater", encoding="utf-8")
        (self.install / "VERSION").write_text(f"{version}\n", encoding="utf-8")
        (self.install / "start.bat").write_text("old start", encoding="utf-8")
        (self.install / "update.bat").write_text("old update", encoding="utf-8")
        for directory in ("saves", "settings", "logs", "screenshots"):
            target = self.install / directory
            target.mkdir()
            (target / "player-data.txt").write_text(f"keep {directory}", encoding="utf-8")

    def _write_update_zip(self, name="update.zip", *, version="1.0.7", extra=None, omit=None) -> Path:
        archive_path = self.work_dir / name
        members = {
            "VERSION": f"{version}\n",
            "start.bat": "new start",
            "update.bat": "new update",
            "game/src/pyside_main.py": "new entrypoint",
            "game/src/new_game_file.py": "new game file",
            "launcher/updater.py": "new updater",
        }
        for member in omit or set():
            members.pop(member)
        members.update(extra or {})
        with zipfile.ZipFile(archive_path, "w") as archive:
            for member, content in members.items():
                archive.writestr(member, content)
        return archive_path

    def _metadata(self, archive_path: Path, *, version="1.0.7", minimum_runtime="1.0.0", checksum=None):
        return updater.ReleaseMetadata(
            version=version,
            minimum_runtime=minimum_runtime,
            update_asset=archive_path.name,
            full_asset=f"MapleIdle_Full_{version}.zip",
            update_sha256=checksum or updater.sha256_file(archive_path),
            full_sha256="0" * 64,
        )

    @staticmethod
    def _download_from(source: Path):
        def download(_asset: str, destination: Path):
            shutil.copy2(source, destination)
        return download

    def _apply(self, metadata, archive_path):
        return updater.update_from_metadata(
            self.install,
            metadata,
            download=self._download_from(archive_path),
            work_dir=self.work_dir / "temporary-update-work",
        )

    def test_equal_remote_version_reports_up_to_date_without_download(self):
        archive = self._write_update_zip()
        metadata = self._metadata(archive, version="1.0.6")
        result = updater.update_from_metadata(
            self.install,
            metadata,
            download=lambda *_: self.fail("equal version must not download"),
            work_dir=self.work_dir / "unused",
        )
        self.assertEqual(result.status, "up-to-date")
        self.assertEqual((self.install / "game" / "src" / "pyside_main.py").read_text(encoding="utf-8"), "old entrypoint")

    def test_newer_remote_version_is_applied_and_preserves_user_data(self):
        archive = self._write_update_zip()
        result = self._apply(self._metadata(archive), archive)
        self.assertEqual(result.status, "updated")
        self.assertEqual((self.install / "VERSION").read_text(encoding="utf-8"), "1.0.7\n")
        self.assertEqual((self.install / "game" / "src" / "pyside_main.py").read_text(encoding="utf-8"), "new entrypoint")
        self.assertEqual((self.install / "launcher" / "updater.py").read_text(encoding="utf-8"), "new updater")
        self.assertTrue((self.install / ".backup" / "game_previous" / "src" / "pyside_main.py").is_file())
        for directory in ("saves", "settings", "logs", "screenshots"):
            self.assertEqual((self.install / directory / "player-data.txt").read_text(encoding="utf-8"), f"keep {directory}")

    def test_newer_local_version_does_not_downgrade(self):
        archive = self._write_update_zip(version="1.0.7")
        metadata = self._metadata(archive, version="1.0.5")
        result = updater.update_from_metadata(
            self.install,
            metadata,
            download=lambda *_: self.fail("downgrade must not download"),
            work_dir=self.work_dir / "unused",
        )
        self.assertEqual(result.status, "local-newer")

    def test_malformed_release_metadata_is_rejected(self):
        with self.assertRaisesRegex(updater.UpdateError, "missing"):
            updater.parse_release_metadata({"version": "1.0.7"})
        with self.assertRaisesRegex(updater.UpdateError, "Invalid semantic version"):
            updater.parse_release_metadata({
                "version": "newest",
                "minimum_runtime": "1.0.0",
                "update_asset": "update.zip",
                "full_asset": "full.zip",
                "update_sha256": "0" * 64,
                "full_sha256": "0" * 64,
            })

    def test_checksum_mismatch_leaves_installation_unchanged(self):
        archive = self._write_update_zip()
        metadata = self._metadata(archive, checksum="1" * 64)
        with self.assertRaisesRegex(updater.UpdateError, "checksum"):
            self._apply(metadata, archive)
        self.assertEqual((self.install / "VERSION").read_text(encoding="utf-8"), "1.0.6\n")
        self.assertFalse((self.install / ".backup").exists())

    def test_invalid_zip_is_rejected_before_replacement(self):
        archive = self.work_dir / "invalid.zip"
        archive.write_bytes(b"not a zip")
        metadata = self._metadata(archive)
        with self.assertRaisesRegex(updater.UpdateError, "not a valid ZIP"):
            self._apply(metadata, archive)
        self.assertEqual((self.install / "VERSION").read_text(encoding="utf-8"), "1.0.6\n")

    def test_path_traversal_zip_is_rejected_before_extraction(self):
        archive = self._write_update_zip(extra={"../outside.txt": "bad"})
        with self.assertRaisesRegex(updater.UpdateError, "Unsafe ZIP path"):
            updater.validate_update_zip(archive)

    def test_user_data_path_in_update_zip_is_rejected(self):
        archive = self._write_update_zip(extra={"saves/savegame.json": "bad"})
        with self.assertRaisesRegex(updater.UpdateError, "forbidden path|user data"):
            updater.validate_update_zip(archive)

    def test_unlisted_launcher_file_is_rejected(self):
        archive = self._write_update_zip(extra={"launcher/anything_else.py": "bad"})
        with self.assertRaisesRegex(updater.UpdateError, "forbidden path"):
            updater.validate_update_zip(archive)

    def test_staging_validation_rejects_missing_entrypoint(self):
        archive = self._write_update_zip(omit={"game/src/pyside_main.py"})
        with self.assertRaisesRegex(updater.UpdateError, "missing"):
            updater.validate_update_zip(archive)

    def test_replacement_failure_rolls_back_game_and_version(self):
        archive = self._write_update_zip()
        metadata = self._metadata(archive)
        original_install_file = updater._install_file

        def fail_when_writing_version(source, destination):
            if destination.name == "VERSION":
                raise OSError("simulated replacement failure")
            original_install_file(source, destination)

        with patch.object(updater, "_install_file", side_effect=fail_when_writing_version):
            with self.assertRaisesRegex(updater.UpdateError, "rolled back"):
                self._apply(metadata, archive)
        self.assertEqual((self.install / "VERSION").read_text(encoding="utf-8"), "1.0.6\n")
        self.assertEqual((self.install / "game" / "src" / "pyside_main.py").read_text(encoding="utf-8"), "old entrypoint")
        self.assertEqual((self.install / "start.bat").read_text(encoding="utf-8"), "old start")
        self.assertEqual((self.install / "launcher" / "updater.py").read_text(encoding="utf-8"), "old updater")

    def test_runtime_too_old_requires_full_package(self):
        archive = self._write_update_zip()
        metadata = self._metadata(archive, minimum_runtime="1.1.0")
        with self.assertRaisesRegex(updater.RuntimeTooOldError, "Full_"):
            self._apply(metadata, archive)
        self.assertEqual((self.install / "VERSION").read_text(encoding="utf-8"), "1.0.6\n")

    def test_latest_release_lookup_uses_mocked_public_assets(self):
        metadata_payload = {
            "version": "1.0.7",
            "minimum_runtime": "1.0.0",
            "update_asset": "MapleIdle_Update_1.0.7.zip",
            "full_asset": "MapleIdle_Full_1.0.7.zip",
            "update_sha256": "a" * 64,
            "full_sha256": "b" * 64,
        }
        requests = []

        def fake_open(url, timeout):
            requests.append(url)
            if url.endswith("/releases/latest"):
                return _Response({"assets": [
                    {"name": "version.json", "browser_download_url": "https://example.test/version.json"},
                    {"name": "MapleIdle_Update_1.0.7.zip", "browser_download_url": "https://example.test/update.zip"},
                ]})
            return _Response(metadata_payload)

        metadata, update_url = updater.fetch_latest_release("owner/repo", opener=fake_open)
        self.assertEqual(metadata.version, "1.0.7")
        self.assertEqual(update_url, "https://example.test/update.zip")
        self.assertEqual(len(requests), 2)
