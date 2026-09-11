"""Build reproducible Maple Idle Full and Update release archives.

The script packages only runtime-needed game files.  It never includes player
saves, logs, tests, source control files, or other development artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
import zipfile


ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT_DIR / "src"
DEFAULT_RUNTIME_DIR = ROOT_DIR / "runtime"
DEFAULT_DIST_DIR = ROOT_DIR / "dist"
ENTRYPOINT = "game/src/pyside_main.py"
REQUIRED_RUNTIME_PYTHON = "runtime/python/python.exe"
REQUIRED_RUNTIME_VERSION = "runtime/VERSION"
RUNTIME_VERSION = "1.0.0"
MINIMUM_RUNTIME_VERSION = "1.0.0"
UPDATER_ENTRYPOINT = "launcher/updater.py"

GAME_EXCLUDED_PARTS = {"__pycache__", ".git", "tests", "saves", "scratch", "tools"}
GAME_EXCLUDED_FILES = {"dps_calculator.py", "launcher.py", "vfx_sandbox.py"}
ARCHIVE_EXCLUDED_PARTS = {"__pycache__", ".git", "saves", "settings", "logs", "scratch", "tests"}
ARCHIVE_EXCLUDED_SUFFIXES = {".pyc", ".pyo"}

RELEASE_START_BAT = r"""@echo off
setlocal
cd /d "%~dp0"
set "PYTHONNOUSERSITE=1"
set "MAPLE_IDLE_SAVE_DIR=%~dp0saves"

for %%D in (saves settings logs) do if not exist "%~dp0%%D" mkdir "%~dp0%%D"
set "PY_EXE=%~dp0runtime\python\python.exe"
if not exist "%PY_EXE%" (
    echo Bundled Python runtime is missing: %PY_EXE%
    pause
    exit /b 1
)

"%PY_EXE%" "%~dp0game\src\pyside_main.py"
if errorlevel 1 (
    echo Maple Idle exited with an error.
    pause
)
"""

RELEASE_UPDATE_BAT = r"""@echo off
setlocal
cd /d "%~dp0"
set "PYTHONNOUSERSITE=1"
set "PY_EXE=%~dp0runtime\python\python.exe"
if not exist "%PY_EXE%" (
    echo Bundled Python runtime is missing: %PY_EXE%
    echo Download the latest MapleIdle Full package from GitHub Releases.
    pause
    exit /b 1
)
if not exist "%~dp0launcher\updater.py" (
    echo Maple Idle updater is missing.
    echo Download the latest MapleIdle Full package from GitHub Releases.
    pause
    exit /b 1
)

