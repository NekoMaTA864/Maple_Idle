"""
新楓之谷 皇家騎士團 - 烈焰巫師 (Flame Wizard) 技能特效模組
"""

import math
from PySide6.QtCore import Qt, QPointF, QRect
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPolygonF, QRadialGradient
)
from vfx_core import (
    _draw_magic_circle, _draw_bloom_line, _draw_ribbon_slash,
    _draw_expanding_shockwave, _draw_physics_particles, _draw_starburst
)

FLAME_WIZARD_EFFECTS = {
    "orbital_flame", "cataclysm", "blazing_extinction", "burning_conduit",
    "flame_barrier", "dragon_blaze_maw", "spirit_flame_aura", "inferno_wave_crests"
}


def render_flame_wizard_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty,
                            rot_angle=0.0, seed=0.0, fracture_lines=None, **kwargs) -> bool:
    if eff_name == "blazing_extinction":
        # 烈焰標記：翻滾太陽火球沿地面推進
        ball_x = cx + (tx - cx) * min(1.0, p * 1.3)
        painter.setBrush(QBrush(QColor(255, 120, 20, alpha)))
        painter.setPen(QPen(QColor(255, 255, 200, alpha), 2))
        painter.drawEllipse(QPointF(ball_x, ty + 10), 22, 22)
        return True

    elif eff_name == "burning_conduit":
        # 灼熱燃燒：地面升起熾熱熔岩五角法陣
        _draw_magic_circle(painter, tx, ty + 15, int(35 + 15 * math.sin(p * math.pi)), rot_angle * 0.03, QColor(255, 100, 30, alpha))
        return True

    elif eff_name == "cataclysm":
        # 焰火滅世：天降高溫垂直烈焰光柱群 + 地面衝擊 + 火星變屑
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        for i in range(3):
            bx = tx - 30 + i * 30
            _draw_bloom_line(painter, (bx, 0), (bx, ty + 20), base_width=15,
                             color=(255, 80 + i * 20, 20), alpha=alpha, core_white=True)
        if p > 0.3:
            imp_p = (p - 0.3) / 0.7
            _draw_ribbon_slash(painter, tx, ty + 5, start_deg=-160, sweep_deg=140,
                               inner_r=20, outer_r=75, color=(255, 80, 20), alpha=int(alpha * 0.85), core_white=True)
            _draw_expanding_shockwave(painter, tx, ty + 12, max_radius=110, p=imp_p,
                                     color=(255, 90, 20), alpha=alpha, aspect=0.35, rings=3)
            _draw_physics_particles(painter, tx, ty + 10, imp_p, count=20,
                                    color=(255, 140, 40), alpha=alpha, seed=42,
                                    spread_x=80.0, spread_y=50.0, gravity=75.0, upward=False)
            _draw_starburst(painter, tx, ty, int(22 + 28 * math.sin(imp_p * math.pi)),
                            QColor(255, 255, 220, alpha), QColor(255, 80, 20, alpha))
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        return True


    elif eff_name == "dragon_blaze_maw":
        # 焰龍狂怒：巨大烈焰龍首撞咬嘎火
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        _draw_ribbon_slash(painter, cx + 10, cy, start_deg=-30, sweep_deg=60,
                           inner_r=18, outer_r=80, color=(255, 80, 20), alpha=alpha, core_white=True)
        rg = QRadialGradient(cx + 10, cy, 80)
        rg.setColorAt(0.0, QColor(255, 255, 180, alpha))
        rg.setColorAt(0.4, QColor(255, 100, 20, int(alpha * 0.8)))
        rg.setColorAt(1.0, QColor(255, 40, 10, 0))
        painter.setBrush(QBrush(rg))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx + 40, cy), 55, 28)
        _draw_physics_particles(painter, tx, ty, p, count=20,
                                color=(255, 120, 30), alpha=alpha, seed=99,
                                spread_x=60.0, spread_y=35.0, gravity=35.0, upward=False)
        _draw_starburst(painter, tx, ty, int(16 + 20 * math.sin(p * math.pi)),
                        QColor(255, 255, 220, alpha), QColor(255, 80, 20, alpha))
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        return True


    elif eff_name == "flame_barrier":
        # 烈焰風暴：高溫旋轉火環包覆護盾 + 灼燒火花升騰
        rad = int(35 + 10 * math.sin(p * math.pi))
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 80, 20, alpha), 3))
        painter.drawEllipse(QPointF(cx, cy - 10), rad, rad)
        painter.setPen(QPen(QColor(255, 180, 60, int(alpha * 0.6)), 1.5))
        painter.drawEllipse(QPointF(cx, cy - 10), int(rad * 0.7), int(rad * 0.7))
        _draw_magic_circle(painter, cx, cy + 5, int(28 + 6 * math.sin(p * math.pi)),
                           rot_angle * 0.05, QColor(255, 100, 30, alpha))
        _draw_physics_particles(painter, cx, cy, p, count=8,
                                color=(255, 120, 30), alpha=alpha, seed=17,
                                spread_x=30.0, spread_y=50.0, gravity=10.0, upward=True)
        return True


    elif eff_name == "inferno_wave_crests":
        # 地獄火浪：三重大地燒岩火浪推進 + 衝擊波
        for wi in range(3):
            wx = cx + (tx - cx) * min(1.0, p * 1.3 + wi * 0.15)
            wave_r = int((22 + wi * 12) * math.sin(p * math.pi))
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(255, 90 + wi * 40, 20, alpha), 3.5))
            if wave_r > 0:
                painter.drawArc(QRect(int(wx - wave_r), int(ty - wave_r), wave_r * 2, wave_r * 2),
                                0 * 16, 180 * 16)
        _draw_expanding_shockwave(painter, tx, ty + 10, max_radius=85, p=p,
                                 color=(255, 80, 20), alpha=alpha, aspect=0.25, rings=2)
        _draw_physics_particles(painter, tx, ty + 5, p, count=14,
                                color=(255, 140, 40), alpha=alpha, seed=33,
                                spread_x=70.0, spread_y=35.0, gravity=55.0, upward=False)
        return True


    elif eff_name == "orbital_flame":
        # 軌道火球：拋出後沿橢圓軌道折返
        orb_x = cx + (tx - cx) * math.sin(p * math.pi)
        orb_y = cy - math.sin(p * math.pi * 2) * 35
        painter.setBrush(QBrush(QColor(255, 90, 20, alpha)))
        painter.setPen(QPen(QColor(255, 240, 150, alpha), 2))
        painter.drawEllipse(QPointF(orb_x, orb_y), 16, 16)
        return True

    elif eff_name == "spirit_flame_aura":
        # 火焰精靈之躍：三隻跳動的火焰小狐仙環繞
        for fi in range(3):
            fang = rot_angle * 0.05 + fi * (math.pi * 2 / 3)
            fx = cx + math.cos(fang) * 32
            fy = (cy - 10) + math.sin(fang) * 14
            painter.setBrush(QBrush(QColor(255, 160, 40, alpha)))
            painter.drawEllipse(QPointF(fx, fy), 6, 6)
        return True

    return False

