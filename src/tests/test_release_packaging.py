"""Focused checks for release metadata written by the packaging script."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import unittest


ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_release


class TestReleasePackaging(unittest.TestCase):
    def setUp(self):
        self.work_dir = ROOT_DIR / "src" / ".release_packaging_test"
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
        self.work_dir.mkdir()

    def tearDown(self):
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)

    def test_version_json_references_exact_archive_checksums_and_runtime_floor(self):
        full = self.work_dir / "MapleIdle_Full_1.0.6.zip"
        update = self.work_dir / "MapleIdle_Update_1.0.6.zip"
        full.write_bytes(b"full")
        update.write_bytes(b"update")
        metadata_path = build_release.write_release_metadata(
            self.work_dir / "version.json",
            version="1.0.6",
            full_archive=full,
            update_archive=update,
        )
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.assertEqual(metadata["version"], "1.0.6")
        self.assertEqual(metadata["minimum_runtime"], "1.0.0")
        self.assertEqual(metadata["full_asset"], full.name)
        self.assertEqual(metadata["update_asset"], update.name)
        self.assertEqual(metadata["full_sha256"], build_release.sha256(full))
        self.assertEqual(metadata["update_sha256"], build_release.sha256(update))