"%PY_EXE%" "%~dp0launcher\updater.py"
set "UPDATE_EXIT=%ERRORLEVEL%"
if not "%UPDATE_EXIT%"=="0" echo Update failed. Your previous game files were kept or restored.
pause
exit /b %UPDATE_EXIT%
"""


def read_version(root_dir: Path = ROOT_DIR) -> str:
    version = (root_dir / "VERSION").read_text(encoding="utf-8").strip()
    if not version:
        raise ValueError("VERSION must not be empty")
    return version


def zip_datetime() -> tuple[int, int, int, int, int, int]:
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH", "315532800"))
    moment = datetime.fromtimestamp(max(epoch, 315532800), tz=timezone.utc)
    return moment.year, moment.month, moment.day, moment.hour, moment.minute, moment.second


def is_excluded(relative_path: Path, excluded_parts: set[str]) -> bool:
    return (
        any(part in excluded_parts for part in relative_path.parts)
        or relative_path.suffix.lower() in ARCHIVE_EXCLUDED_SUFFIXES
    )


def collect_tree(source_dir: Path, archive_prefix: str, excluded_parts: set[str], excluded_files: set[str] | None = None) -> dict[str, Path]:
    files: dict[str, Path] = {}
    excluded_files = excluded_files or set()
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(source_dir)
        if is_excluded(relative, excluded_parts) or path.name in excluded_files:
            continue
        files[f"{archive_prefix}/{relative.as_posix()}"] = path
    return files


def collect_game_files(root_dir: Path = ROOT_DIR) -> dict[str, Path]:
    files = collect_tree(root_dir / "src", "game/src", GAME_EXCLUDED_PARTS, GAME_EXCLUDED_FILES)
    assets_dir = root_dir / "assets"
    if assets_dir.is_dir():
        files.update(collect_tree(assets_dir, "game/assets", GAME_EXCLUDED_PARTS))
    files["game/requirements-lock.txt"] = root_dir / "requirements-lock.txt"
    return files


def collect_launcher_files(root_dir: Path = ROOT_DIR) -> dict[str, Path]:
    launcher_dir = root_dir / "launcher"
    updater_path = launcher_dir / "updater.py"
    if not updater_path.is_file():
        raise FileNotFoundError(f"Release updater is missing: {updater_path}")
    return {UPDATER_ENTRYPOINT: updater_path}


def runtime_root(runtime_dir: Path) -> Path:
    runtime_dir = runtime_dir.resolve()
    if not (runtime_dir / "python" / "python.exe").is_file():
        raise FileNotFoundError(f"Portable runtime not found: {runtime_dir / 'python' / 'python.exe'}")
    return runtime_dir


def write_zip(archive_path: Path, files: dict[str, Path | bytes]) -> None:
    timestamp = zip_datetime()
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for archive_name in sorted(files):
            source = files[archive_name]
            payload = source if isinstance(source, bytes) else source.read_bytes()
            info = zipfile.ZipInfo(archive_name, date_time=timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def assert_archive_safe(names: set[str], *, full: bool) -> None:
    for name in names:
        parts = Path(name).parts
        if any(part in ARCHIVE_EXCLUDED_PARTS for part in parts):
            raise ValueError(f"Forbidden release file: {name}")
    if full:
        if REQUIRED_RUNTIME_PYTHON not in names:
            raise ValueError("Full package is missing bundled runtime python.exe")
        if REQUIRED_RUNTIME_VERSION not in names:
            raise ValueError("Full package is missing bundled runtime VERSION")
    elif any(name == "runtime" or name.startswith("runtime/") for name in names):
        raise ValueError("Update package must not contain runtime")


def smoke_validate(full_archive: Path, update_archive: Path) -> None:
    for archive_path, is_full in ((full_archive, True), (update_archive, False)):
        with zipfile.ZipFile(archive_path) as archive:
            bad_member = archive.testzip()
            if bad_member:
                raise ValueError(f"Corrupt ZIP member in {archive_path.name}: {bad_member}")
            names = set(archive.namelist())
            required = {"VERSION", "start.bat", "update.bat", ENTRYPOINT, UPDATER_ENTRYPOINT}
            missing = required - names
            if missing:
                raise ValueError(f"{archive_path.name} is missing: {', '.join(sorted(missing))}")
            assert_archive_safe(names, full=is_full)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_release_metadata(
    path: Path,
    *,
    version: str,
    full_archive: Path,
    update_archive: Path,
) -> Path:
    metadata = {
        "version": version,
        "minimum_runtime": MINIMUM_RUNTIME_VERSION,
        "update_asset": update_archive.name,
        "full_asset": full_archive.name,
        "update_sha256": sha256(update_archive),
        "full_sha256": sha256(full_archive),
    }
    path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def run_tests(root_dir: Path) -> None:
    command = [sys.executable, "-m", "unittest", "discover", "-s", "src/tests"]
    result = subprocess.run(command, cwd=root_dir, check=False)
    if result.returncode:
        raise RuntimeError("Tests failed; refusing to build release archives")


def build_release(root_dir: Path, runtime_dir: Path, dist_dir: Path, skip_tests: bool = False) -> tuple[Path, Path, Path, Path]:
    if not skip_tests:
        run_tests(root_dir)

    version = read_version(root_dir)
    runtime_dir = runtime_root(runtime_dir)
    game_files = collect_game_files(root_dir)
    launcher_files = collect_launcher_files(root_dir)
    if ENTRYPOINT not in game_files:
        raise FileNotFoundError(f"Release entrypoint is missing: {ENTRYPOINT}")

    common_files: dict[str, Path | bytes] = {
        "VERSION": root_dir / "VERSION",
        "start.bat": RELEASE_START_BAT.replace("\n", "\r\n").encode("utf-8"),
        "update.bat": RELEASE_UPDATE_BAT.replace("\n", "\r\n").encode("utf-8"),
    }
    update_files = {**game_files, **launcher_files, **common_files}
    full_files = {
        **update_files,
        **collect_tree(runtime_dir, "runtime", ARCHIVE_EXCLUDED_PARTS),
        REQUIRED_RUNTIME_VERSION: f"{RUNTIME_VERSION}\n".encode("utf-8"),
    }

    dist_dir.mkdir(parents=True, exist_ok=True)
    full_archive = dist_dir / f"MapleIdle_Full_{version}.zip"
    update_archive = dist_dir / f"MapleIdle_Update_{version}.zip"
    write_zip(full_archive, full_files)
    write_zip(update_archive, update_files)
    smoke_validate(full_archive, update_archive)

    sums_path = dist_dir / "SHA256SUMS.txt"
    sums_path.write_text(
        f"{sha256(full_archive)}  {full_archive.name}\n"
        f"{sha256(update_archive)}  {update_archive.name}\n",
        encoding="utf-8",
    )
    metadata_path = write_release_metadata(
        dist_dir / "version.json",
        version=version,
        full_archive=full_archive,
        update_archive=update_archive,
    )
    return full_archive, update_archive, sums_path, metadata_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME_DIR, help="Directory containing python/python.exe")
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST_DIR, help="Output directory for release archives")
    parser.add_argument("--skip-tests", action="store_true", help="Build without running the full test suite")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    full_archive, update_archive, sums_path, metadata_path = build_release(
        ROOT_DIR,
        args.runtime,
        args.dist,
        skip_tests=args.skip_tests,
    )
    print(f"Built: {full_archive}")
    print(f"Built: {update_archive}")
    print(f"Checksums: {sums_path}")
    print(f"Release metadata: {metadata_path}")
    print("Smoke validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
