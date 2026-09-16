"""Deterministically capture Hero build showcase frames from the real sandbox."""

from __future__ import annotations

import os
from pathlib import Path

if os.name == "nt":
    # The Windows Qt platform loads the installed CJK font database.  The
    # offscreen plugin on this host reports zero families and renders boxes.
    os.environ["QT_QPA_PLATFORM"] = "windows"
else:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

try:
    from .combat_rules import BURNING_SOUL, FIGHTING_INSTINCT, RAGE_ORBS
    from .fonts import resolved_ui_family
    from .sandbox import CombatVisualSandbox, MODE_MANUAL
    from .skills import HERO_PHANTOM_SLASH, HERO_SPATIAL_SLASH, HERO_SWORD_DESCENT
except ImportError:  # Direct ``py -3 visual_sandbox/capture_showcase.py`` execution.
    from combat_rules import BURNING_SOUL, FIGHTING_INSTINCT, RAGE_ORBS
    from fonts import resolved_ui_family
    from sandbox import CombatVisualSandbox, MODE_MANUAL
    from skills import HERO_PHANTOM_SLASH, HERO_SPATIAL_SLASH, HERO_SWORD_DESCENT


CAPTURE_WIDTH = 540
CAPTURE_HEIGHT = 880
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "showcase" / "assets" / "hero"


def _render(window: CombatVisualSandbox) -> QImage:
    image = QImage(CAPTURE_WIDTH, CAPTURE_HEIGHT, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    window.render(painter, QPoint(0, 0))
    painter.end()
    return image


def _prepare_hero(window: CombatVisualSandbox, preset_name: str) -> None:
    window.avatar_index = 0
    window.current_loadout_preset["hero"] = preset_name
    window.control_mode = MODE_MANUAL
    window._reset_current_loadout_state()
    window.idle_phase = 0.72
    window.resize(CAPTURE_WIDTH, CAPTURE_HEIGHT)
    # One deterministic base render refreshes current avatar anchors before
    # the real _trigger_skill() creates its presentation effect.
    _render(window)


def _capture_stable(window: CombatVisualSandbox) -> QImage:
    _prepare_hero(window, "穩定循環")
    runtime = window.runtime_state
    runtime.set(RAGE_ORBS, 5)
    runtime.activate(BURNING_SOUL, 8.0)
    assert window._trigger_skill(2), "stable showcase spatial slash did not cast"
    effect = next(effect for effect in window.active_effects if effect.effect_id == HERO_SPATIAL_SLASH)
    assert effect.variant == "maximum"
    effect.age = 0.32
    return _render(window)


def _capture_sustain(window: CombatVisualSandbox) -> QImage:
    _prepare_hero(window, "持續輸出")
    runtime = window.runtime_state
    runtime.set(RAGE_ORBS, 3)
    runtime.activate(BURNING_SOUL, 8.0)
    runtime.activate(FIGHTING_INSTINCT, 8.0)
    assert window._trigger_skill(1), "sustain showcase phantom slash did not cast"
    effect = next(effect for effect in window.active_effects if effect.effect_id == HERO_PHANTOM_SLASH)
    assert effect.variant == "enhanced"
    effect.age = 0.30
    return _render(window)


def _capture_burst(window: CombatVisualSandbox) -> QImage:
    _prepare_hero(window, "爆發")
    runtime = window.runtime_state
    runtime.set(RAGE_ORBS, 5)
    runtime.activate(FIGHTING_INSTINCT, 8.0)
    assert window._trigger_skill(3), "burst showcase sword descent did not cast"
    effect = next(effect for effect in window.active_effects if effect.effect_id == HERO_SWORD_DESCENT)
    assert effect.variant == "instinct"
    effect.age = 0.37
    return _render(window)


def capture_showcase() -> tuple[Path, ...]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    print(f"Qt UI font: {resolved_ui_family()}")
    window = CombatVisualSandbox()
    window.idle_timer.stop()
    window.show()
    app.processEvents()

    captures = (
        ("stable.png", _capture_stable(window)),
        ("sustain.png", _capture_sustain(window)),
        ("burst.png", _capture_burst(window)),
    )
    output_paths = []
    for filename, image in captures:
        output_path = OUTPUT_DIR / filename
        if not image.save(str(output_path), "PNG"):
            raise RuntimeError(f"Could not save capture: {output_path}")
        output_paths.append(output_path)

    window.close()
    app.processEvents()
    return tuple(output_paths)


if __name__ == "__main__":
    paths = capture_showcase()
    for path in paths:
        print(f"captured {path} ({CAPTURE_WIDTH}x{CAPTURE_HEIGHT})")
