"""Capture deterministic Hero build preview videos from the real sandbox."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path

if os.name == "nt":
    # The Windows Qt platform loads the installed CJK font database.  The
    # offscreen plugin on this host reports zero families and renders boxes.
    os.environ["QT_QPA_PLATFORM"] = "windows"
else:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    import cv2
    import numpy as np
except ImportError as exc:  # pragma: no cover - exercised on machines without the optional capture tool.
    raise RuntimeError(
        "Video capture requires OpenCV (cv2) and NumPy. "
        "Install the local capture dependencies, then rerun this script."
    ) from exc

from PySide6.QtCore import QPoint
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

try:
    from .combat_rules import BURNING_SOUL, FIGHTING_INSTINCT, RAGE_ORBS
    from .fonts import resolved_ui_family
    from .sandbox import CombatVisualSandbox, MODE_MANUAL
    from .skills import loadout_presets
except ImportError:  # Direct ``py -3 visual_sandbox/capture_showcase_video.py`` execution.
    from combat_rules import BURNING_SOUL, FIGHTING_INSTINCT, RAGE_ORBS
    from fonts import resolved_ui_family
    from sandbox import CombatVisualSandbox, MODE_MANUAL
    from skills import loadout_presets


CAPTURE_WIDTH = 540
CAPTURE_HEIGHT = 880
FPS = 20
DURATION_SECONDS = 8.0
FRAME_COUNT = int(round(FPS * DURATION_SECONDS))
FIXED_DT = 1.0 / FPS
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "showcase" / "assets" / "hero"


@dataclass(frozen=True)
class CastEvent:
    """One deterministic manual cast in a presentation timeline."""

    at: float
    slot_index: int


@dataclass(frozen=True)
class BuildTimeline:
    """The small scripted state used to make one looping preview."""

    preset_name: str
    initial_rage: int
    casts: tuple[CastEvent, ...]


_HERO_PRESETS = tuple(loadout_presets["hero"])
if len(_HERO_PRESETS) < 3:  # Keep a clear error if the sandbox data is incomplete.
    raise RuntimeError("Hero showcase capture expects three Hero loadout presets.")


TIMELINES = {
    "stable": BuildTimeline(
        preset_name=_HERO_PRESETS[0],
        initial_rage=2,
        casts=(
            CastEvent(0.00, 3),  # Burning Soul Sword
            CastEvent(0.45, 0),  # Rage Attack
            CastEvent(0.95, 2),  # Spatial Slash
            CastEvent(1.55, 1),  # Sword Illusion
            CastEvent(3.65, 0),
            CastEvent(5.05, 2),
            CastEvent(6.65, 1),
        ),
    ),
    "sustain": BuildTimeline(
        preset_name=_HERO_PRESETS[1],
        initial_rage=3,
        casts=(
            CastEvent(0.00, 2),  # Burning Soul Sword
            CastEvent(0.40, 3),  # Fighting Instinct
            CastEvent(0.85, 1),  # Enhanced Sword Illusion
            CastEvent(1.35, 0),
            CastEvent(4.45, 0),
            CastEvent(5.95, 1),
            CastEvent(7.55, 0),
        ),
    ),
    "burst": BuildTimeline(
        preset_name=_HERO_PRESETS[2],
        initial_rage=5,
        casts=(
            CastEvent(0.00, 2),  # Fighting Instinct
            CastEvent(0.45, 3),  # Instinct Sacred Sword Descent
            CastEvent(1.00, 1),  # Maximum Spatial Slash
            CastEvent(2.15, 0),
            CastEvent(5.10, 1),
            CastEvent(5.55, 0),
        ),
    ),
}


def _render_image(window: CombatVisualSandbox) -> QImage:
    """Render one frame through QWidget's existing paint path."""
    image = QImage(CAPTURE_WIDTH, CAPTURE_HEIGHT, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    window.render(painter, QPoint(0, 0))
    painter.end()
    return image


def _image_to_bgr(image: QImage) -> np.ndarray:
    """Convert a rendered QImage into the BGR frame OpenCV expects."""
    converted = image.convertToFormat(QImage.Format.Format_BGR888)
    width = converted.width()
    height = converted.height()
    stride = converted.bytesPerLine()
    raw = np.frombuffer(converted.bits().tobytes(), dtype=np.uint8)
    rows = raw.reshape((height, stride))
    return rows[:, : width * 3].reshape((height, width, 3)).copy()


def _advance_deterministic(window: CombatVisualSandbox, dt: float) -> None:
    """Advance only the same local presentation state as the sandbox timer."""
    window.idle_phase = (window.idle_phase + dt * (0.045 / 0.04)) % math.tau
    for effect in window.active_effects:
        effect.age += dt
    window.active_effects = [effect for effect in window.active_effects if effect.age < effect.duration]
    for skill_id, remaining in window.cooldowns_remaining.items():
        window.cooldowns_remaining[skill_id] = max(0.0, remaining - dt)
    window.runtime_state.tick(dt)
    window.auto_action_remaining = max(0.0, window.auto_action_remaining - dt)
    window.skill_flash = max(0.0, window.skill_flash - dt)


def _prepare_window(window: CombatVisualSandbox, timeline: BuildTimeline) -> None:
    """Reset one Hero build, then establish anchors using a real render."""
    window.avatar_index = 0
    window.current_loadout_preset["hero"] = timeline.preset_name
    window.control_mode = MODE_MANUAL
    window.resize(CAPTURE_WIDTH, CAPTURE_HEIGHT)
    window._reset_current_loadout_state()
    window.runtime_state.set(RAGE_ORBS, timeline.initial_rage)
    window.idle_phase = 0.0
    # This initial render refreshes the avatar anchors before the first cast.
    _render_image(window)


def _open_webm(path: Path):
    """Open the first locally available WebM writer or fail loudly."""
    path.unlink(missing_ok=True)
    for codec in ("VP80", "VP90"):
        writer = cv2.VideoWriter(
            str(path),
            cv2.VideoWriter_fourcc(*codec),
            float(FPS),
            (CAPTURE_WIDTH, CAPTURE_HEIGHT),
        )
        if writer.isOpened():
            return writer, codec
        writer.release()
    raise RuntimeError(
        "No usable WebM encoder is available in OpenCV/FFmpeg. "
        "Install an OpenCV build with WebM (VP8/VP9) support and rerun."
    )


def _validate_webm(path: Path) -> tuple[int, int, int]:
    """Verify the generated file is readable and has the requested geometry."""
    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError(f"WebM output was not created: {path}")
    capture = cv2.VideoCapture(str(path))
    try:
        if not capture.isOpened():
            raise RuntimeError(f"Generated WebM cannot be opened: {path}")
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        ok, _ = capture.read()
        if not ok or (width, height) != (CAPTURE_WIDTH, CAPTURE_HEIGHT) or frame_count < FRAME_COUNT:
            raise RuntimeError(
                f"Generated WebM failed validation: size={width}x{height}, "
                f"frames={frame_count}, first_frame={ok}"
            )
        return width, height, frame_count
    finally:
        capture.release()


def _capture_build(window: CombatVisualSandbox, build_id: str, timeline: BuildTimeline) -> Path:
    _prepare_window(window, timeline)
    output_path = OUTPUT_DIR / f"{build_id}.webm"
    writer, codec = _open_webm(output_path)
    try:
        next_cast = 0
        for frame_index in range(FRAME_COUNT):
            now = frame_index * FIXED_DT
            while next_cast < len(timeline.casts) and timeline.casts[next_cast].at <= now + 1e-9:
                event = timeline.casts[next_cast]
                if not window._trigger_skill(event.slot_index):
                    raise RuntimeError(f"Timeline cast failed for {build_id} at {event.at:.2f}s")
                next_cast += 1
            writer.write(_image_to_bgr(_render_image(window)))
            _advance_deterministic(window, FIXED_DT)
    finally:
        writer.release()
    width, height, frame_count = _validate_webm(output_path)
    print(f"captured {output_path} ({width}x{height}, {DURATION_SECONDS:.1f}s, {codec})")
    return output_path


def capture_showcase_videos() -> tuple[Path, ...]:
    """Generate stable, sustain, and burst WebM previews in a fixed order."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    print(f"Qt UI font: {resolved_ui_family()}")
    window = CombatVisualSandbox()
    window.idle_timer.stop()
    window.show()
    app.processEvents()
    try:
        return tuple(_capture_build(window, build_id, timeline) for build_id, timeline in TIMELINES.items())
    finally:
        window.close()
        app.processEvents()


if __name__ == "__main__":
    capture_showcase_videos()
