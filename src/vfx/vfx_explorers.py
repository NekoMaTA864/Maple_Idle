"""
新楓之谷 冒險家陣營 (15 職業 / 120 招) 技能特效渲染統一分派模組 (vfx_explorers.py)
已模組化拆分為 warriors, mages, bowmen, thieves, pirates 五大子模組
"""

from vfx.explorers.warriors import render_warriors_vfx, WARRIORS_EFFECTS
from vfx.explorers.mages import render_mages_vfx, MAGES_EFFECTS
from vfx.explorers.bowmen import render_bowmen_vfx, BOWMEN_EFFECTS
from vfx.explorers.thieves import render_thieves_vfx, THIEVES_EFFECTS
from vfx.explorers.pirates import render_pirates_vfx, PIRATES_EFFECTS


def render_explorer_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty,
                        rot_angle=0.0, seed=0.0, fracture_lines=None, **kwargs) -> bool:
    """渲染 冒險家陣營 (15 職業 / 120 招) 特效，若命中回傳 True，否則 False"""
    if eff_name in WARRIORS_EFFECTS:
        return render_warriors_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty, rot_angle, seed, fracture_lines, **kwargs)
    if eff_name in MAGES_EFFECTS:
        return render_mages_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty, rot_angle, seed, fracture_lines, **kwargs)
    if eff_name in BOWMEN_EFFECTS:
        return render_bowmen_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty, rot_angle, seed, fracture_lines, **kwargs)
    if eff_name in THIEVES_EFFECTS:
        return render_thieves_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty, rot_angle, seed, fracture_lines, **kwargs)
    if eff_name in PIRATES_EFFECTS:
        return render_pirates_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty, rot_angle, seed, fracture_lines, **kwargs)
    return False
