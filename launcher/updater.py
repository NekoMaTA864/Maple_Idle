"""Safe, foreground updater for a portable Maple Idle installation.

The updater deliberately accepts only the files that a MapleIdle Update archive
is allowed to replace.  Player-created files never participate in extraction,
backup, replacement, or rollback.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
import zipfile


GITHUB_REPOSITORY = "NekoMaTA864/Maple_Idle"
USER_DATA_DIRECTORIES = {"saves", "settings", "logs", "screenshots"}
UPDATABLE_FILES = {"VERSION", "start.bat", "update.bat"}
UPDATABLE_DIRECTORIES = {"game"}
UPDATABLE_LAUNCHER_FILES = {"launcher/updater.py"}
REQUIRED_UPDATE_MEMBERS = {
    "VERSION",
    "start.bat",
    "update.bat",
    "game/src/pyside_main.py",
    "launcher/updater.py",
}
SEMVER_RE = re.compile(r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class UpdateError(RuntimeError):
    """A recoverable update failure with a player-readable message."""


class RuntimeTooOldError(UpdateError):
    """The installed portable runtime cannot safely run the new game build."""


@dataclass(frozen=True)
class ReleaseMetadata:
    version: str
    minimum_runtime: str
    update_asset: str
    full_asset: str
    update_sha256: str
    full_sha256: str


@dataclass(frozen=True)
class UpdateResult:
    status: str
    message: str


def parse_semver(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str):
        raise UpdateError("Version must be a semantic-version string.")
    match = SEMVER_RE.fullmatch(value.strip())
    if not match:
        raise UpdateError(f"Invalid semantic version: {value!r}")
    return tuple(int(part) for part in match.groups())


def parse_release_metadata(payload: object) -> ReleaseMetadata:
    if not isinstance(payload, dict):
        raise UpdateError("Release metadata must be a JSON object.")
    required = {
        "version",
        "minimum_runtime",
        "update_asset",
        "full_asset",
        "update_sha256",
        "full_sha256",
    }
    missing = required - payload.keys()
    if missing:
        raise UpdateError(f"Release metadata is missing: {', '.join(sorted(missing))}")
    metadata = ReleaseMetadata(**{key: payload[key] for key in required})
    parse_semver(metadata.version)
    parse_semver(metadata.minimum_runtime)
    for field_name in ("update_asset", "full_asset"):
        asset = getattr(metadata, field_name)
        if not isinstance(asset, str) or Path(asset).name != asset or not asset.endswith(".zip"):
            raise UpdateError(f"Release metadata has an invalid {field_name}.")
    for field_name in ("update_sha256", "full_sha256"):
        checksum = getattr(metadata, field_name)
        if not isinstance(checksum, str) or not SHA256_RE.fullmatch(checksum.lower()):
            raise UpdateError(f"Release metadata has an invalid {field_name}.")
    return metadata


def installation_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_version(path: Path) -> str:
    try:
        version = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise UpdateError(f"Cannot read {path.name}: {exc}") from exc
    parse_semver(version)
    return version


def read_runtime_version(root_dir: Path) -> str:
    runtime_version = root_dir / "runtime" / "VERSION"
    if not runtime_version.is_file():
        raise RuntimeTooOldError(
            "This installation has no portable runtime compatibility marker. "
            "Download the latest Full package instead of applying an Update package."
        )
    return read_version(runtime_version)


def latest_release_asset_url(repository: str, asset_name: str) -> str:
    """Return GitHub's public redirect URL without using the REST API."""
    return f"https://github.com/{repository}/releases/latest/download/{asset_name}"


def _github_download_error(action: str, exc: Exception) -> UpdateError:
    if isinstance(exc, HTTPError):
        if exc.code == 404:
            return UpdateError(
                f"{action} was not found (HTTP 404). The latest GitHub Release may not include the required asset."
            )
        if exc.code == 403:
            return UpdateError(
                f"{action} was denied by GitHub (HTTP 403). Retry later or check that the release is public."
            )
        if exc.code == 429:
            return UpdateError(f"{action} is temporarily rate limited by GitHub (HTTP 429). Retry later.")
        return UpdateError(f"{action} failed with GitHub HTTP {exc.code}.")
    if isinstance(exc, URLError):
        return UpdateError(f"Network failure while requesting {action}: {exc.reason}")
    return UpdateError(f"Network failure while requesting {action}: {exc}")


