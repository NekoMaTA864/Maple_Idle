"""Small presentation rules for prototype combat runtime state.

The sandbox still owns input, cooldowns, and skill playback.  This module only
describes the resource/timed-state consequences of a successful cast so those
rules can grow without filling the QWidget with Hero-specific branches.
"""

from __future__ import annotations

try:
    from .combat_runtime import CombatRuntimeState
except ImportError:  # Direct ``py visual_sandbox/main.py`` execution.
    from combat_runtime import CombatRuntimeState


HERO_ID = "hero"
RAGE_ORBS = "rage_orbs"
BURNING_SOUL = "burning_soul"
FIGHTING_INSTINCT = "fighting_instinct"

RAGE_GENERATORS = {
    "hero_rage_attack": 1,
    "hero_sword_illusion": 1,
}

TIMED_STATE_ACTIVATIONS = {
    "hero_burning_soul_sword": (BURNING_SOUL, 8.0),
    "hero_fighting_instinct": (FIGHTING_INSTINCT, 8.0),
}

HERO_SWORD_ILLUSION = "hero_sword_illusion"
HERO_SPATIAL_SLASH = "hero_spatial_slash"
HERO_SACRED_SWORD_DESCENT = "hero_sacred_sword_descent"


def create_runtime_state(prototype_id: str) -> CombatRuntimeState:
    """Create a fresh per-profession runtime with Hero's resource bounds."""
    runtime = CombatRuntimeState()
    if prototype_id == HERO_ID:
        runtime.configure_resource(RAGE_ORBS, 0, minimum=0, maximum=5)
    return runtime


def apply_skill_runtime_effects(
    prototype_id: str,
    skill_id: str,
    runtime: CombatRuntimeState,
) -> None:
    """Apply only the runtime consequences of a successfully cast skill."""
    if prototype_id != HERO_ID:
        return

    rage_delta = RAGE_GENERATORS.get(skill_id, 0)
    if rage_delta:
        runtime.add(RAGE_ORBS, rage_delta)

    timed_activation = TIMED_STATE_ACTIVATIONS.get(skill_id)
    if timed_activation is not None:
        state_key, duration = timed_activation
        runtime.activate(state_key, duration)


def effective_rage(runtime: CombatRuntimeState) -> int | float:
    """Return Hero's effective rage without mutating the stored orb count."""
    if runtime.is_active(FIGHTING_INSTINCT):
        return 5
    return runtime.get(RAGE_ORBS, 0)


def resolve_skill_variant(
    prototype_id: str,
    skill_id: str,
    runtime: CombatRuntimeState,
) -> str:
    """Resolve a presentation variant from the runtime before a cast mutates it."""
    if prototype_id != HERO_ID:
        return "normal"

    rage = effective_rage(runtime)
    if skill_id == HERO_SWORD_ILLUSION:
        return "enhanced" if rage >= 3 else "normal"
    if skill_id == HERO_SPATIAL_SLASH:
        if rage >= 5:
            return "maximum"
        if rage >= 3:
            return "empowered"
        return "normal"
    if skill_id == HERO_SACRED_SWORD_DESCENT:
        if runtime.is_active(FIGHTING_INSTINCT):
            return "instinct"
        return "max_rage" if rage == 5 else "normal"
    return "normal"
