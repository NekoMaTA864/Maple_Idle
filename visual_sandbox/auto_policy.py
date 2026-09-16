"""Small, deterministic AUTO PRIORITY selectors for the visual sandbox.

The selector only answers which equipped skill should be attempted next.  It
does not mutate runtime state, cooldowns, sequence cursors, or presentation.
"""

from __future__ import annotations

try:
    from .combat_rules import BURNING_SOUL, FIGHTING_INSTINCT, effective_rage
    from .skills import priority_skill_ids
except ImportError:  # Direct ``py visual_sandbox/main.py`` execution.
    from combat_rules import BURNING_SOUL, FIGHTING_INSTINCT, effective_rage
    from skills import priority_skill_ids


HERO_ID = "hero"

HERO_RAGE_ATTACK = "hero_rage_attack"
HERO_SWORD_ILLUSION = "hero_sword_illusion"
HERO_BURNING_SOUL_SWORD = "hero_burning_soul_sword"
HERO_SPATIAL_SLASH = "hero_spatial_slash"
HERO_FIGHTING_INSTINCT = "hero_fighting_instinct"
HERO_SACRED_SWORD_DESCENT = "hero_sacred_sword_descent"


def _ready(skill_id: str, cooldowns_remaining: dict[str, float]) -> bool:
    return cooldowns_remaining.get(skill_id, 0.0) <= 0.0


def _equipped(equipped_skill_ids: tuple[str, ...] | list[str]) -> set[str]:
    return set(equipped_skill_ids)


def _hero_policy(
    equipped: set[str],
    runtime,
    cooldowns_remaining: dict[str, float],
) -> str | None:
    """Apply the policy for the Hero loadout identified by its skill IDs."""
    rage = effective_rage(runtime)
    burning_active = runtime.is_active(BURNING_SOUL)
    instinct_active = runtime.is_active(FIGHTING_INSTINCT)

    stable = {
        HERO_RAGE_ATTACK,
        HERO_SWORD_ILLUSION,
        HERO_SPATIAL_SLASH,
        HERO_BURNING_SOUL_SWORD,
    }
    if equipped == stable:
        if not burning_active and HERO_BURNING_SOUL_SWORD in equipped and _ready(HERO_BURNING_SOUL_SWORD, cooldowns_remaining):
            return HERO_BURNING_SOUL_SWORD
        if rage >= 3 and HERO_SPATIAL_SLASH in equipped and _ready(HERO_SPATIAL_SLASH, cooldowns_remaining):
            return HERO_SPATIAL_SLASH
        if HERO_SWORD_ILLUSION in equipped and _ready(HERO_SWORD_ILLUSION, cooldowns_remaining):
            return HERO_SWORD_ILLUSION
        if HERO_RAGE_ATTACK in equipped and _ready(HERO_RAGE_ATTACK, cooldowns_remaining):
            return HERO_RAGE_ATTACK
        return None

    sustain = {
        HERO_RAGE_ATTACK,
        HERO_SWORD_ILLUSION,
        HERO_BURNING_SOUL_SWORD,
        HERO_FIGHTING_INSTINCT,
    }
    if equipped == sustain:
        if not burning_active and HERO_BURNING_SOUL_SWORD in equipped and _ready(HERO_BURNING_SOUL_SWORD, cooldowns_remaining):
            return HERO_BURNING_SOUL_SWORD
        if (
            burning_active
            and not instinct_active
            and HERO_FIGHTING_INSTINCT in equipped
            and _ready(HERO_FIGHTING_INSTINCT, cooldowns_remaining)
        ):
            return HERO_FIGHTING_INSTINCT
        if HERO_SWORD_ILLUSION in equipped and _ready(HERO_SWORD_ILLUSION, cooldowns_remaining):
            return HERO_SWORD_ILLUSION
        if HERO_RAGE_ATTACK in equipped and _ready(HERO_RAGE_ATTACK, cooldowns_remaining):
            return HERO_RAGE_ATTACK
        return None

    burst = {
        HERO_RAGE_ATTACK,
        HERO_SPATIAL_SLASH,
        HERO_FIGHTING_INSTINCT,
        HERO_SACRED_SWORD_DESCENT,
    }
    if equipped == burst:
        if instinct_active and HERO_SACRED_SWORD_DESCENT in equipped and _ready(HERO_SACRED_SWORD_DESCENT, cooldowns_remaining):
            return HERO_SACRED_SWORD_DESCENT
        if (
            not instinct_active
            and HERO_SACRED_SWORD_DESCENT in equipped
            and HERO_FIGHTING_INSTINCT in equipped
            and _ready(HERO_SACRED_SWORD_DESCENT, cooldowns_remaining)
            and _ready(HERO_FIGHTING_INSTINCT, cooldowns_remaining)
        ):
            return HERO_FIGHTING_INSTINCT
        if instinct_active and HERO_SPATIAL_SLASH in equipped and _ready(HERO_SPATIAL_SLASH, cooldowns_remaining):
            return HERO_SPATIAL_SLASH
        if rage >= 5 and HERO_SPATIAL_SLASH in equipped and _ready(HERO_SPATIAL_SLASH, cooldowns_remaining):
            return HERO_SPATIAL_SLASH
        if HERO_RAGE_ATTACK in equipped and _ready(HERO_RAGE_ATTACK, cooldowns_remaining):
            return HERO_RAGE_ATTACK
        return None

    return None


def select_auto_priority_skill(
    prototype_id: str,
    build_name: str,
    equipped_skill_ids: tuple[str, ...] | list[str],
    runtime,
    cooldowns_remaining: dict[str, float],
) -> str | None:
    """Return the next ready equipped skill for AUTO PRIORITY.

    ``build_name`` is accepted as part of the policy boundary for future
    presets, but the current Hero policies deliberately identify builds by
    their stable loadout skill IDs rather than UI-local display text.
    """
    del build_name
    equipped = _equipped(equipped_skill_ids)
    if prototype_id == HERO_ID:
        return _hero_policy(equipped, runtime, cooldowns_remaining)

    for skill_id in priority_skill_ids.get(prototype_id, ()):
        if skill_id in equipped and _ready(skill_id, cooldowns_remaining):
            return skill_id
    return None
