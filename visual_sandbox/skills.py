"""Skill pool data and presentation playback for the visual sandbox."""

import math
from dataclasses import dataclass

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPainter

try:
    from .combat_rules import HERO_BURNING_SOUL_FOLLOWUP
except ImportError:  # Direct ``py visual_sandbox/main.py`` execution.
    from combat_rules import HERO_BURNING_SOUL_FOLLOWUP

try:
    from .vfx import (
        EffectState,
        clamp01,
        draw_cannon_muzzle_flash,
        draw_cannonball,
        draw_flying_shuriken,
        draw_burning_soul_cast,
        draw_burning_soul_followup,
        draw_fighting_instinct_burst,
        draw_hero_slash,
        draw_hero_phantom_slash,
        draw_holy_area_base,
        draw_holy_burst,
        draw_holy_cast_pulse,
        draw_impact,
        lerp_point,
        draw_sword_descent,
        draw_spatial_slash,
    )
except ImportError:  # Direct ``py visual_sandbox/main.py`` execution.
    from vfx import (
        EffectState,
        clamp01,
        draw_cannon_muzzle_flash,
        draw_cannonball,
        draw_flying_shuriken,
        draw_burning_soul_cast,
        draw_burning_soul_followup,
        draw_fighting_instinct_burst,
        draw_hero_slash,
        draw_hero_phantom_slash,
        draw_holy_area_base,
        draw_holy_burst,
        draw_holy_cast_pulse,
        draw_impact,
        lerp_point,
        draw_sword_descent,
        draw_spatial_slash,
    )


HERO_SLASH = "hero_slash"
HERO_PHANTOM_SLASH = "hero_phantom_slash"
HERO_BURNING_SOUL = "hero_burning_soul"
HERO_SPATIAL_SLASH = "hero_spatial_slash"
HERO_FIGHTING_INSTINCT = "hero_fighting_instinct"
HERO_SWORD_DESCENT = "hero_sword_descent"
NIGHT_LORD_SHURIKEN = "night_lord_shuriken"
CANNON_SHOT = "cannon_shot"
BISHOP_HOLY_AREA = "bishop_holy_area"
PRESENTATION_PLACEHOLDER = "presentation_placeholder"


@dataclass(frozen=True)
class SkillSpec:
    skill_id: str
    display_name: str
    effect_id: str
    duration: float
    cooldown: float


