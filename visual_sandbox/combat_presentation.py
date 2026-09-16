"""Runtime-aware presentation boundary for the visual sandbox.

The drawing primitives remain in :mod:`vfx` and stay runtime-agnostic.  This
thin adapter is the only place that translates timed runtime states into the
Hero's persistent visuals.
"""

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPainter

try:
    from .combat_rules import BURNING_SOUL, FIGHTING_INSTINCT, HERO_ID
    from .combat_runtime import CombatRuntimeState
    from .vfx import draw_burning_soul_sword, draw_rage_aura
except ImportError:  # Direct ``py visual_sandbox/main.py`` execution.
    from combat_rules import BURNING_SOUL, FIGHTING_INSTINCT, HERO_ID
    from combat_runtime import CombatRuntimeState
    from vfx import draw_burning_soul_sword, draw_rage_aura


def draw_runtime_presentation(
    painter: QPainter,
    prototype_id: str,
    runtime: CombatRuntimeState,
    player_center: QPointF,
    area: QRectF,
    phase: float,
    layer: str = "all",
) -> None:
    """Draw persistent visuals for the active prototype's runtime state."""
    if prototype_id != HERO_ID:
        return
    if layer in ("all", "before_avatar") and runtime.is_active(FIGHTING_INSTINCT):
        draw_rage_aura(
            painter,
            player_center,
            area,
            phase,
            runtime.remaining(FIGHTING_INSTINCT),
        )
    if layer in ("all", "after_avatar") and runtime.is_active(BURNING_SOUL):
        draw_burning_soul_sword(
            painter,
            player_center,
            area,
            phase,
            runtime.remaining(BURNING_SOUL),
        )
