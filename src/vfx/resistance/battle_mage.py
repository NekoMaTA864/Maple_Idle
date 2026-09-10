"""
新楓之谷 反抗軍 - 煉獄巫師 (Battle Mage) 技能特效模組
"""

import math
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient, QRadialGradient,
    QPainterPath, QPolygonF
)
from vfx_core import (
    _draw_starburst, _draw_magic_circle, _draw_bloom_line,
    _draw_ribbon_slash, _draw_expanding_shockwave, _draw_physics_particles,
    _draw_crackling_lightning
)

BATTLE_MAGE_EFFECTS = {
    "altar_annihilation_hex", "finishing_blow_scythe", "blow_finish",
    "battle_king_bar_smash", "blue_aura_ring", "dark_genesis_thunder",
    "dark_genesis", "union_aura_halo", "dark_aura", "draining_aura",
    "grim_reaper_slash", "reaper_scythe", "abyssal_lightning_storm",
    "death_contract_shield", "yellow_aura_ring"
}


def render_battle_mage_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty,
                           rot_angle=0.0, seed=0.0, fracture_lines=None, **kwargs) -> bool:
    if eff_name == "altar_annihilation_hex":
        # 【暗黑祭壇】：雙座懸浮深邃冥晶祭壇 + 高頻激光鏈索絞殺 + 碎裂電弧 + 升騰幽靈餘燼
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        altar_left = QPointF(tx - 85, ty)
        altar_right = QPointF(tx + 85, ty)

        for apt in [altar_left, altar_right]:
            ax, ay = apt.x(), apt.y()
            _draw_magic_circle(painter, ax, ay + 18, 16, rot_angle * 0.08, QColor(160, 50, 240, int(alpha * 0.7)))
            c_rad = 16 + 3 * math.sin(p * 8.0 + ax)
            poly = QPolygonF([QPointF(ax, ay - c_rad), QPointF(ax + c_rad * 0.65, ay), QPointF(ax, ay + c_rad * 0.7), QPointF(ax - c_rad * 0.65, ay)])
            painter.setBrush(QBrush(QColor(180, 50, 240, int(alpha * 0.85))))
            painter.setPen(QPen(QColor(255, 230, 255, alpha), 1.8))
            painter.drawPolygon(poly)
            _draw_starburst(painter, ax, ay - c_rad * 0.8, 8, QColor(255, 255, 255, alpha), QColor(220, 100, 255, alpha))

        _draw_bloom_line(painter, altar_left, QPointF(tx, ty), 6.5, (190, 60, 255), alpha, core_white=True)
        _draw_bloom_line(painter, altar_right, QPointF(tx, ty), 6.5, (190, 60, 255), alpha, core_white=True)
        _draw_bloom_line(painter, altar_left, altar_right, 4.0, (140, 30, 220), int(alpha * 0.65), core_white=True)

        _draw_crackling_lightning(painter, altar_left, QPointF(tx, ty), p, (220, 140, 255), alpha, jitter=14.0, seed=12)
        _draw_crackling_lightning(painter, altar_right, QPointF(tx, ty), p, (220, 140, 255), alpha, jitter=14.0, seed=34)

        _draw_expanding_shockwave(painter, tx, ty + 10, 48, p, (200, 70, 255), alpha, aspect=0.4, rings=2)
        _draw_physics_particles(painter, tx, ty, p, count=16, color=(220, 90, 255), alpha=alpha, seed=88, spread_x=45, spread_y=35, upward=True)
        _draw_starburst(painter, tx, ty, int(22 + 28 * math.sin(p * math.pi)), QColor(255, 255, 255, alpha), QColor(210, 80, 255, alpha))
        return True

    elif eff_name in ["finishing_blow_scythe", "blow_finish"]:
        # 【終極攻擊 (最後一擊)】：長杖破空撕裂，雙向帶狀網格死神斬擊流光 + 鬼爪立體爪痕 + 空間衝擊波 + 魂火餘燼
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        _draw_ribbon_slash(painter, tx - 10, ty, start_deg=-140, sweep_deg=130, inner_r=32, outer_r=68, color=(190, 60, 255), alpha=alpha, core_white=True)
        _draw_ribbon_slash(painter, tx + 10, ty, start_deg=40, sweep_deg=130, inner_r=32, outer_r=68, color=(220, 80, 255), alpha=alpha, core_white=True)

        for ci in [-1, 0, 1]:
            c_off = ci * 18
            p_start = QPointF(tx + c_off - 20, ty - 28)
            p_end = QPointF(tx + c_off + 20, ty + 28)
            _draw_bloom_line(painter, p_start, p_end, 3.5, (210, 110, 255), alpha, core_white=True)

        _draw_expanding_shockwave(painter, tx, ty, 52, p, (200, 70, 255), alpha, aspect=0.5, rings=2)
        _draw_physics_particles(painter, tx, ty, p, count=18, color=(210, 100, 255), alpha=alpha, seed=55, spread_x=70, spread_y=55, gravity=25)
        _draw_starburst(painter, tx, ty, int(20 + 26 * math.sin(p * math.pi)), QColor(255, 255, 255, alpha), QColor(200, 70, 255, alpha))
        return True

    elif eff_name == "battle_king_bar_smash":
        # 【鬥王杖擊】：巨型黑曜紫金神兵橫掃破空 -> 怒劈大地引爆高熱死靈紫光柱、碎裂冥痕與衝擊巨環
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        if p < 0.44:
            sw_p = p / 0.44
            sweep_ang = -70 + sw_p * 160
            _draw_ribbon_slash(painter, tx, ty - 5, start_deg=-70, sweep_deg=160 * sw_p, inner_r=38, outer_r=88, color=(210, 80, 255), alpha=alpha, core_white=True)

            painter.save()
            painter.translate(tx, ty - 5)
            painter.rotate(sweep_ang)
            bar_len = 130
            bar_thick = 16
            bar_grad = QLinearGradient(-bar_len // 2, 0, bar_len // 2, 0)
            bar_grad.setColorAt(0.0, QColor(220, 110, 255, alpha))
            bar_grad.setColorAt(0.2, QColor(25, 10, 35, alpha))
            bar_grad.setColorAt(0.5, QColor(255, 235, 255, alpha))
            bar_grad.setColorAt(0.8, QColor(25, 10, 35, alpha))
            bar_grad.setColorAt(1.0, QColor(220, 110, 255, alpha))
            painter.setBrush(QBrush(bar_grad))
            painter.setPen(QPen(QColor(240, 190, 255, alpha), 2))
            painter.drawRoundedRect(QRectF(-bar_len // 2, -bar_thick // 2, bar_len, bar_thick), 5, 5)
            painter.restore()

            _draw_physics_particles(painter, tx, ty - 5, sw_p, count=12, color=(220, 120, 255), alpha=int(alpha * 0.8), seed=23, spread_x=60, spread_y=40, gravity=10)
        else:
            imp_p = (p - 0.44) / 0.56
            ground_y = ty + 16

            _draw_bloom_line(painter, QPointF(tx, ty - 120), QPointF(tx, ground_y), 16.0 * (1.0 - imp_p * 0.4), (230, 90, 255), alpha, core_white=True)

            f_dist = 30 + 85 * imp_p
            fractures = [
                (tx, ground_y, tx - f_dist * 0.9, ground_y + 14),
                (tx, ground_y, tx - f_dist * 0.45, ground_y - 10),
                (tx, ground_y, tx + f_dist * 0.45, ground_y - 10),
                (tx, ground_y, tx + f_dist * 0.95, ground_y + 16),
                (tx, ground_y, tx - f_dist * 0.15, ground_y + 20),
                (tx, ground_y, tx + f_dist * 0.15, ground_y + 20),
            ]
            for x1, y1, x2, y2 in fractures:
                _draw_bloom_line(painter, QPointF(x1, y1), QPointF(x2, y2), 4.0 * (1.0 - imp_p * 0.7), (190, 60, 240), int(alpha * (1.0 - imp_p * 0.6)), core_white=True)

            _draw_expanding_shockwave(painter, tx, ground_y, 110, imp_p, (220, 100, 255), alpha, aspect=0.35, rings=2)
            _draw_physics_particles(painter, tx, ground_y, imp_p, count=22, color=(230, 130, 255), alpha=alpha, seed=99, spread_x=90, spread_y=70, gravity=60)
            _draw_starburst(painter, tx, ground_y, int(25 + 35 * math.sin(imp_p * math.pi)), QColor(255, 255, 255, alpha), QColor(200, 60, 255, alpha))
        return True

    elif eff_name == "blue_aura_ring":
        # 藍色光環：堅若磐石的深藍守護光環
        painter.setPen(QPen(QColor(80, 180, 255, alpha), 3))
        painter.drawEllipse(QPointF(cx, cy + 12), 38, 14)
        return True

    elif eff_name in ["dark_genesis_thunder", "dark_genesis"]:
        # 【暗黑世紀】：死靈黑曜神罰天降！全屏震顫，天空劈落 5 柱粗大黑曜電漿核融雷暴 + 地面死靈法陣爆縮
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        ground_y = ty + 14
        
        cir_rad = int(40 + 45 * math.sin(p * math.pi))
        _draw_magic_circle(painter, tx, ground_y, cir_rad, rot_angle * 0.05, QColor(190, 70, 255, alpha))
        _draw_magic_circle(painter, tx, 20, int(cir_rad * 0.7), -rot_angle * 0.06, QColor(220, 100, 255, int(alpha * 0.6)))

        strikes = [
            (tx, 0.0, 16, 101),
            (tx - 60, -18.0, 9, 202),
            (tx + 58, 18.0, 9, 303),
            (tx - 32, -8.0, 11, 404),
            (tx + 30, 8.0, 11, 505),
        ]
        for sx, x_drift, width, seed in strikes:
            _draw_crackling_lightning(painter, (sx + x_drift * 0.3, 0), (sx + x_drift, ground_y), p,
                                      QColor(180, 60, 255), alpha, jitter=14.0, steps=7, seed=seed)
            if width >= 14:
                _draw_bloom_line(painter, (sx, 0), (sx, ground_y), base_width=width,
                                 color=QColor(230, 120, 255), alpha=alpha, core_white=True)

        _draw_expanding_shockwave(painter, tx, ground_y, max_radius=120, p=p,
                                 color=QColor(240, 150, 255), alpha=alpha, aspect=0.35, rings=2)
        _draw_bloom_line(painter, (tx - 55, ground_y), (tx + 55, ground_y), base_width=5,
                         color=QColor(255, 200, 255), alpha=int(alpha * (1.0 - p * 0.5)), core_white=True)
        _draw_bloom_line(painter, (tx - 35, ground_y - 8), (tx + 35, ground_y + 8), base_width=3,
                         color=QColor(210, 100, 255), alpha=int(alpha * (1.0 - p * 0.6)), core_white=False)

        _draw_physics_particles(painter, tx, ground_y - 5, p, count=26,
                                color=QColor(255, 190, 255), alpha=alpha, seed=998,
                                spread_x=90.0, spread_y=60.0, gravity=180.0, upward=False)
        _draw_starburst(painter, tx, ground_y - 15, int(25 + 35 * math.sin(p * math.pi)),
                        QColor(255, 255, 255, alpha), QColor(210, 80, 255, alpha))
        return True

    elif eff_name == "union_aura_halo":
        # 【聯盟光環】：四色神級光環融合爆發！地面紫金星陣 + 4 顆帶狀流光神珠 + 貫天死神核融光柱 + 升騰幽冥魂火
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        _draw_magic_circle(painter, cx, cy + 18, int(42 + 10 * math.sin(p * math.pi)), rot_angle * 0.05, QColor(220, 100, 255, alpha))
        _draw_magic_circle(painter, cx, cy + 18, int(22 + 6 * math.sin(p * math.pi)), -rot_angle * 0.08, QColor(255, 220, 100, int(alpha * 0.7)))

        orbs_info = [
            (QColor(255, 55, 75, alpha), 0.0),
            (QColor(255, 220, 45, alpha), math.pi * 0.5),
            (QColor(50, 195, 255, alpha), math.pi * 1.0),
            (QColor(65, 255, 140, alpha), math.pi * 1.5),
        ]
        orb_pts = []
        rx = 52 + 8 * math.sin(p * math.pi)
        ry = 20 + 4 * math.sin(p * math.pi)
        for col, phase_offset in orbs_info:
            ang = rot_angle * 0.09 + phase_offset
            ox = cx + math.cos(ang) * rx
            oy = cy - 6 + math.sin(ang) * ry
            orb_pts.append(QPointF(ox, oy))

            rg = QRadialGradient(ox, oy, 13)
            rg.setColorAt(0.0, QColor(255, 255, 255, alpha))
            rg.setColorAt(0.45, col)
            rg.setColorAt(1.0, QColor(col.red(), col.green(), col.blue(), 0))
            painter.setBrush(QBrush(rg))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(ox, oy), 13, 13)
            _draw_starburst(painter, ox, oy, 9, QColor(255, 255, 255, alpha), col)

            deg = math.degrees(ang)
            _draw_ribbon_slash(painter, cx, cy - 6, start_deg=deg - 55, sweep_deg=55,
                               inner_r=rx - 8, outer_r=rx + 8, color=col, alpha=int(alpha * 0.6), core_white=False)

        if len(orb_pts) == 4:
            for idx1, idx2 in [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (1, 3)]:
                _draw_bloom_line(painter, orb_pts[idx1], orb_pts[idx2], base_width=3,
                                 color=QColor(240, 200, 255), alpha=int(alpha * 0.65), core_white=True)

        beam_w = int(28 + 14 * math.sin(p * math.pi))
        _draw_bloom_line(painter, (cx, cy + 18), (cx, cy - 85), base_width=beam_w,
                         color=QColor(220, 100, 255), alpha=int(alpha * 0.85), core_white=True)

        _draw_physics_particles(painter, cx, cy + 12, p, count=20,
                                color=QColor(255, 230, 160), alpha=alpha, seed=777,
                                spread_x=36.0, spread_y=75.0, gravity=25.0, upward=True)
        return True

    elif eff_name == "dark_aura":
        # 黑暗光環：腳底旋轉黑紫色魔法陣
        _draw_magic_circle(painter, cx, cy + 15, int(35 + 10 * math.sin(p * math.pi)), rot_angle * 0.03, QColor(140, 40, 200, alpha))
        return True

    elif eff_name == "draining_aura":
        # 吸收光環：生命吸取魔力螺旋
        for i in range(4):
            ang = rot_angle * 0.05 + i * (math.pi / 2)
            dx = cx + math.cos(ang) * 35
            dy = cy + math.sin(ang) * 15
            painter.setBrush(QBrush(QColor(80, 255, 140, alpha)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(dx, dy), 6, 6)
        return True

    elif eff_name in ["grim_reaper_slash", "reaper_scythe"]:
        # 【死神召喚】：太古死神虛空裂隙降臨！170° 巨型黑曜月牙帶狀流光斬裂空間 + 空間撕裂斷層
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        rift_cx = tx
        rift_cy = ty - 32
        rift_w = int(48 + 25 * math.sin(p * math.pi))
        rift_h = int(22 + 12 * math.sin(p * math.pi))
        rg = QRadialGradient(rift_cx, rift_cy, rift_w)
        rg.setColorAt(0.0, QColor(15, 5, 25, int(alpha * 0.95)))
        rg.setColorAt(0.5, QColor(110, 25, 170, int(alpha * 0.75)))
        rg.setColorAt(0.9, QColor(190, 70, 255, int(alpha * 0.4)))
        rg.setColorAt(1.0, QColor(190, 70, 255, 0))
        painter.setBrush(QBrush(rg))
        painter.setPen(QPen(QColor(220, 140, 255, int(alpha * 0.8)), 1.5))
        painter.drawEllipse(QPointF(rift_cx, rift_cy), rift_w, rift_h)

        eye_y = rift_cy - 2
        painter.setBrush(QBrush(QColor(255, 30, 70, alpha)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(rift_cx - 9, eye_y), 3.5, 2.0)
        painter.drawEllipse(QPointF(rift_cx + 9, eye_y), 3.5, 2.0)

        slash_start = -115 + p * 50
        _draw_ribbon_slash(painter, tx, ty, start_deg=slash_start, sweep_deg=170,
                           inner_r=25, outer_r=96, color=QColor(220, 60, 255), alpha=alpha, core_white=True)

        slash_ang = -75 + p * 145
        painter.save()
        painter.translate(tx, ty)
        painter.rotate(slash_ang)
        scythe_len = 84
        scythe_path = QPainterPath()
        scythe_path.moveTo(-scythe_len * 0.6, scythe_len * 0.4)
        scythe_path.lineTo(scythe_len * 0.3, -scythe_len * 0.35)
        scythe_path.quadTo(scythe_len * 0.7, -scythe_len * 0.85, scythe_len * 0.95, -scythe_len * 0.4)
        scythe_path.quadTo(scythe_len * 0.65, -scythe_len * 0.5, scythe_len * 0.3, -scythe_len * 0.35)

        blade_grad = QLinearGradient(0, -scythe_len * 0.8, scythe_len, 0)
        blade_grad.setColorAt(0.0, QColor(255, 255, 255, alpha))
        blade_grad.setColorAt(0.3, QColor(210, 80, 255, int(alpha * 0.95)))
        blade_grad.setColorAt(0.7, QColor(100, 20, 160, int(alpha * 0.8)))
        blade_grad.setColorAt(1.0, QColor(20, 10, 30, int(alpha * 0.9)))
        painter.setBrush(QBrush(blade_grad))
        painter.setPen(QPen(QColor(240, 180, 255, alpha), 2))
        painter.drawPath(scythe_path)
        painter.restore()

        _draw_bloom_line(painter, (tx - 45, ty - 32), (tx + 45, ty + 32), base_width=4.5,
                         color=QColor(255, 220, 255), alpha=alpha, core_white=True)
        _draw_bloom_line(painter, (tx + 40, ty - 30), (tx - 40, ty + 30), base_width=3.0,
                         color=QColor(200, 80, 255), alpha=int(alpha * 0.85), core_white=False)

        _draw_expanding_shockwave(painter, tx, ty, max_radius=88, p=p,
                                 color=QColor(230, 80, 255), alpha=alpha, aspect=0.55, rings=2)
        _draw_physics_particles(painter, tx, ty, p, count=24,
                                color=QColor(210, 80, 255), alpha=alpha, seed=888,
                                spread_x=75.0, spread_y=60.0, gravity=85.0, upward=False)
        _draw_starburst(painter, tx, ty, int(22 + 28 * math.sin(p * math.pi)),
                        QColor(255, 255, 255, alpha), QColor(220, 70, 255, alpha))
        return True

    elif eff_name == "abyssal_lightning_storm":
        # 【深淵雷電】：撕開虛空冥界黑雷風暴！5 條暴走碎形電漿狂暴穿刺 + 中心核融電漿球 + 衝擊波環
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        arcs = [
            (tx - 65, ty - 45, tx + 60, ty + 35, 11),
            (tx + 60, ty - 40, tx - 55, ty + 40, 22),
            (tx, ty - 75, tx + 12, ty + 45, 33),
            (tx - 50, ty + 45, tx + 50, ty - 35, 44),
            (tx - 70, ty, tx + 70, ty - 10, 55),
        ]
        for x1, y1, x2, y2, seed in arcs:
            _draw_crackling_lightning(painter, (x1, y1), (x2, y2), p,
                                      QColor(180, 60, 255), alpha, jitter=18.0, steps=6, seed=seed)

        rg = QRadialGradient(tx, ty, 32)
        rg.setColorAt(0.0, QColor(255, 255, 255, alpha))
        rg.setColorAt(0.35, QColor(210, 110, 255, int(alpha * 0.9)))
        rg.setColorAt(0.75, QColor(140, 30, 220, int(alpha * 0.5)))
        rg.setColorAt(1.0, QColor(70, 10, 140, 0))
        painter.setBrush(QBrush(rg))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(tx, ty), 32, 32)

        _draw_bloom_line(painter, (tx - 38, ty), (tx + 38, ty), base_width=4,
                         color=QColor(240, 180, 255), alpha=alpha, core_white=True)
        _draw_bloom_line(painter, (tx, ty - 38), (tx, ty + 38), base_width=4,
                         color=QColor(240, 180, 255), alpha=alpha, core_white=True)

        _draw_expanding_shockwave(painter, tx, ty, max_radius=82, p=p,
                                 color=QColor(210, 120, 255), alpha=alpha, aspect=0.7, rings=2)
        _draw_physics_particles(painter, tx, ty, p, count=22,
                                color=QColor(200, 130, 255), alpha=alpha, seed=555,
                                spread_x=65.0, spread_y=65.0, gravity=45.0, upward=False)
        _draw_starburst(painter, tx, ty, int(20 + 26 * math.sin(p * math.pi)),
                        QColor(255, 255, 255, alpha), QColor(170, 70, 255, alpha))
        return True

    elif eff_name == "death_contract_shield":
        # 【死神庇護】：太古死神巨大骨翼包覆守護！全隊周身展開高維六角晶格符文護盾 + 骨脈白熾光 + 靈魂餘燼升騰
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        wing_span = 58 + 12 * math.sin(p * math.pi)
        for sign in [-1, 1]:
            w_path = QPainterPath()
            w_path.moveTo(cx, cy - 8)
            w_path.quadTo(cx + sign * wing_span * 0.6, cy - 50, cx + sign * wing_span, cy - 26)
            w_path.quadTo(cx + sign * (wing_span - 8), cy + 14, cx + sign * (wing_span * 0.4), cy + 26)
            w_path.quadTo(cx + sign * 15, cy + 8, cx, cy - 8)

            w_grad = QLinearGradient(cx, cy - 32, cx + sign * wing_span, cy)
            w_grad.setColorAt(0.0, QColor(200, 100, 255, int(alpha * 0.8)))
            w_grad.setColorAt(0.5, QColor(110, 30, 160, int(alpha * 0.6)))
            w_grad.setColorAt(1.0, QColor(25, 5, 45, 0))
            painter.setBrush(QBrush(w_grad))
            painter.setPen(QPen(QColor(230, 170, 255, int(alpha * 0.85)), 1.8))
            painter.drawPath(w_path)

            for bi in [0.35, 0.65]:
                bx = cx + sign * wing_span * bi
                by = cy - 26 + bi * 22
                _draw_bloom_line(painter, (cx, cy - 8), (bx, by), base_width=2.5,
                                 color=QColor(255, 200, 255), alpha=int(alpha * 0.9), core_white=True)

        shield_rad = int(38 + 6 * math.sin(p * 6.0))
        s_rg = QRadialGradient(cx, cy - 6, shield_rad)
        s_rg.setColorAt(0.0, QColor(180, 90, 255, int(alpha * 0.18)))
        s_rg.setColorAt(0.75, QColor(150, 60, 230, int(alpha * 0.45)))
        s_rg.setColorAt(1.0, QColor(230, 170, 255, int(alpha * 0.9)))
        painter.setBrush(QBrush(s_rg))
        painter.setPen(QPen(QColor(240, 200, 255, alpha), 2))
        painter.drawEllipse(QPointF(cx, cy - 6), shield_rad, shield_rad)

        for ri in range(6):
            r_ang = rot_angle * 0.05 + ri * (math.pi / 3)
            rx = cx + math.cos(r_ang) * (shield_rad + 6)
            ry = cy - 6 + math.sin(r_ang) * (shield_rad + 6)
            painter.setBrush(QBrush(QColor(255, 235, 255, alpha)))
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(QPolygonF([QPointF(rx, ry - 3.5), QPointF(rx + 3.5, ry), QPointF(rx, ry + 3.5), QPointF(rx - 3.5, ry)]))

        _draw_expanding_shockwave(painter, cx, cy - 6, max_radius=60, p=p,
                                 color=QColor(220, 160, 255), alpha=alpha, aspect=1.0, rings=1)
        _draw_physics_particles(painter, cx, cy + 14, p, count=16,
                                color=QColor(240, 210, 255), alpha=alpha, seed=444,
                                spread_x=32.0, spread_y=55.0, gravity=20.0, upward=True)
        return True

    elif eff_name == "yellow_aura_ring":
        # 黃色光環：明亮耀眼的極速光環擴散
        painter.setPen(QPen(QColor(255, 235, 60, alpha), 3))
        painter.drawEllipse(QPointF(cx, cy + 12), 38, 14)
        return True

    return False