active_skill_pools = {
    "hero": (
        SkillSpec("hero_rage_attack", "狂暴攻擊", HERO_SLASH, 0.66, 3.0),
        SkillSpec("hero_sword_illusion", "劍之幻象", HERO_PHANTOM_SLASH, 0.72, 5.0),
        SkillSpec("hero_burning_soul_sword", "燃燒靈魂之劍", HERO_BURNING_SOUL, 0.58, 8.0),
        SkillSpec("hero_spatial_slash", "空間斬", HERO_SPATIAL_SLASH, 0.52, 4.0),
        SkillSpec("hero_fighting_instinct", "鬥氣本能", HERO_FIGHTING_INSTINCT, 0.52, 10.0),
        SkillSpec("hero_sacred_sword_descent", "聖劍降臨", HERO_SWORD_DESCENT, 0.58, 14.0),
    ),
    "night_lord": (
        SkillSpec("night_lord_quad_throw", "四飛閃", NIGHT_LORD_SHURIKEN, 0.72, 2.5),
        SkillSpec("night_lord_taunt_contract", "挑釁契約", PRESENTATION_PLACEHOLDER, 0.46, 6.0),
        SkillSpec("night_lord_wind_shuriken", "風魔手裏劍", PRESENTATION_PLACEHOLDER, 0.46, 4.0),
        SkillSpec("night_lord_dakrus_secret", "達克魯的秘傳", PRESENTATION_PLACEHOLDER, 0.46, 8.0),
        SkillSpec("night_lord_scatter_throw", "散式投擲", PRESENTATION_PLACEHOLDER, 0.46, 3.5),
        SkillSpec("night_lord_flash_explosive_talisman", "飛閃起爆符", PRESENTATION_PLACEHOLDER, 0.46, 12.0),
    ),
    "cannon": (
        SkillSpec("cannon_barrage", "加農砲連擊", CANNON_SHOT, 0.82, 3.0),
        SkillSpec("cannon_monkey_militia", "輔助猴子", PRESENTATION_PLACEHOLDER, 0.46, 6.0),
        SkillSpec("cannon_rolling_rainbow", "滾動彩虹加農砲", PRESENTATION_PLACEHOLDER, 0.46, 8.0),
        SkillSpec("cannon_super_cannonball", "超級巨型加農砲彈", PRESENTATION_PLACEHOLDER, 0.46, 12.0),
        SkillSpec("cannon_suppressive_fire", "壓制砲擊", PRESENTATION_PLACEHOLDER, 0.46, 5.0),
        SkillSpec("cannon_sixth_job_placeholder", "六轉代表技能", PRESENTATION_PLACEHOLDER, 0.46, 14.0),
    ),
    "bishop": (
        SkillSpec("bishop_angels_ray", "天使之箭", PRESENTATION_PLACEHOLDER, 0.46, 3.0),
        SkillSpec("bishop_group_heal", "群體治癒", PRESENTATION_PLACEHOLDER, 0.46, 6.0),
        SkillSpec("bishop_holy_prayer", "聖靈祈禱", PRESENTATION_PLACEHOLDER, 0.46, 10.0),
        SkillSpec("bishop_peace_maker", "和平使者", BISHOP_HOLY_AREA, 1.02, 8.0),
        SkillSpec("bishop_divine_punishment", "神之懲罰", PRESENTATION_PLACEHOLDER, 0.46, 5.0),
        SkillSpec("bishop_heavens_damnation", "天堂神罰", PRESENTATION_PLACEHOLDER, 0.46, 15.0),
    ),
}


# Sandbox AUTO uses this presentation priority only; it intentionally mirrors
# each pool's declared order and carries no combat-balancing semantics.
priority_skill_ids = {
    prototype_id: [spec.skill_id for spec in pool]
    for prototype_id, pool in active_skill_pools.items()
}


equipped_skill_ids = {
    "hero": ("hero_rage_attack", "hero_sword_illusion", "hero_spatial_slash", "hero_burning_soul_sword"),
    "night_lord": ("night_lord_quad_throw", "night_lord_wind_shuriken", "night_lord_scatter_throw", "night_lord_dakrus_secret"),
    "cannon": ("cannon_barrage", "cannon_monkey_militia", "cannon_rolling_rainbow", "cannon_super_cannonball"),
    "bishop": ("bishop_angels_ray", "bishop_group_heal", "bishop_peace_maker", "bishop_heavens_damnation"),
}


# Debug-only build presets.  Each entry is a four-skill loadout drawn from the
# corresponding six-skill active pool; the sandbox owns which preset is active.
loadout_presets = {
    "hero": {
        "穩定循環": (
            "hero_rage_attack",
            "hero_sword_illusion",
            "hero_spatial_slash",
            "hero_burning_soul_sword",
        ),
        "持續輸出": (
            "hero_rage_attack",
            "hero_sword_illusion",
            "hero_burning_soul_sword",
            "hero_fighting_instinct",
        ),
        "爆發": (
            "hero_rage_attack",
            "hero_spatial_slash",
            "hero_fighting_instinct",
            "hero_sacred_sword_descent",
        ),
    },
    "night_lord": {"Default": equipped_skill_ids["night_lord"]},
    "cannon": {"Default": equipped_skill_ids["cannon"]},
    "bishop": {"Default": equipped_skill_ids["bishop"]},
}


PROTOTYPE_IDS = ("hero", "night_lord", "cannon", "bishop")


def prototype_id_for_avatar(avatar_index: int) -> str:
    return PROTOTYPE_IDS[avatar_index]


def skill_pool_for_avatar(avatar_index: int) -> tuple[SkillSpec, ...]:
    return active_skill_pools[prototype_id_for_avatar(avatar_index)]


