"""
新楓之谷 反抗軍 - 機甲戰神 (Mechanic) 技能特效模組
"""

import math
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QRadialGradient
)
from vfx_core import (
    _draw_starburst,
    _draw_bloom_line,
    _draw_expanding_shockwave,
    _draw_crackling_lightning,
    _draw_magic_circle,
)

MECHANIC_EFFECTS = {
    "full_metal_jacket", "laser_blast", "support_gate", "ap_salvo_plus",
    "robot_launcher", "homing_beacon_cluster", "tank_mode_aura", "distortion_bomb_singularity"
}


def render_mechanic_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty,
                        rot_angle=0.0, seed=0.0, fracture_lines=None, **kwargs) -> bool:
    if eff_name == "ap_salvo_plus":
        # 重機槍掃射：高頻破甲黃金彈道連綿激射
        for bi in range(6):
            b_t = (p * 2.8 + bi * 0.18) % 1.0
            bx = cx + (tx - cx) * b_t + (bi % 2 - 0.5) * 8
            by = (cy - 12) + (ty - (cy - 12)) * b_t + (bi % 3 - 1) * 6
            painter.setPen(QPen(QColor(255, 220, 60, int(alpha * 0.9)), 2.5))
            painter.drawLine(QPointF(bx - 14, by), QPointF(bx + 14, by))
        _draw_starburst(painter, cx + 25, cy - 12, int(10 + 12 * math.sin(p * math.pi)), QColor(255, 255, 200, alpha), QColor(255, 140, 30, alpha))
        return True

    elif eff_name == "distortion_bomb_singularity":
        # 重力扭曲彈：中心超重力黑洞吸積盤坍縮
        b_rad = int(25 + 45 * math.sin(p * math.pi))
        painter.setBrush(QBrush(QColor(20, 10, 40, int(alpha * 0.9))))
        painter.setPen(QPen(QColor(160, 100, 255, alpha), 2))
        painter.drawEllipse(QPointF(tx, ty), b_rad, b_rad)
        return True

    elif eff_name == "full_metal_jacket":
        # 重裝機槍：雙聯裝高射速機槍彈道激射
        for i in range(4):
            ax = cx + (tx - cx) * min(1.0, p * 1.5 + i * 0.1)
            ay = cy + (ty - cy) * min(1.0, p * 1.5 + i * 0.1) + (i - 1.5) * 6
            painter.setPen(QPen(QColor(100, 200, 255, alpha), 3))
            painter.drawLine(QPointF(ax - 18, ay), QPointF(ax, ay))
        return True

    elif eff_name == "homing_beacon_cluster":
        # 追蹤導向飛彈：肩膀導彈貢射很 + S型飛行尾焰
        for mi in range(4):
            delay = mi * 0.1
            mis_p = max(0.0, min(1.0, (p - delay) / 0.7))
            if mis_p > 0:
                mx = cx + (tx - cx) * mis_p + math.sin(mis_p * 8 + mi) * 12
                my = cy + (ty - cy) * mis_p - math.sin(mis_p * math.pi) * 30
                painter.setBrush(QBrush(QColor(255, 120, 40, int(alpha * 0.8))))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(mx, my), 5, 5)
                # 尾焰亮炸
                if mis_p > 0.1:
                    _draw_bloom_line(painter, (mx - 12, my + 5), (mx, my),
                                     base_width=3, color=(255, 140, 40), alpha=int(alpha * 0.6), core_white=False)
        # 命中爆炸
        if p > 0.7:
            exp_p = (p - 0.7) / 0.3
            _draw_expanding_shockwave(painter, tx, ty, max_radius=55, p=exp_p,
                                     color=(255, 120, 40), alpha=alpha, aspect=0.6, rings=2)
        return True

    elif eff_name == "laser_blast":
        # 巨型雷射砲：雙管高能激光射穿全場 + 電氣衝擊
        # 主雷射光柱 (bloom lines)
        for off in [-6, 6]:
            _draw_bloom_line(painter, (cx, cy + off), (tx, ty + off),
                             base_width=7, color=(60, 180, 255), alpha=alpha, core_white=True)
        # 槍口的蔑變閃光
        _draw_starburst(painter, cx + 20, cy, int(12 + 10 * math.sin(p * math.pi * 3)),
                        QColor(255, 255, 255, alpha), QColor(80, 200, 255, alpha))
        # 命中的震波
        if p > 0.4:
            hit_p = (p - 0.4) / 0.6
            _draw_expanding_shockwave(painter, tx, ty, max_radius=70, p=hit_p,
                                     color=(60, 180, 255), alpha=alpha, aspect=0.55, rings=2)
        return True

    elif eff_name == "robot_launcher":
        # 機器人轟炸：重裝機器人空降轟炸引爆地表衝擊波
        painter.setPen(QPen(QColor(255, 60, 40, alpha), 2))
        painter.drawLine(QPointF(tx - 20, ty), QPointF(tx + 20, ty))
        painter.drawLine(QPointF(tx, ty - 20), QPointF(tx, ty + 20))
        painter.drawEllipse(QPointF(tx, ty), 16, 16)
        if p >= 0.35:
            exp_p = (p - 0.35) / 0.65
            rad = int(25 + 55 * exp_p)
            rg = QRadialGradient(tx, ty, rad)
            rg.setColorAt(0.0, QColor(255, 255, 220, int(255 * (1.0 - exp_p))))
            rg.setColorAt(0.5, QColor(255, 100, 30, int(220 * (1.0 - exp_p))))
            rg.setColorAt(1.0, QColor(255, 40, 20, 0))
            painter.setBrush(QBrush(rg))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(tx, ty), rad, int(rad * 0.55))
        return True

    elif eff_name == "support_gate":
        # 支援磁場：技術傳送門電弧圈陣 + 科幻藍色旋轉法陣
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(60, 180, 255, alpha), 2.5))
        painter.drawEllipse(QPointF(cx, cy + 10), 36, 16)
        # 間歇男峓電弧
        for ei in range(3):
            eang = rot_angle * 0.08 + ei * (math.pi * 2 / 3)
            ex = cx + math.cos(eang) * 35
            ey = (cy + 10) + math.sin(eang) * 16
            _draw_crackling_lightning(painter, QPointF(cx, cy + 10), QPointF(ex, ey),
                                      p, (80, 200, 255), int(alpha * 0.6), jitter=6.0, seed=ei * 9)
        # 旋轉科幻法陣
        _draw_magic_circle(painter, cx, cy + 10, int(28 + 6 * math.sin(p * math.pi)),
                           rot_angle * 0.07, QColor(60, 180, 255, int(alpha * 0.7)))
        return True

    elif eff_name == "tank_mode_aura":
        # 金屬機甲：坦克：周身展開金屬重裝磁力防護罩
        painter.setPen(QPen(QColor(120, 220, 255, alpha), 2, Qt.DashLine))
        painter.drawRoundedRect(QRectF(cx - 32, cy - 36, 64, 56), 10, 10)
        return True

    return False