def _read_json(url: str, opener: Callable = urlopen) -> object:
    try:
        with opener(url, timeout=20) as response:
            raw = response.read()
    except Exception as exc:
        raise _github_download_error("GitHub release metadata", exc) from exc
    try:
        return json.loads(raw.decode("utf-8"))
    except (AttributeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UpdateError("GitHub Release metadata is not valid JSON.") from exc


def fetch_latest_release(repository: str = GITHUB_REPOSITORY, opener: Callable = urlopen) -> tuple[ReleaseMetadata, str]:
    """Read public latest-release metadata without consuming GitHub REST quota."""
    metadata = parse_release_metadata(_read_json(latest_release_asset_url(repository, "version.json"), opener))
    update_url = latest_release_asset_url(repository, metadata.update_asset)
    return metadata, update_url


def fetch_latest_release_metadata(repository: str = GITHUB_REPOSITORY, opener: Callable = urlopen) -> ReleaseMetadata:
    """Return metadata only; retained as the small, directly testable lookup API."""
    metadata, _update_url = fetch_latest_release(repository, opener)
    return metadata


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_asset(url: str, destination: Path, opener: Callable = urlopen) -> None:
    try:
        with opener(url, timeout=60) as response, destination.open("wb") as output:
            shutil.copyfileobj(response, output)
    except Exception as exc:
        raise _github_download_error("GitHub update package download", exc) from exc


def _normal_member_name(name: str) -> str:
    normal = name.replace("\\", "/")
    pure = PurePosixPath(normal)
    if not normal or normal.startswith("/") or re.match(r"^[A-Za-z]:", normal):
        raise UpdateError(f"Unsafe ZIP path: {name!r}")
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise UpdateError(f"Unsafe ZIP path: {name!r}")
    return pure.as_posix()


def _is_allowed_member(name: str) -> bool:
    if name in UPDATABLE_FILES:
        return True
    if name in UPDATABLE_LAUNCHER_FILES:
        return True
    parts = PurePosixPath(name).parts
    return len(parts) > 1 and parts[0] in UPDATABLE_DIRECTORIES


def validate_update_zip(archive_path: Path) -> list[str]:
    try:
        with zipfile.ZipFile(archive_path) as archive:
            names: list[str] = []
            seen: set[str] = set()
            for info in archive.infolist():
                if info.is_dir():
                    continue
                name = _normal_member_name(info.filename)
                if name in seen:
                    raise UpdateError(f"Update ZIP contains duplicate path: {name}")
                seen.add(name)
                if not _is_allowed_member(name):
                    raise UpdateError(f"Update ZIP contains forbidden path: {name}")
                if PurePosixPath(name).parts[0] in USER_DATA_DIRECTORIES:
                    raise UpdateError(f"Update ZIP attempts to include user data: {name}")
                mode = info.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise UpdateError(f"Update ZIP contains a symbolic link: {name}")
                names.append(name)
    except zipfile.BadZipFile as exc:
        raise UpdateError("Downloaded update is not a valid ZIP archive.") from exc
    missing = REQUIRED_UPDATE_MEMBERS - set(names)
    if missing:
        raise UpdateError(f"Update ZIP is missing: {', '.join(sorted(missing))}")
    return names


def extract_update_to_staging(archive_path: Path, staging_dir: Path) -> None:
    names = validate_update_zip(archive_path)
    staging_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        for name in names:
            destination = staging_dir.joinpath(*PurePosixPath(name).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(name) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)
    validate_staging(staging_dir)


def validate_staging(staging_dir: Path) -> None:
    for member in REQUIRED_UPDATE_MEMBERS:
        if not staging_dir.joinpath(*PurePosixPath(member).parts).is_file():
            raise UpdateError(f"Staging validation failed: {member} is missing.")
    allowed_roots = UPDATABLE_DIRECTORIES | UPDATABLE_FILES | {"launcher"}
    unexpected = [path for path in staging_dir.iterdir() if path.name not in allowed_roots]
    if unexpected:
        raise UpdateError(f"Staging validation found an unexpected path: {unexpected[0].name}")


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def _copy_path(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _install_file(source: Path, destination: Path) -> None:
    shutil.copy2(source, destination)


def _snapshot_metadata(root_dir: Path, metadata_backup: Path) -> dict[str, bool]:
    existed: dict[str, bool] = {}
    for relative in sorted(UPDATABLE_FILES | {"launcher"}):
        source = root_dir / relative
        existed[relative] = source.exists()
        if source.exists():
            _copy_path(source, metadata_backup / relative)
    return existed


def _restore_backup(root_dir: Path, backup_dir: Path, existed: dict[str, bool]) -> None:
    game_dir = root_dir / "game"
    backup_game = backup_dir / "game_previous"
    if game_dir.exists():
        _remove_path(game_dir)
    if backup_game.exists():
        shutil.move(str(backup_game), str(game_dir))

    metadata_backup = backup_dir / "metadata_previous"
    for relative, was_present in existed.items():
        destination = root_dir / relative
        if destination.exists():
            _remove_path(destination)
        if was_present:
            _copy_path(metadata_backup / relative, destination)


def apply_staged_update(root_dir: Path, staging_dir: Path, remote_version: str) -> None:
    validate_staging(staging_dir)
    game_dir = root_dir / "game"
    if not game_dir.is_dir():
        raise UpdateError("Current installation has no game directory; download the Full package instead.")

    backup_dir = root_dir / ".backup"
    if backup_dir.exists():
        _remove_path(backup_dir)
    backup_dir.mkdir()
    metadata_backup = backup_dir / "metadata_previous"
    existed: dict[str, bool] = {}
    game_backed_up = False
    try:
        existed = _snapshot_metadata(root_dir, metadata_backup)
        shutil.move(str(game_dir), str(backup_dir / "game_previous"))
        game_backed_up = True
        shutil.move(str(staging_dir / "game"), str(game_dir))
        for relative in sorted(UPDATABLE_FILES):
            _install_file(staging_dir / relative, root_dir / relative)
        launcher_dir = root_dir / "launcher"
        if launcher_dir.exists():
            _remove_path(launcher_dir)
        _copy_path(staging_dir / "launcher", launcher_dir)
        if read_version(root_dir / "VERSION") != remote_version:
            raise UpdateError("Updated VERSION does not match GitHub Release metadata.")
        if not (game_dir / "src" / "pyside_main.py").is_file():
            raise UpdateError("Updated game entrypoint is missing after replacement.")
    except Exception as exc:
        if game_backed_up:
            _restore_backup(root_dir, backup_dir, existed)
        if isinstance(exc, UpdateError):
            raise
        raise UpdateError(f"Update replacement failed and was rolled back: {exc}") from exc


def update_from_metadata(
    root_dir: Path,
    metadata: ReleaseMetadata,
    *,
    download: Callable[[str, Path], None],
    work_dir: Path | None = None,
) -> UpdateResult:
    metadata = parse_release_metadata(metadata.__dict__)
    local_version = read_version(root_dir / "VERSION")
    if parse_semver(metadata.version) == parse_semver(local_version):
        return UpdateResult("up-to-date", "Maple Idle is already up to date.")
    if parse_semver(metadata.version) < parse_semver(local_version):
        return UpdateResult("local-newer", "Installed Maple Idle is newer than the latest GitHub Release; no downgrade was applied.")
    runtime_version = read_runtime_version(root_dir)
    if parse_semver(runtime_version) < parse_semver(metadata.minimum_runtime):
        raise RuntimeTooOldError(
            "The installed portable runtime is too old for this update. "
            f"Download {metadata.full_asset} from GitHub Releases instead."
        )

    def run(workspace: Path) -> None:
        archive_path = workspace / metadata.update_asset
        staging_dir = workspace / "staging"
        download(metadata.update_asset, archive_path)
        actual_checksum = sha256_file(archive_path)
        if actual_checksum.lower() != metadata.update_sha256.lower():
            raise UpdateError("Update checksum verification failed; no files were changed.")
        extract_update_to_staging(archive_path, staging_dir)
        apply_staged_update(root_dir, staging_dir, metadata.version)

    if work_dir is None:
        with tempfile.TemporaryDirectory(prefix="mapleidle-update-") as temporary:
            run(Path(temporary))
    else:
        if work_dir.exists():
            _remove_path(work_dir)
        work_dir.mkdir(parents=True)
        try:
            run(work_dir)
        finally:
            if work_dir.exists():
                _remove_path(work_dir)
    return UpdateResult("updated", f"Maple Idle was updated from {local_version} to {metadata.version}.")


def update_from_github(
    root_dir: Path,
    repository: str = GITHUB_REPOSITORY,
    *,
    opener: Callable = urlopen,
    work_dir: Path | None = None,
) -> UpdateResult:
    metadata, asset_url = fetch_latest_release(repository, opener)
    return update_from_metadata(
        root_dir,
        metadata,
        download=lambda _asset, path: download_asset(asset_url, path, opener),
        work_dir=work_dir,
    )


def main() -> int:
    try:
        result = update_from_github(installation_root())
        print(result.message)
        return 0
    except UpdateError as exc:
        print(f"Update could not be completed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