def equipped_specs_for_avatar(avatar_index: int) -> tuple[SkillSpec, ...]:
    """Backward-compatible resolver for each profession's initial preset."""
    prototype_id = prototype_id_for_avatar(avatar_index)
    preset_name = "Default" if "Default" in loadout_presets[prototype_id] else next(iter(loadout_presets[prototype_id]))
    return loadout_specs_for_avatar(avatar_index, preset_name)


def loadout_specs_for_avatar(avatar_index: int, preset_name: str) -> tuple[SkillSpec, ...]:
    """Resolve one named four-skill preset without changing the pool data."""
    prototype_id = prototype_id_for_avatar(avatar_index)
    by_id = {spec.skill_id: spec for spec in active_skill_pools[prototype_id]}
    skill_ids = loadout_presets[prototype_id][preset_name]
    return tuple(by_id[skill_id] for skill_id in skill_ids)


def skill_spec_for_id(skill_id: str) -> SkillSpec:
    for pool in active_skill_pools.values():
        for spec in pool:
            if spec.skill_id == skill_id:
                return spec
    raise KeyError(f"Unknown sandbox skill id: {skill_id}")


def create_effect(
    skill_id: str,
    anchors: dict[str, QPointF],
    fallback_origin: QPointF,
    target: QPointF,
    target_ground: QPointF,
    variant: str = "normal",
) -> EffectState:
    spec = skill_spec_for_id(skill_id)
    if spec.effect_id == CANNON_SHOT:
        origin = anchors.get("muzzle", fallback_origin)
    elif spec.effect_id == BISHOP_HOLY_AREA:
        origin = anchors.get("tip", fallback_origin)
    else:
        origin = anchors.get("attack_origin", fallback_origin)
    return EffectState(spec.effect_id, 0.0, spec.duration, QPointF(origin), QPointF(target), QPointF(target_ground), variant)


def create_presentation_effect(
    effect_id: str,
    player_center: QPointF,
    target: QPointF,
    target_ground: QPointF,
    area: QRectF,
) -> EffectState:
    """Create a stateless follow-up effect without skill/cooldown semantics."""
    if effect_id != HERO_BURNING_SOUL_FOLLOWUP:
        raise ValueError(f"Unknown presentation event: {effect_id}")
    origin = QPointF(
        player_center.x() + area.width() * 0.15,
        player_center.y() - area.height() * 0.018,
    )
    return EffectState(effect_id, 0.0, 0.50, origin, QPointF(target), QPointF(target_ground))


def draw_skill_effect(painter: QPainter, effect: EffectState, area: QRectF) -> None:
    renderers = {
        HERO_SLASH: _draw_hero_skill,
        HERO_PHANTOM_SLASH: _draw_hero_phantom_skill,
        HERO_BURNING_SOUL: _draw_hero_burning_soul_skill,
        HERO_BURNING_SOUL_FOLLOWUP: _draw_hero_burning_soul_followup_skill,
        HERO_SPATIAL_SLASH: _draw_hero_spatial_slash_skill,
        HERO_FIGHTING_INSTINCT: _draw_hero_fighting_instinct_skill,
        HERO_SWORD_DESCENT: _draw_hero_sword_descent_skill,
        NIGHT_LORD_SHURIKEN: _draw_night_lord_skill,
        CANNON_SHOT: _draw_cannon_skill,
        BISHOP_HOLY_AREA: _draw_bishop_skill,
    }
    renderer = renderers.get(effect.effect_id)
    if renderer is not None:
        renderer(painter, effect, area)


def _draw_hero_skill(painter: QPainter, effect: EffectState, area: QRectF) -> None:
    draw_hero_slash(painter, effect, area)
    impact_progress = (effect.age - 0.34) / 0.22
    if 0.0 <= impact_progress <= 1.0:
        draw_impact(painter, effect.target, impact_progress, "medium", (116, 207, 255))


