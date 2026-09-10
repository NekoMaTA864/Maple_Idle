"""
新楓之谷 反抗軍陣營 (4 職業 / 32 招) 技能特效渲染統一分派模組 (vfx_resistance.py)
已模組化拆分為 blaster, wild_hunter, mechanic, battle_mage 四大子模組
"""

from vfx.resistance.blaster import render_blaster_vfx, BLASTER_EFFECTS
from vfx.resistance.wild_hunter import render_wild_hunter_vfx, WILD_HUNTER_EFFECTS
from vfx.resistance.mechanic import render_mechanic_vfx, MECHANIC_EFFECTS
from vfx.resistance.battle_mage import render_battle_mage_vfx, BATTLE_MAGE_EFFECTS


def render_resistance_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty,
                          rot_angle=0.0, seed=0.0, fracture_lines=None, **kwargs) -> bool:
    """渲染 反抗軍陣營 (4 職業 / 32 招) 特效，若命中回傳 True，否則 False"""
    if eff_name in BLASTER_EFFECTS:
        return render_blaster_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty, rot_angle, seed, fracture_lines, **kwargs)
    if eff_name in WILD_HUNTER_EFFECTS:
        return render_wild_hunter_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty, rot_angle, seed, fracture_lines, **kwargs)
    if eff_name in MECHANIC_EFFECTS:
        return render_mechanic_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty, rot_angle, seed, fracture_lines, **kwargs)
    if eff_name in BATTLE_MAGE_EFFECTS:
        return render_battle_mage_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty, rot_angle, seed, fracture_lines, **kwargs)
    return False
