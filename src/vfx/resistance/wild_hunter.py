"""
新楓之谷 反抗軍 - 狂豹獵人 (Wild Hunter) 技能特效模組
"""

from PySide6.QtCore import Qt, QPointF, QRect
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath
)
import math
from vfx_core import (
    _draw_bloom_line,
    _draw_expanding_shockwave,
    _draw_physics_particles,
    _draw_ribbon_slash,
    _draw_starburst,
)

WILD_HUNTER_EFFECTS = {
    "wild_arrow_blast", "call_of_the_wild", "jaguar_storm", "howling_aura",
    "sonic_boom", "jaguar_claw_slash", "cross_road_charge", "silent_rampage_aura"
}


def render_wild_hunter_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty,
                          rot_angle=0.0, seed=0.0, fracture_lines=None, **kwargs) -> bool:
    if eff_name == "call_of_the_wild":
        # 狂野召喚：美洲豹金色咆哮荒野戰意光環
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 215, 60, alpha), 3.5))
        painter.drawEllipse(QPointF(cx, cy - 10), 40, 40)
        _draw_starburst(painter, cx, cy - 10, 18, QColor(255, 255, 200, alpha), QColor(255, 180, 50, alpha))
        return True

    elif eff_name == "cross_road_charge":
        # 狂暴衝刺：美洲豹衝鋒殘影破空衝撞
        painter.setPen(QPen(QColor(255, 170, 70, alpha), 5))
        painter.drawLine(QPointF(cx, cy), QPointF(tx, ty))
        _draw_starburst(painter, tx, ty, 22, QColor(255, 255, 200, alpha), QColor(255, 120, 40, alpha))
        return True

    elif eff_name == "howling_aura":
        # 咋哮：音波釋放震氣暴讀 + 暗恩風粒
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(220, 150, 50, alpha), 2.5))
        painter.drawEllipse(QPointF(cx, cy - 10), int(32 + 8 * math.sin(p * math.pi)), 18)
        _draw_expanding_shockwave(painter, cx, cy - 10, max_radius=80, p=p,
                                 color=(220, 150, 50), alpha=int(alpha * 0.6), aspect=0.5, rings=3)
        _draw_physics_particles(painter, cx, cy, p, count=8,
                                color=(200, 130, 50), alpha=alpha, seed=17,
                                spread_x=28.0, spread_y=45.0, gravity=12.0, upward=True)
        return True

    elif eff_name == "jaguar_claw_slash":
        # 利爪揮擊：巨大爪痕划破空間 + 扇面截斩
        _draw_ribbon_slash(painter, tx, ty, start_deg=-100, sweep_deg=80,
                           inner_r=15, outer_r=65, color=(210, 130, 40),
                           alpha=alpha, core_white=False)
        for ci in range(3):
            c_r = 40 - ci * 8
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(220, 150, 50, alpha), 3.5 - ci * 0.8))
            painter.drawArc(QRect(int(tx - c_r), int(ty - c_r), c_r * 2, c_r * 2),
                            -80 * 16, 130 * 16)
        _draw_starburst(painter, tx, ty, int(12 + 14 * math.sin(p * math.pi)),
                        QColor(255, 240, 180, alpha), QColor(220, 130, 40, alpha))
        return True

    elif eff_name == "jaguar_storm":
        # 美洲豹風暴：從傳送門衝出暴衝的豹群
        for ji in range(3):
            delay = ji * 0.15
            jag_p = max(0.0, min(1.0, (p - delay) / 0.7))
            if jag_p > 0:
                jx = cx + (tx - cx) * jag_p + ji * 5
                jy = ty + (ji - 1) * 18
                jag_path = QPainterPath()
                jag_path.moveTo(jx - 20, jy)
                jag_path.cubicTo(jx - 10, jy - 12, jx + 10, jy - 8, jx + 20, jy)
                jag_path.cubicTo(jx + 10, jy + 8, jx - 10, jy + 12, jx - 20, jy)
                painter.setBrush(QBrush(QColor(200, 130, 40, int(alpha * 0.8))))
                painter.setPen(QPen(QColor(255, 200, 80, alpha), 2))
                painter.drawPath(jag_path)
                _draw_physics_particles(painter, jx - 10, jy, jag_p, count=6,
                                        color=(200, 140, 50), alpha=int(alpha * 0.6), seed=ji * 5,
                                        spread_x=20.0, spread_y=10.0, gravity=25.0, upward=False)
        if p > 0.6:
            _draw_expanding_shockwave(painter, tx, ty, max_radius=70, p=(p - 0.6) / 0.4,
                                     color=(210, 130, 40), alpha=alpha, aspect=0.55, rings=2)
        return True

    elif eff_name == "silent_rampage_aura":
        # 寂靜狂怒：美洲豹金色獸瞳在身後燃燒
        painter.setBrush(QBrush(QColor(255, 215, 60, alpha)))
        painter.drawEllipse(QPointF(cx - 16, cy - 35), 8, 4)
        painter.drawEllipse(QPointF(cx + 16, cy - 35), 8, 4)
        return True

    elif eff_name == "sonic_boom":
        # 鑽石之爪 / 音爆：半球音爆震波
        rad = int(25 + 65 * p)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 180, 50, alpha), 3))
        painter.drawArc(QRect(int(tx - rad), int(ty - rad), rad * 2, rad * 2), -60 * 16, 120 * 16)
        return True

    elif eff_name == "wild_arrow_blast":
        # 狂豹狂襲：騎乘速射弩箭
        for i in range(4):
            ax = cx + (tx - cx) * min(1.0, p * 1.4 + i * 0.1)
            painter.setPen(QPen(QColor(255, 160, 60, alpha), 3))
            painter.drawLine(QPointF(ax - 20, ty + (i - 1.5) * 8), QPointF(ax, ty + (i - 1.5) * 8))
        return True

    return False