def _draw_hero_phantom_skill(painter: QPainter, effect: EffectState, area: QRectF) -> None:
    draw_hero_phantom_slash(painter, effect, area)
    impact_progress = (effect.age - 0.38) / 0.20
    if 0.0 <= impact_progress <= 1.0:
        draw_impact(painter, effect.target, impact_progress, "medium", (130, 183, 255))


def _draw_hero_burning_soul_skill(painter: QPainter, effect: EffectState, area: QRectF) -> None:
    draw_burning_soul_cast(painter, effect, area)


def _draw_hero_burning_soul_followup_skill(painter: QPainter, effect: EffectState, area: QRectF) -> None:
    draw_burning_soul_followup(painter, effect, area)


def _draw_hero_spatial_slash_skill(painter: QPainter, effect: EffectState, area: QRectF) -> None:
    draw_spatial_slash(painter, effect, area)
    impact_levels = {"normal": "small", "empowered": "medium", "maximum": "large"}
    impact_progress = (effect.age - 0.31) / 0.19
    if 0.0 <= impact_progress <= 1.0:
        draw_impact(painter, effect.target, impact_progress, impact_levels.get(effect.variant, "small"), (105, 204, 255))


def _draw_hero_fighting_instinct_skill(painter: QPainter, effect: EffectState, area: QRectF) -> None:
    draw_fighting_instinct_burst(painter, effect, area)


def _draw_hero_sword_descent_skill(painter: QPainter, effect: EffectState, area: QRectF) -> None:
    draw_sword_descent(painter, effect, area)
    impact_levels = {"normal": "medium", "max_rage": "large", "instinct": "large"}
    impact_progress = (effect.age - 0.40) / 0.18
    if 0.0 <= impact_progress <= 1.0:
        draw_impact(painter, effect.target, impact_progress, impact_levels.get(effect.variant, "medium"), (167, 225, 255))


def _draw_night_lord_skill(painter: QPainter, effect: EffectState, area: QRectF) -> None:
    travel_x = effect.target.x() - effect.origin.x()
    travel_y = effect.target.y() - effect.origin.y()
    travel_length = max(1.0, math.hypot(travel_x, travel_y))
    direction = QPointF(travel_x / travel_length, travel_y / travel_length)
    flight_duration = 0.29
    for index, delay in enumerate((0.0, 0.065, 0.13)):
        local_age = effect.age - delay
        if 0.0 <= local_age <= flight_duration:
            progress = clamp01(local_age / flight_duration)
            eased = 1.0 - (1.0 - progress) ** 2
            position = lerp_point(effect.origin, effect.target, eased)
            draw_flying_shuriken(painter, position, max(6.0, area.width() * 0.016), effect.age * 720.0 + index * 80.0, direction, 1.0)
        impact_progress = (local_age - flight_duration) / 0.16
        if 0.0 <= impact_progress <= 1.0:
            draw_impact(painter, effect.target, impact_progress, "small", (170, 137, 255))


def _draw_cannon_skill(painter: QPainter, effect: EffectState, area: QRectF) -> None:
    draw_cannon_muzzle_flash(painter, effect.origin, area, effect.age)
    flight_progress = (effect.age - 0.10) / 0.43
    if 0.0 <= flight_progress <= 1.0:
        draw_cannonball(painter, effect.origin, effect.target, area, flight_progress)
    impact_progress = (effect.age - 0.53) / 0.25
    if 0.0 <= impact_progress <= 1.0:
        draw_impact(painter, effect.target, impact_progress, "large", (255, 158, 66))


def _draw_bishop_skill(painter: QPainter, effect: EffectState, area: QRectF) -> None:
    draw_holy_cast_pulse(painter, effect.origin, effect.target, area, effect.age)
    base_fade = 1.0 - clamp01((effect.age - 0.82) / 0.20)
    draw_holy_area_base(painter, effect.target_ground, area, base_fade)
    for pulse_start in (0.10, 0.39, 0.68):
        pulse_progress = (effect.age - pulse_start) / 0.27
        if 0.0 <= pulse_progress <= 1.0:
            draw_holy_burst(painter, effect.target_ground, pulse_progress, area)
