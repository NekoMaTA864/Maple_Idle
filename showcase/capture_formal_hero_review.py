"""Capture Hero review previews from the formal main VFX Gallery.

This is a showcase-only capture helper.  It imports the formal Gallery and
its VisualEffectManager, then composes the three review builds without
touching CombatManager, gameplay state, or the production renderer.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import cv2
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase, QImage

from tools.vfx_gallery import VFXGalleryWindow


FPS = 20
DURATION_SECONDS = 4.0
FRAME_COUNT = int(round(FPS * DURATION_SECONDS))
OUTPUT_DIR = ROOT / "showcase" / "assets" / "hero"


TIMELINES = {
    "stable": (
        (0.00, "hero_burning_soul_sword"),
        (0.45, "hero_rage_attack"),
        (0.95, "hero_sword_illusion"),
        (1.45, "hero_spatial_slash"),
    ),
    "sustain": (
        (0.00, "hero_burning_soul_sword"),
        (0.35, "hero_fighting_instinct"),
        (0.85, "hero_sword_illusion"),
        (1.30, "hero_rage_attack"),
    ),
    "burst": (
        (0.00, "hero_fighting_instinct"),
        (0.45, "hero_spatial_slash"),
        (0.95, "hero_sacred_sword_descent"),
        (1.45, "hero_rage_attack"),
    ),
}

POSTER_TIMES = {
    "stable": 1.65,
    "sustain": 1.05,
    "burst": 1.25,
}


def _qimage_to_bgr(image):
    image = image.convertToFormat(QImage.Format.Format_RGBA8888)
    width = image.width()
    height = image.height()
    channels = image.bytesPerLine() // 4
    pixels = np.frombuffer(image.bits(), dtype=np.uint8, count=image.sizeInBytes())
    pixels = pixels.reshape((height, channels, 4))[:, :width, :]
    return cv2.cvtColor(pixels, cv2.COLOR_RGBA2BGR)


def _install_capture_font(app: QApplication) -> None:
    """Keep the formal arena's existing font names readable offscreen."""
    font_path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "NotoSansTC-VF.ttf"
    if not font_path.exists():
        return
    font_id = QFontDatabase.addApplicationFont(str(font_path))
    families = QFontDatabase.applicationFontFamilies(font_id) if font_id >= 0 else []
    if not families:
        return
    family = families[0]
    QFont.insertSubstitution("Microsoft YaHei UI", family)
    QFont.insertSubstitution("Microsoft YaHei", family)
    app.setFont(QFont(family))


def _open_writer(path: Path, width: int, height: int):
    for codec in ("VP80", "VP90"):
        writer = cv2.VideoWriter(
            str(path), cv2.VideoWriter_fourcc(*codec), FPS, (width, height)
        )
        if writer.isOpened():
            return writer, codec
        writer.release()
    raise RuntimeError(f"No WebM writer is available for {path}")


def _reset_capture(window: VFXGalleryWindow) -> None:
    window.state.clear_presentation()
    window.arena.set_debug_anchors(False)
    window.arena.set_combat_avatar("hero")
    window.arena.game_time = 0.0


def _capture_build(window: VFXGalleryWindow, app: QApplication, build_id: str) -> None:
    _reset_capture(window)

    # The formal Gallery normally resets presentation before each button
    # press.  Temporarily keeping that lifecycle call empty lets this
    # showcase compose several formal presets into one Build preview.
    window.state.clear_presentation = lambda: None
    events = TIMELINES[build_id]
    event_index = 0
    poster_image = None
    poster_frame = int(round(POSTER_TIMES[build_id] * FPS))

    first_image = window.arena.grab().toImage()
    width, height = first_image.width(), first_image.height()
    output_path = OUTPUT_DIR / f"{build_id}.webm"
    writer, codec = _open_writer(output_path, width, height)
    try:
        for frame_index in range(FRAME_COUNT):
            current_time = frame_index / FPS
            while event_index < len(events) and events[event_index][0] <= current_time:
                _, preset_name = events[event_index]
                window.play_preset(preset_name)
                event_index += 1

            window.state.update_presentation(1.0 / FPS)
            window.arena.update_vfx_timer(1.0 / FPS)
            window.arena.repaint()
            app.processEvents()

            image = window.arena.grab().toImage()
            if frame_index == poster_frame:
                poster_image = image.copy()
            writer.write(_qimage_to_bgr(image))
    finally:
        writer.release()
        window.state.clear_presentation = window.state.__class__.clear_presentation.__get__(
            window.state, window.state.__class__
        )
        window.state.clear_presentation()

    if poster_image is None:
        raise RuntimeError(f"Poster frame was not captured for {build_id}")
    poster_path = OUTPUT_DIR / f"{build_id}.png"
    if not poster_image.save(str(poster_path), "PNG"):
        raise RuntimeError(f"Could not save poster: {poster_path}")

    capture = cv2.VideoCapture(str(output_path))
    try:
        video_size = (
            int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if not capture.isOpened() or video_size != (width, height) or frame_count < FRAME_COUNT:
            raise RuntimeError(
                f"Invalid WebM capture: size={video_size}, frames={frame_count}"
            )
    finally:
        capture.release()

    print(
        f"captured {build_id}: {width}x{height}, {frame_count} frames, codec={codec}, "
        f"poster={poster_path.name}, video={output_path.name}"
    )


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    _install_capture_font(app)
    window = VFXGalleryWindow()
    window.resize(760, 760)
    window.show()
    app.processEvents()
    window.timer.stop()
    app.processEvents()

    for build_id in ("stable", "sustain", "burst"):
        _capture_build(window, app, build_id)

    window.close()
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
