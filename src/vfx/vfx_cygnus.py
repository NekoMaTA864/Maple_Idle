"""
新楓之谷 皇家騎士團陣營 (5 職業 / 40 招) 技能特效渲染統一分派模組 (vfx_cygnus.py)
已模組化拆分為 dawn_warrior, flame_wizard, wind_archer, night_walker, thunder_breaker 五大子模組
"""

from vfx.cygnus.dawn_warrior import render_dawn_warrior_vfx, DAWN_WARRIOR_EFFECTS
from vfx.cygnus.flame_wizard import render_flame_wizard_vfx, FLAME_WIZARD_EFFECTS
from vfx.cygnus.wind_archer import render_wind_archer_vfx, WIND_ARCHER_EFFECTS
from vfx.cygnus.night_walker import render_night_walker_vfx, NIGHT_WALKER_EFFECTS
from vfx.cygnus.thunder_breaker import render_thunder_breaker_vfx, THUNDER_BREAKER_EFFECTS


def render_cygnus_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty,
                      rot_angle=0.0, seed=0.0, fracture_lines=None, **kwargs) -> bool:
    """渲染 皇家騎士團陣營 (5 職業 / 40 招) 特效，若命中回傳 True，否則 False"""
    if eff_name in DAWN_WARRIOR_EFFECTS:
        return render_dawn_warrior_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty, rot_angle, seed, fracture_lines, **kwargs)
    if eff_name in FLAME_WIZARD_EFFECTS:
        return render_flame_wizard_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty, rot_angle, seed, fracture_lines, **kwargs)
    if eff_name in WIND_ARCHER_EFFECTS:
        return render_wind_archer_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty, rot_angle, seed, fracture_lines, **kwargs)
    if eff_name in NIGHT_WALKER_EFFECTS:
        return render_night_walker_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty, rot_angle, seed, fracture_lines, **kwargs)
    if eff_name in THUNDER_BREAKER_EFFECTS:
        return render_thunder_breaker_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty, rot_angle, seed, fracture_lines, **kwargs)
    return False
