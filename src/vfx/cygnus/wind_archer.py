"""
新楓之谷 皇家騎士團 - 破風使者 (Wind Archer) 技能特效模組
"""

import math
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath
)
from vfx_core import (
    _draw_starburst,
    _draw_bloom_line,
    _draw_expanding_shockwave,
    _draw_physics_particles,
)

WIND_ARCHER_EFFECTS = {
    "song_of_heaven", "howling_gale", "trifling_wind", "monsoon",
    "wind_blessing", "spiral_vortex_lance", "albatross_wings_aura", "vortex_sphere_core"
}


def render_wind_archer_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty,
                           rot_angle=0.0, seed=0.0, fracture_lines=None, **kwargs) -> bool:
    if eff_name == "albatross_wings_aura":
        # 天空信天翁：巨大青翠精靈神翼自背後展開
        for s in [-1, 1]:
            painter.setPen(QPen(QColor(120, 255, 210, alpha), 2))
            painter.setBrush(QBrush(QColor(80, 230, 180, int(alpha * 0.6))))
            w = QPainterPath()
            w.moveTo(cx, cy - 20)
            w.cubicTo(cx + s * 60, cy - 60, cx + s * 80, cy - 10, cx + s * 25, cy + 10)
            painter.drawPath(w)
        return True

    elif eff_name == "howling_gale":
        # 嘘叫狂風：巨大習緐龍捲風推進 + 風粒陰隨
        gale_x = cx + (tx - cx) * min(1.0, p * 1.2)
        for gi in range(5):
            r = 18 + gi * 10
            fade = 1.0 - gi * 0.15
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(80, 220, 140, int(alpha * fade)), 2.5))
            painter.drawEllipse(QPointF(gale_x, ty), r, int(r * 0.45))
        # 風粒帶隨龍捲前進
        _draw_physics_particles(painter, gale_x, ty, p, count=10,
                                color=(100, 230, 160), alpha=alpha, seed=44,
                                spread_x=45.0, spread_y=25.0, gravity=15.0, upward=False)
        return True

    elif eff_name == "monsoon":
        # 季風：漫天綠葉覆蓋全螢幕風暴
        for i in range(12):
            lx = cx + (tx - cx + 100) * ((p * 1.5 + i * 0.08) % 1.0) - 50
            ly = cy - 80 + (i * 20)
            painter.setBrush(QBrush(QColor(120, 240, 160, alpha)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(lx, ly), 7, 4)
        return True

    elif eff_name == "song_of_heaven":
        # 天空之歌：長弓激射碧綠光之箭雨
        for i in range(5):
            cur_p = min(1.0, p * 1.5 + i * 0.1)
            ax = cx + (tx - cx) * cur_p
            ay = cy + (ty - cy) * cur_p + (i - 2) * 7
            painter.setPen(QPen(QColor(60, 240, 150, alpha), 3))
            painter.drawLine(QPointF(ax - 20, ay), QPointF(ax, ay))
        return True

    elif eff_name == "spiral_vortex_lance":
        # 螺旋衝擊：螺旋穿透翠綠光柱 + 氣旋命中震波
        # 主光柱 bloom line
        _draw_bloom_line(painter, (cx, cy), (tx, ty),
                         base_width=7, color=(80, 220, 140), alpha=alpha, core_white=True)
        # 沿途螺旋氣流小橢圓
        for si in range(5):
            s_frac = (si + 1) / 6.0
            sx = cx + (tx - cx) * s_frac
            sy = cy + (ty - cy) * s_frac
            spiral_ang = rot_angle * 0.08 + si * 1.2
            so_x = sx + math.cos(spiral_ang) * 10
            so_y = sy + math.sin(spiral_ang) * 5
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(100, 240, 180, int(alpha * 0.6)), 2))
            painter.drawEllipse(QPointF(so_x, so_y), 8, 4)
        # 命中震波
        if p > 0.5:
            hit_p = (p - 0.5) / 0.5
            _draw_expanding_shockwave(painter, tx, ty, max_radius=65, p=hit_p,
                                     color=(80, 220, 140), alpha=alpha, aspect=0.55, rings=2)
        return True

    elif eff_name == "trifling_wind":
        # 妖精之箭：自動飛出的翠綠微風之羽
        for i in range(4):
            ang = rot_angle * 0.05 + i * (math.pi / 2)
            fx = tx + math.cos(ang) * (30 + 20 * p)
            fy = ty + math.sin(ang) * (20 + 15 * p)
            painter.setBrush(QBrush(QColor(80, 255, 160, alpha)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(fx, fy), 6, 3)
        return True

    elif eff_name == "vortex_sphere_core":
        # 風暴法球：風暴核心高速自轉並激射微型風刃
        painter.setBrush(QBrush(QColor(140, 245, 180, int(alpha * 0.8))))
        painter.drawEllipse(QPointF(tx, ty), 22, 22)
        for vi in range(4):
            vang = p * 15.0 + vi * (math.pi / 2)
            painter.setPen(QPen(QColor(255, 255, 255, alpha), 2))
            painter.drawLine(QPointF(tx, ty), QPointF(tx + math.cos(vang) * 35, ty + math.sin(vang) * 16))
        return True

    elif eff_name == "wind_blessing":
        # 旋風守護：氣旋護盾小橢圓群 + 風粒升騰
        for wi in range(3):
            w_ang = rot_angle * 0.06 + wi * (math.pi * 2 / 3)
            wx = cx + math.cos(w_ang) * (25 + 8 * math.sin(p * math.pi))
            wy = (cy - 10) + math.sin(w_ang) * (12 + 4 * math.sin(p * math.pi))
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(80, 220, 140, alpha), 2.5))
            painter.drawEllipse(QPointF(wx, wy), 10, 5)
        # 習緐線圈
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(120, 240, 180, int(alpha * 0.5)), 1.5))
        painter.drawEllipse(QPointF(cx, cy - 10), int(32 + 5 * math.sin(p * math.pi)), 14)
        # 風粒升騰
        _draw_physics_particles(painter, cx, cy, p, count=8,
                                color=(100, 230, 160), alpha=alpha, seed=21,
                                spread_x=22.0, spread_y=40.0, gravity=8.0, upward=True)
        return True

    return False

