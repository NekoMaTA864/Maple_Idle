"""
新楓之谷 皇家騎士團 - 暗夜行者 (Night Walker) 技能特效模組
"""

import math
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath
)
from vfx_core import (
    _draw_shuriken, _draw_magic_circle, _draw_starburst,
    _draw_expanding_shockwave, _draw_physics_particles
)

NIGHT_WALKER_EFFECTS = {
    "shadow_illusion", "shadow_spear", "shadow_spark", "darkness_ascending",
    "shadow_bat", "quintuple_dark_stars", "shadow_servant_aura", "dark_omen_summon"
}


def render_night_walker_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty,
                            rot_angle=0.0, seed=0.0, fracture_lines=None, **kwargs) -> bool:
    if eff_name == "dark_omen_summon":
        # 黑暗預兆：地下巨型暗夜法陣噴湧無數暗夜蝙蝠
        _draw_magic_circle(painter, tx, ty + 12, 38, rot_angle * 0.04, QColor(120, 50, 200, alpha))
        _draw_starburst(painter, tx, ty - 10, 24, QColor(220, 160, 255, alpha), QColor(100, 40, 180, alpha))
        return True

    elif eff_name == "darkness_ascending":
        # 黑暗吞噬：暗紫雙翅展開 + 暗吵法陣底部
        w_span = int(50 + 40 * math.sin(p * math.pi))
        for side in [-1, 1]:
            path = QPainterPath()
            path.moveTo(cx, cy - 10)
            path.cubicTo(cx + side * (w_span * 0.5), cy - 60,
                         cx + side * w_span, cy - 30,
                         cx + side * (w_span * 0.8), cy + 15)
            path.lineTo(cx, cy)
            painter.setBrush(QBrush(QColor(40, 10, 60, int(alpha * 0.75))))
            painter.setPen(QPen(QColor(160, 80, 255, alpha), 2))
            painter.drawPath(path)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(220, 140, 255, alpha), 3))
        painter.drawEllipse(QPointF(cx, cy - 10), 38, 38)
        _draw_magic_circle(painter, cx, cy + 10, int(26 + 8 * math.sin(p * math.pi)),
                           rot_angle * 0.04, QColor(140, 50, 220, int(alpha * 0.65)))
        _draw_physics_particles(painter, cx, cy, p, count=10,
                                color=(120, 40, 200), alpha=alpha, seed=33,
                                spread_x=30.0, spread_y=55.0, gravity=15.0, upward=True)
        return True

    elif eff_name == "quintuple_dark_stars":
        # 五連投擲：五道暗夜毒標呈扇形疾射目標
        for qi in range(5):
            qx = tx + (qi - 2) * 14
            qy = ty + math.sin(qi * 1.5) * 12
            _draw_shuriken(painter, qx, qy, p * 720, 10, QColor(160, 80, 240, alpha), True)
        return True

    elif eff_name == "shadow_bat":
        # 蝙蝠群襲：波形振翅紫黑暗夜蝙蝠群
        for i in range(4):
            delay = i * 0.12
            cur_p = max(0.0, min(1.0, (p - delay) / 0.75))
            if cur_p > 0:
                bx = cx + (tx - cx) * cur_p
                by = cy + (ty - cy) * cur_p + math.sin(cur_p * math.pi * 4 + i) * 22
                path = QPainterPath()
                path.moveTo(bx, by)
                path.lineTo(bx - 12, by - 8)
                path.lineTo(bx - 6, by + 2)
                path.lineTo(bx - 12, by + 8)
                path.closeSubpath()
                painter.setBrush(QBrush(QColor(140, 60, 220, alpha)))
                painter.setPen(QPen(QColor(220, 160, 255, alpha), 1))
                painter.drawPath(path)
        return True

    elif eff_name == "shadow_illusion":
        # 影分身投擲：3 重暗影殘影同步射鏢
        for i in range(3):
            sx = cx + (tx - cx) * min(1.0, p * 1.3)
            sy = cy + (ty - cy) * min(1.0, p * 1.3) + (i - 1) * 15
            _draw_shuriken(painter, sx, sy, rot_angle + i * 30, 10, QColor(120, 40, 200, alpha))
        return True

    elif eff_name == "shadow_servant_aura":
        # 僕從召喚：暗影替身紫色粗糲輪廓 + 暗影広霧上飄
        s_off = int(math.sin(p * 5.0) * 4)
        painter.setBrush(QBrush(QColor(20, 0, 40, int(alpha * 0.8))))
        painter.setPen(QPen(QColor(160, 60, 240, alpha), 2))
        painter.drawEllipse(QPointF(cx + 28 + s_off, cy - 40), 8, 8)
        body_path = QPainterPath()
        body_path.moveTo(cx + 28 + s_off - 10, cy - 32)
        body_path.cubicTo(cx + 28 + s_off - 14, cy - 8, cx + 28 + s_off + 14, cy - 8, cx + 28 + s_off + 10, cy - 32)
        body_path.closeSubpath()
        painter.drawPath(body_path)
        _draw_physics_particles(painter, cx + 28 + s_off, cy - 18, p, count=8,
                                color=(120, 40, 200), alpha=alpha, seed=19,
                                spread_x=16.0, spread_y=28.0, gravity=8.0, upward=True)
        return True

    elif eff_name == "shadow_spark":
        # 快速暗影鏢：爆裂的暗夜十字星標火花
        _draw_shuriken(painter, tx, ty, rot_angle * 1.5, 22, QColor(160, 70, 240, alpha), core_white=True)
        return True

    elif eff_name == "shadow_spear":
        # 暗影之矛：地面破土而出的尖銃暗影黑矛槍林 + 矛尖閃光
        for i in range(5):
            px = tx - 50 + i * 25
            spear_h = int(65 * math.sin(p * math.pi) * (0.8 + (i % 3) * 0.2))
            painter.setPen(QPen(QColor(100, 40, 160, alpha), 4))
            painter.drawLine(QPointF(px, ty + 15), QPointF(px + (i - 2) * 4, ty + 15 - spear_h))
            painter.setPen(QPen(QColor(220, 160, 255, alpha), 1.5))
            painter.drawLine(QPointF(px, ty + 15), QPointF(px + (i - 2) * 4, ty + 15 - spear_h))
            tip_x = px + (i - 2) * 4
            tip_y = ty + 15 - spear_h
            _draw_starburst(painter, tip_x, tip_y, int(5 + 4 * math.sin(p * math.pi)),
                            QColor(220, 180, 255, int(alpha * 0.9)), QColor(120, 50, 200, int(alpha * 0.9)))
        _draw_expanding_shockwave(painter, tx, ty + 15, max_radius=65, p=p,
                                 color=(100, 40, 160), alpha=alpha, aspect=0.3, rings=2)
        return True

    return False

