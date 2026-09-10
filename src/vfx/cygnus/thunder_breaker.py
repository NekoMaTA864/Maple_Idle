"""
新楓之谷 皇家騎士團 - 閃雷悍將 (Thunder Breaker) 技能特效模組
"""

import math
from PySide6.QtCore import Qt, QPointF, QRect
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath, QPolygonF
)
from vfx_core import (
    _draw_bloom_line, _draw_expanding_shockwave, _draw_physics_particles,
    _draw_crackling_lightning, _draw_starburst, _draw_magic_circle
)

THUNDER_BREAKER_EFFECTS = {
    "thunder_shark", "thunderbolt", "typhoon_wave", "god_of_the_sea",
    "lightning_cascade", "shark_sweep_charge", "electrify_surge_aura", "tidal_crash_splashes"
}


def render_thunder_breaker_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty,
                              rot_angle=0.0, seed=0.0, fracture_lines=None, **kwargs) -> bool:
    if eff_name == "electrify_surge_aura":
        # 疾風雷電：青藍雷球在身邊劇烈放電 + 閃電弧
        for ei in range(3):
            eang = rot_angle * 0.06 + ei * (math.pi * 2 / 3)
            ex = cx + math.cos(eang) * 32
            ey = cy + math.sin(eang) * 14
            painter.setBrush(QBrush(QColor(180, 240, 255, alpha)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(ex, ey), 7, 7)
            # 每個電球向角色中心放電
            _draw_crackling_lightning(painter, QPointF(ex, ey), QPointF(cx, cy - 5),
                                      p, (200, 240, 255), int(alpha * 0.6), jitter=5.0, seed=ei * 7)
        return True

    elif eff_name == "god_of_the_sea":
        # 雷神降臨：全場怒濤巨浪拍打 + 海嘯衝擊
        for i in range(3):
            wx = tx - 60 + i * 60
            painter.setBrush(QBrush(QColor(0, 140, 255, int(alpha * 0.55))))
            painter.setPen(QPen(QColor(180, 240, 255, alpha), 2))
            painter.drawEllipse(QPointF(wx, ty + 15), 45, 20)
        # 中央海浪衝擊震波
        _draw_expanding_shockwave(painter, tx, ty + 15, max_radius=110, p=p,
                                 color=(30, 160, 255), alpha=alpha, aspect=0.35, rings=2)
        # 海浪飛濺水珠
        _draw_physics_particles(painter, tx, ty + 10, p, count=16,
                                color=(140, 220, 255), alpha=alpha, seed=55,
                                spread_x=90.0, spread_y=40.0, gravity=45.0, upward=False)
        return True

    elif eff_name == "lightning_cascade":
        # 閃電連鎖：環繞電弧球向外連鎖傳導 - 4方向鋸齒電弧
        for i in range(4):
            ang = i * (math.pi / 2) + rot_angle * 0.05
            ox = tx + math.cos(ang) * 55
            oy = ty + math.sin(ang) * 55
            _draw_crackling_lightning(painter, QPointF(tx, ty), QPointF(ox, oy),
                                      p, (180, 230, 255), alpha, jitter=8.0, seed=i * 10 + 5)
        # 中心電弧球
        _draw_starburst(painter, tx, ty, int(14 + 18 * math.sin(p * math.pi)),
                        QColor(255, 255, 255, alpha), QColor(100, 210, 255, alpha))
        return True

    elif eff_name == "shark_sweep_charge":
        # 海鯊突擊：太古雷霆狂鯊幻影前衝
        painter.setPen(QPen(QColor(100, 200, 255, alpha), 4))
        painter.setBrush(QBrush(QColor(60, 160, 255, int(alpha * 0.7))))
        poly = QPolygonF([QPointF(cx, cy - 15), QPointF(tx, ty), QPointF(cx, cy + 15)])
        painter.drawPolygon(poly)
        return True

    elif eff_name == "thunder_shark":
        # 殲滅雷光 / 雷神之鯊：湛藍電弧巨鯊撲咬
        shark_p = min(1.0, p * 1.4)
        sx = cx + (tx - cx) * shark_p
        sy = cy + (ty - cy) * shark_p
        painter.save()
        painter.translate(sx, sy)
        path = QPainterPath()
        path.moveTo(25, 0)
        path.lineTo(-30, -18)
        path.lineTo(-15, 0)
        path.lineTo(-30, 18)
        path.closeSubpath()
        painter.setBrush(QBrush(QColor(0, 160, 255, alpha)))
        painter.setPen(QPen(QColor(200, 240, 255, alpha), 2))
        painter.drawPath(path)
        painter.restore()
        return True

    elif eff_name == "thunderbolt":
        # 霹靂海嘯：粗大天雷直轟地面 + 電弧擴散 + 衝擊震波
        # 主雷柱（bloom line 光暈天雷）
        _draw_bloom_line(painter, (tx, 0), (tx, ty + 20), base_width=18,
                         color=(80, 200, 255), alpha=alpha, core_white=True)
        # 落地電弧向兩側擴散
        if p > 0.3:
            imp_p = (p - 0.3) / 0.7
            _draw_crackling_lightning(painter, QPointF(tx, ty), QPointF(tx - 80, ty + 10),
                                      imp_p, (180, 230, 255), alpha, jitter=10.0, seed=11)
            _draw_crackling_lightning(painter, QPointF(tx, ty), QPointF(tx + 80, ty + 10),
                                      imp_p, (180, 230, 255), alpha, jitter=10.0, seed=22)
            # 落地衝擊波
            _draw_expanding_shockwave(painter, tx, ty + 12, max_radius=90, p=imp_p,
                                     color=(80, 200, 255), alpha=alpha, aspect=0.3, rings=2)
        return True

    elif eff_name == "tidal_crash_splashes":
        # 迴旋狂潮：三道帶電海嘯重錘砸落 + 浪花震波
        for ti in range(3):
            tx_wave = tx + (ti - 1) * 30
            # 主波浪弧線
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(120, 220, 255, alpha), 3.5))
            painter.drawArc(QRect(int(tx_wave - 20), int(ty - 25), 40, 50), -30 * 16, 240 * 16)
        # 落地衝擊波
        _draw_expanding_shockwave(painter, tx, ty + 12, max_radius=80, p=p,
                                 color=(80, 200, 255), alpha=alpha, aspect=0.28, rings=2)
        # 落水電弧飛濺
        _draw_physics_particles(painter, tx, ty + 10, p, count=12,
                                color=(180, 240, 255), alpha=alpha, seed=77,
                                spread_x=60.0, spread_y=30.0, gravity=50.0, upward=False)
        return True

    elif eff_name == "typhoon_wave":
        # 巨浪破擊：海龍捲風旋轉怒濤
        for i in range(4):
            cur_r = int((20 + i * 12) * math.sin(p * math.pi))
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(40, 180, 255, alpha), 2.5))
            painter.drawEllipse(QPointF(tx, ty + 10 - i * 16), cur_r, int(cur_r * 0.35))
        return True

    return False

