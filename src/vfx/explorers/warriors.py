"""
新楓之谷 冒險家 劍士 (英雄 / 黑騎士 / 聖騎士) 技能特效渲染模組 (warriors.py)
"""

import math
import random
from PySide6.QtCore import Qt, QPointF, QRect, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QRadialGradient,
    QPainterPath, QPolygonF
)
from vfx_core import (
    _draw_starburst, _draw_combo_orb, _draw_shuriken, _draw_magic_circle,
    _draw_bloom_line, _draw_ribbon_slash, _draw_expanding_shockwave,
    _draw_physics_particles, _draw_crackling_lightning,
    ease_in_out, ease_out_quad, ease_in_quad, ease_out_cubic, ease_out_sine
)

WARRIORS_EFFECTS = {'beholder_eye', 'sanctuary_hammer', 'divine_charge_slash', 'dimension_rift', 'beam_blade_slash', 'divine_echo', 'x_cross_slash', 'beholder_laser', 'valhalla_aura', 'grand_cross', 'hyper_body_aura', 'spear_forest', 'reincarnation_wings', 'combo_fury_smash', 'mjolnir_throw', 'dark_dragon_thrust', 'smite_cross', 'cyclone_spear_spin', 'gungnir_spear', 'soul_blade', 'vertical_cleave', 'combo_orbs', 'elemental_blast', 'elemental_force_aura'}


def render_warriors_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty,
                       rot_angle=0.0, seed=0.0, fracture_lines=None, **kwargs) -> bool:
    if eff_name == "x_cross_slash":
        # 狂暴之怒：雙刃交叉裂空火刃 (42°/-42° 雙刀光 + 8角星芒)
        blade_span = int(48 + 52 * math.sin(p * math.pi * 0.95))
        thick = max(3, int(11 * (1.0 - p * 0.7)))
        for sign in [1, -1]:
            painter.save()
            painter.translate(tx, ty)
            painter.rotate(sign * 42)
            path = QPainterPath()
            path.moveTo(-blade_span, -thick * 0.5)
            path.quadTo(0, -thick * 2.3, blade_span, -thick * 0.5)
            path.lineTo(blade_span + 8 * p, 0)
            path.quadTo(0, thick * 2.3, -blade_span, thick * 0.5)
            path.closeSubpath()
            grad = QLinearGradient(-blade_span, 0, blade_span, 0)
            grad.setColorAt(0.0, QColor(r, g, b, 0))
            grad.setColorAt(0.2, QColor(r, g, b, int(alpha * 0.85)))
            grad.setColorAt(0.5, QColor(255, 235, 160, alpha))
            grad.setColorAt(0.8, QColor(r, g, b, int(alpha * 0.85)))
            grad.setColorAt(1.0, QColor(r, g, b, 0))
            painter.setBrush(QBrush(grad))
            painter.setPen(QPen(QColor(255, 120, 50, alpha), 1.5))
            painter.drawPath(path)
            painter.setPen(QPen(QColor(255, 255, 255, alpha), max(1, int(thick * 0.4))))
            painter.drawLine(QPointF(-blade_span * 0.85, 0), QPointF(blade_span * 0.85, 0))
            painter.restore()
        _draw_starburst(painter, tx, ty, int(14 + 28 * math.sin(p * math.pi)), QColor(255, 255, 220, alpha), QColor(r, g, b, int(alpha * 0.7)))
        return True
    elif eff_name == "dimension_rift":
        # 空間斬：碎裂玻璃裂網與中心次元黑洞吸積盤
        lines = fracture_lines or [
            ((tx, ty), (tx + 50, ty - 45), (tx + 110, ty - 80)),
            ((tx, ty), (tx - 60, ty - 35), (tx - 120, ty - 60)),
            ((tx, ty), (tx + 40, ty + 50), (tx + 95, ty + 90)),
            ((tx, ty), (tx - 50, ty + 45), (tx - 105, ty + 80)),
        ]
        painter.setPen(QPen(QColor(r, g, b, int(alpha * 0.7)), max(2, int(7 * (1.0 - p)))))
        for p_start, p_mid, p_end in lines:
            painter.drawLine(QPointF(p_start[0], p_start[1]), QPointF(p_mid[0], p_mid[1]))
            painter.drawLine(QPointF(p_mid[0], p_mid[1]), QPointF(p_end[0], p_end[1]))
        painter.setPen(QPen(QColor(255, 255, 255, alpha), 2))
        for p_start, p_mid, p_end in lines:
            painter.drawLine(QPointF(p_start[0], p_start[1]), QPointF(p_mid[0], p_mid[1]))
        core_rad = int(20 + 60 * math.sin(p * math.pi))
        rg = QRadialGradient(tx, ty, core_rad)
        rg.setColorAt(0.0, QColor(10, 5, 25, int(alpha * 0.95)))
        rg.setColorAt(0.5, QColor(r, g, b, int(alpha * 0.8)))
        rg.setColorAt(0.85, QColor(255, 180, 240, int(alpha * 0.4)))
        rg.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(rg))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(tx, ty), core_rad, core_rad)
        return True
    elif eff_name == "vertical_cleave":
        # 終極攻擊：天降金熾巨刃垂直怒劈貫頂
        b_drop = min(1.0, p * 2.5)
        top_y = (ty - 140) + 100 * b_drop
        tip_y = top_y + 100
        blade_w = max(12, int(26 * (1.0 - p * 0.5)))
        painter.save()
        path_blade = QPainterPath()
        path_blade.moveTo(tx - blade_w * 0.5, top_y)
        path_blade.lineTo(tx + blade_w * 0.5, top_y)
        path_blade.lineTo(tx + blade_w * 0.35, tip_y - 15)
        path_blade.lineTo(tx, tip_y)
        path_blade.lineTo(tx - blade_w * 0.35, tip_y - 15)
        path_blade.closeSubpath()
        grad = QLinearGradient(tx - blade_w, 0, tx + blade_w, 0)
        grad.setColorAt(0.0, QColor(255, 180, 40, 0))
        grad.setColorAt(0.5, QColor(255, 255, 240, alpha))
        grad.setColorAt(1.0, QColor(255, 180, 40, 0))
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(QColor(255, 220, 100, alpha), 1.5))
        painter.drawPath(path_blade)
        painter.restore()
        if p >= 0.2:
            imp_p = (p - 0.2) / 0.8
            rx = int(20 + 75 * imp_p)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(255, 215, 60, int(255 * (1.0 - imp_p))), max(2, int(5 * (1.0 - imp_p)))))
            painter.drawEllipse(QPointF(tx, ty + 16), rx, int(rx * 0.3))
        return True
    elif eff_name == "soul_blade":
        # 燃燒之劍：懸空靈魂神劍破空重劈地表岩漿裂痕 + 爆炎地裂
        sw_x = tx - 30 + math.sin(p * 20) * 2.0
        sw_base = ty + 15
        path_blade = QPainterPath()
        path_blade.moveTo(sw_x - 6, sw_base - 75)
        path_blade.lineTo(sw_x + 6, sw_base - 75)
        path_blade.lineTo(sw_x + 4, sw_base - 10)
        path_blade.lineTo(sw_x, sw_base + 4)
        path_blade.lineTo(sw_x - 4, sw_base - 10)
        path_blade.closeSubpath()
        painter.setBrush(QBrush(QColor(255, 120, 20, alpha)))
        painter.setPen(QPen(QColor(255, 240, 150, alpha), 1.5))
        painter.drawPath(path_blade)
        for ring_i in range(3):
            r_ph = (p * 2.2 + ring_i * 0.33) % 1.0
            r_y = sw_base - (r_ph * 70)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(255, 100 + ring_i * 45, 30, int(alpha * (1.0 - r_ph * 0.5))), 2))
            painter.drawEllipse(QPointF(sw_x, r_y), 15, 6)
        # 砸地衝擊：大劍橫掃弧面 + 火燼爆散
        if p > 0.45:
            sw_p = (p - 0.45) / 0.55
            _draw_ribbon_slash(painter, sw_x, sw_base, start_deg=-80, sweep_deg=160,
                               inner_r=20, outer_r=70, color=(255, 120, 30), alpha=int(alpha * sw_p), core_white=True)
            _draw_expanding_shockwave(painter, sw_x, sw_base, max_radius=70, p=sw_p,
                                     color=(255, 100, 20), alpha=alpha, aspect=0.32, rings=2)
            _draw_physics_particles(painter, sw_x, sw_base, sw_p, count=16,
                                    color=(255, 140, 40), alpha=alpha, seed=31,
                                    spread_x=55.0, spread_y=35.0, gravity=65.0, upward=False)
        return True
    elif eff_name == "combo_orbs":
        # 鬥氣本能：周身 8 顆旋轉鬥氣球與脈衝衝擊波
        rx, ry = 52, 18
        for i in range(8):
            ang = i * (math.pi * 2 / 8) + rot_angle * 0.04
            ox = cx + math.cos(ang) * rx
            oy = (cy - 10) + math.sin(ang) * ry
            _draw_combo_orb(painter, ox, oy, scale=0.85, alpha=alpha)
        wave_r = int(20 + 240 * p)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(80, 180, 255, int(alpha * 0.6)), max(1, int(4 * (1.0 - p)))))
        painter.drawEllipse(QPointF(cx, cy - 10), wave_r, int(wave_r * 0.6))

    # =========================================================================
    # 2. 黑騎士 (Dark Knight)
    # =========================================================================
        return True
    elif eff_name == "valhalla_aura":
        # 劍士意念：英靈聖光之翼與金黃巨劍環繞光環
        for wing_sign in [-1, 1]:
            w_path = QPainterPath()
            w_path.moveTo(cx, cy - 20)
            w_path.cubicTo(cx + wing_sign * 55, cy - 65, cx + wing_sign * 75, cy - 10, cx + wing_sign * 25, cy + 10)
            w_path.cubicTo(cx + wing_sign * 45, cy - 20, cx + wing_sign * 20, cy - 35, cx, cy - 20)
            painter.setBrush(QBrush(QColor(255, 215, 80, int(alpha * 0.7))))
            painter.setPen(QPen(QColor(255, 250, 200, alpha), 1.5))
            painter.drawPath(w_path)
        _draw_starburst(painter, cx, cy - 25, int(18 + 24 * math.sin(p * math.pi)), QColor(255, 255, 220, alpha), QColor(255, 180, 50, alpha))
        return True
    elif eff_name == "beam_blade_slash":
        # 劍氣斬：半月形連環劍氣衝擊波向右突進
        for bi in range(3):
            b_offset = (p * 120 + bi * 25)
            bx = cx + b_offset
            by = cy - 20 + math.sin(bi * 1.5) * 10
            b_span = 35 + bi * 8
            painter.setPen(QPen(QColor(255, 120 + bi * 40, 50, int(alpha * (1.0 - bi * 0.2))), 3.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawArc(QRect(int(bx - 15), int(by - b_span), 30, b_span * 2), -60 * 16, 120 * 16)
        return True
    elif eff_name == "combo_fury_smash":
        # 鬥氣衝擊：巨型鐵鏈鎖定敵人並從天怒扣崩裂地表 + 地裂震波
        chain_y = min(ty, (ty - 120) + 120 * min(1.0, p * 2.2))
        painter.setPen(QPen(QColor(240, 70, 40, alpha), 3))
        painter.drawLine(QPointF(cx, cy - 30), QPointF(tx, chain_y))
        if p >= 0.3:
            s_p = (p - 0.3) / 0.7
            s_rad = int(25 + 65 * s_p)
            painter.setPen(QPen(QColor(255, 100, 30, int(255 * (1.0 - s_p))), 2.5))
            painter.drawEllipse(QPointF(tx, ty), s_rad, int(s_rad * 0.35))
            # 砸地震波 + 鬥氣爆散
            _draw_expanding_shockwave(painter, tx, ty + 10, max_radius=90, p=s_p,
                                     color=(255, 80, 30), alpha=alpha, aspect=0.32, rings=2)
            _draw_physics_particles(painter, tx, ty + 8, s_p, count=14,
                                    color=(255, 120, 40), alpha=alpha, seed=88,
                                    spread_x=60.0, spread_y=35.0, gravity=60.0, upward=True)

    # =========================================================================
    # 5. 黑騎士新增技能 (Dark Knight 6~8)
    # =========================================================================
        return True
    elif eff_name == "dark_dragon_thrust":
        # 暗黑穿刺：紫黑狂龍長槍三連突刺破空錐
        for i in range(3):
            delay = i * 0.12
            cur_p = max(0.0, min(1.0, (p - delay) / 0.75))
            if cur_p > 0:
                sx = cx + (tx - cx) * min(1.0, cur_p * 1.4)
                sy = cy + (ty - cy) * min(1.0, cur_p * 1.4) + (i - 1) * 16
                painter.setPen(QPen(QColor(160, 60, 240, int(alpha * (1.0 - cur_p * 0.4))), 5))
                painter.drawLine(QPointF(sx - 45, sy), QPointF(sx, sy))
                painter.setPen(QPen(QColor(255, 220, 255, alpha), 2))
                painter.drawLine(QPointF(sx - 25, sy), QPointF(sx + 8, sy))
                # 破空錐
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(QColor(180, 100, 255, int(alpha * 0.7)), 1.5))
                painter.drawArc(QRect(int(sx - 15), int(sy - 15), 30, 30), 45 * 16, 90 * 16)
        return True
    elif eff_name == "gungnir_spear":
        # 永恆死槍：死神巨矛從天際直貫大地引發暗雷爆發 + 瓦爾哈拉符文召喚
        spear_y = (ty - 160) + 160 * min(1.0, p * 2.2)
        # 召喚符文陣 (p < 0.4)
        if p < 0.4:
            _draw_magic_circle(painter, tx, ty - 60, int(28 + 12 * p * 2.5),
                               rot_angle * 0.06, QColor(160, 60, 240, alpha))
        # 巨矛貫穿 (bloom line 替換雙重直線)
        _draw_bloom_line(painter, (tx, spear_y - 90), (tx, spear_y + 15),
                         base_width=10, color=(140, 50, 220), alpha=alpha, core_white=True)
        # 落地衝擊
        if p > 0.35:
            imp = (p - 0.35) / 0.65
            rg_imp = QRadialGradient(tx, ty, int(35 + 85 * imp))
            rg_imp.setColorAt(0.0, QColor(200, 100, 255, int(alpha * 0.8)))
            rg_imp.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(rg_imp))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(tx, ty), int(35 + 85 * imp), int((35 + 85 * imp) * 0.5))
            _draw_expanding_shockwave(painter, tx, ty + 8, max_radius=100, p=imp,
                                     color=(160, 60, 240), alpha=alpha, aspect=0.38, rings=2)
            _draw_physics_particles(painter, tx, ty + 8, imp, count=16,
                                    color=(180, 80, 255), alpha=alpha, seed=44,
                                    spread_x=65.0, spread_y=40.0, gravity=55.0, upward=False)
        return True
    elif eff_name == "beholder_eye":
        # 召喚魔眼：盤旋血紅魔眼射出監視射線與符文
        eye_x = cx + 25 + math.cos(rot_angle * 0.03) * 35
        eye_y = cy - 45 + math.sin(rot_angle * 0.03) * 12
        painter.setBrush(QBrush(QColor(120, 20, 180, alpha)))
        painter.setPen(QPen(QColor(255, 80, 100, alpha), 2))
        painter.drawEllipse(QPointF(eye_x, eye_y), 18, 11)
        painter.setBrush(QBrush(QColor(255, 220, 40, alpha)))
        painter.drawEllipse(QPointF(eye_x + 3, eye_y), 5, 5)
        # 監視射線至目標
        painter.setPen(QPen(QColor(220, 50, 100, int(alpha * 0.65)), 2, Qt.DashLine))
        painter.drawLine(QPointF(eye_x, eye_y), QPointF(tx, ty))
        return True
    elif eff_name == "spear_forest":
        # 暗影長矛：地面破土而出的尖銳暗影黑矛槍林
        for i in range(5):
            px = tx - 50 + i * 25
            spear_h = int(65 * math.sin(p * math.pi) * (0.8 + (i % 3) * 0.2))
            painter.setPen(QPen(QColor(100, 40, 160, alpha), 4))
            painter.drawLine(QPointF(px, ty + 15), QPointF(px + (i - 2) * 4, ty + 15 - spear_h))
            painter.setPen(QPen(QColor(220, 160, 255, alpha), 1.5))
            painter.drawLine(QPointF(px, ty + 15), QPointF(px + (i - 2) * 4, ty + 15 - spear_h))
        return True
    elif eff_name == "reincarnation_wings":
        # 黑暗契約：死神黑翼展開與不滅神盾
        w_span = int(50 + 40 * math.sin(p * math.pi))
        for side in [-1, 1]:
            path = QPainterPath()
            path.moveTo(cx, cy - 10)
            path.cubicTo(cx + side * (w_span * 0.5), cy - 60, cx + side * w_span, cy - 30, cx + side * (w_span * 0.8), cy + 15)
            path.lineTo(cx, cy)
            painter.setBrush(QBrush(QColor(40, 10, 60, int(alpha * 0.75))))
            painter.setPen(QPen(QColor(160, 80, 255, alpha), 2))
            painter.drawPath(path)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(220, 140, 255, alpha), 3))
        painter.drawEllipse(QPointF(cx, cy - 10), 38, 38)

    # =========================================================================
    # 3. 聖騎士 (Paladin)
    # =========================================================================
        return True
    elif eff_name == "hyper_body_aura":
        # 神聖之火：深紫龍火圖騰盤旋腳底升騰
        for ri in range(3):
            r_ang = rot_angle * 0.04 + ri * (math.pi * 2 / 3)
            rx = cx + math.cos(r_ang) * (30 + 10 * math.sin(p * math.pi))
            ry = (cy + 10) + math.sin(r_ang) * 12
            painter.setBrush(QBrush(QColor(160, 80, 255, alpha)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(rx, ry), 7, 7)
        painter.setPen(QPen(QColor(200, 130, 255, int(alpha * 0.8)), 2))
        painter.drawEllipse(QPointF(cx, cy + 10), 38, 14)
        return True
    elif eff_name == "beholder_laser":
        # 魔眼衝擊：魔眼蓄力貫穿射線
        painter.setPen(QPen(QColor(140, 60, 255, int(alpha * 0.5)), 12 * (1.0 - p)))
        painter.drawLine(QPointF(cx, cy - 15), QPointF(tx, ty))
        painter.setPen(QPen(QColor(240, 200, 255, alpha), 3))
        painter.drawLine(QPointF(cx, cy - 15), QPointF(tx, ty))
        _draw_starburst(painter, tx, ty, int(15 + 20 * math.sin(p * math.pi)), QColor(255, 255, 255, alpha), QColor(160, 80, 255, alpha))
        return True
    elif eff_name == "cyclone_spear_spin":
        # 槍刺旋風：四重紫黑槍芒渦旋 + 旋風帶狀衝擊
        spin_ang = p * 12.0
        for spi in range(4):
            sang = spin_ang + spi * (math.pi / 2)
            px1 = tx + math.cos(sang) * (45 * (1.0 - p * 0.5))
            py1 = ty + math.sin(sang) * (20 * (1.0 - p * 0.5))
            painter.setPen(QPen(QColor(180, 60, 240, alpha), 3))
            painter.drawLine(QPointF(tx, ty), QPointF(px1, py1))
        # 旋風帶狀弧面（4 段 ribbon slash 模擬旋轉氣旋）
        base_deg = math.degrees(spin_ang)
        for si in range(4):
            _draw_ribbon_slash(painter, tx, ty,
                               start_deg=(base_deg + si * 90) % 360, sweep_deg=70,
                               inner_r=12, outer_r=45, color=(160, 50, 220),
                               alpha=int(alpha * 0.6), core_white=False)
        # 持續擴散衝擊環
        _draw_expanding_shockwave(painter, tx, ty, max_radius=60, p=p,
                                 color=(180, 60, 240), alpha=alpha, aspect=0.4, rings=2)

    # =========================================================================
    # 6. 聖騎士新增技能 (Paladin 6~8)
    # =========================================================================
        return True
    elif eff_name == "sanctuary_hammer":
        # 聖域：天罰金色巨鎚轟砸
        h_y = (ty - 150) + 150 * min(1.0, p * 2.2)
        painter.save()
        painter.translate(tx, h_y)
        painter.setBrush(QBrush(QColor(255, 215, 60, alpha)))
        painter.setPen(QPen(QColor(255, 255, 220, alpha), 2))
        painter.drawRoundedRect(QRect(-32, -20, 64, 30), 4, 4)
        painter.setBrush(QBrush(QColor(180, 120, 40, alpha)))
        painter.drawRect(QRect(-5, -60, 10, 40))
        painter.restore()
        if p > 0.3:
            rad = int(30 + 90 * ((p - 0.3) / 0.7))
            _draw_magic_circle(painter, tx, ty + 15, rad, rot_angle * 0.02, QColor(255, 230, 80, alpha))
        return True
    elif eff_name == "grand_cross":
        # 聖十字壁壘：全屏旋轉神聖十字聖盾
        s_size = int(35 + 45 * math.sin(p * math.pi))
        painter.save()
        painter.translate(cx, cy - 10)
        painter.rotate(rot_angle * 0.8)
        painter.setPen(QPen(QColor(255, 240, 120, alpha), 6))
        painter.drawLine(QPointF(-s_size, 0), QPointF(s_size, 0))
        painter.drawLine(QPointF(0, -s_size), QPointF(0, s_size))
        painter.setPen(QPen(QColor(255, 255, 255, alpha), 2.5))
        painter.drawLine(QPointF(-s_size, 0), QPointF(s_size, 0))
        painter.drawLine(QPointF(0, -s_size), QPointF(0, s_size))
        painter.restore()
        return True
    elif eff_name == "elemental_blast":
        # 元素衝擊：四色元素晶球旋轉爆裂
        colors_4 = [QColor(255, 60, 40), QColor(40, 180, 255), QColor(255, 220, 40), QColor(240, 240, 255)]
        rad = int(45 * (1.0 - p * 0.7))
        for i, col in enumerate(colors_4):
            ang = i * (math.pi / 2) + rot_angle * 0.06
            ox = tx + math.cos(ang) * rad
            oy = ty + math.sin(ang) * rad
            painter.setBrush(QBrush(col))
            painter.setPen(QPen(QColor(255, 255, 255, alpha), 1.5))
            painter.drawEllipse(QPointF(ox, oy), 10, 10)
        _draw_starburst(painter, tx, ty, int(22 + 35 * p), QColor(255, 255, 255, alpha), QColor(255, 200, 50, alpha))
        return True
    elif eff_name == "smite_cross":
        # 降魔十字：金色降魔十字架從天墜落鏈條鎖定禁錮
        cy_cross = (ty - 130) + 130 * min(1.0, p * 2.0)
        painter.setPen(QPen(QColor(255, 215, 60, alpha), 5))
        painter.drawLine(QPointF(tx - 24, cy_cross), QPointF(tx + 24, cy_cross))
        painter.drawLine(QPointF(tx, cy_cross - 35), QPointF(tx, cy_cross + 35))
        for ang_chain in [-0.5, 0.5, -2.5, 2.5]:
            painter.setPen(QPen(QColor(200, 170, 50, int(alpha * 0.8)), 2, Qt.DashLine))
            painter.drawLine(QPointF(tx, cy_cross), QPointF(tx + math.cos(ang_chain) * 55, ty + 10))
        return True
    elif eff_name == "divine_echo":
        # 神聖介入：聖光金色漣漪音波向四周一波波擴散
        for i in range(3):
            phase = (p * 2.0 + i * 0.33) % 1.0
            cur_r = int(15 + 85 * phase)
            cur_a = int(alpha * (1.0 - phase))
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(255, 230, 110, cur_a), 3))
            painter.drawEllipse(QPointF(cx, cy - 10), cur_r, int(cur_r * 0.45))

    # =========================================================================
    # 4. 箭神 (Bowmaster)
    # =========================================================================
        return True
    elif eff_name == "mjolnir_throw":
        # 雷神之鎚：金色飛鎚旋轉拋擲與電光四射 + 雷霆命中爆炸
        h_ang = p * 20.0
        hx = cx + (tx - cx) * min(1.0, p * 1.5)
        hy = cy + (ty - cy) * min(1.0, p * 1.5) - math.sin(p * math.pi) * 45
        painter.save()
        painter.translate(hx, hy)
        painter.rotate(h_ang * 57.3)
        painter.setBrush(QBrush(QColor(255, 215, 60, alpha)))
        painter.setPen(QPen(QColor(255, 255, 200, alpha), 2))
        painter.drawRect(-14, -8, 28, 16)
        painter.setPen(QPen(QColor(180, 140, 40, alpha), 3))
        painter.drawLine(0, 8, 0, 26)
        painter.restore()
        # 命中時雷霆爆炸
        if p > 0.6:
            imp_p = (p - 0.6) / 0.4
            _draw_expanding_shockwave(painter, tx, ty, max_radius=80, p=imp_p,
                                     color=(255, 215, 60), alpha=alpha, aspect=0.55, rings=2)
            _draw_crackling_lightning(painter, QPointF(tx, ty), QPointF(tx - 55, ty - 15),
                                      imp_p, (255, 230, 100), alpha, jitter=8.0, seed=3)
            _draw_crackling_lightning(painter, QPointF(tx, ty), QPointF(tx + 55, ty - 15),
                                      imp_p, (255, 230, 100), alpha, jitter=8.0, seed=7)
            _draw_physics_particles(painter, tx, ty, imp_p, count=12,
                                    color=(255, 200, 50), alpha=alpha, seed=66,
                                    spread_x=50.0, spread_y=35.0, gravity=55.0, upward=False)
        return True
    elif eff_name == "divine_charge_slash":
        # 神聖衝擊：金白聖劍三連重斬弧面光痕 + 命中星芒
        for di in range(3):
            d_x = tx + (di - 1) * 24
            # 每斬改用 ribbon slash 弧面（sweep_deg=70，金白色）
            _draw_ribbon_slash(painter, d_x, ty, start_deg=-100, sweep_deg=70,
                               inner_r=18, outer_r=55, color=(255, 240, 160),
                               alpha=int(alpha * (1.0 - di * 0.15)), core_white=True)
            _draw_starburst(painter, d_x, ty, int(10 + 8 * math.sin(p * math.pi)),
                            QColor(255, 255, 255, alpha), QColor(255, 220, 80, alpha))
        return True
    elif eff_name == "elemental_force_aura":
        # 元素誓約：四色聖光微粒盤旋
        elem_cols = [(255, 90, 60), (90, 200, 255), (255, 230, 80), (140, 240, 160)]
        for ei, ecol in enumerate(elem_cols):
            e_ang = rot_angle * 0.05 + ei * (math.pi / 2)
            ex = cx + math.cos(e_ang) * 36
            ey = (cy - 5) + math.sin(e_ang) * 16
            painter.setBrush(QBrush(QColor(ecol[0], ecol[1], ecol[2], alpha)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(ex, ey), 6, 6)

    # =========================================================================
    # 7. 箭神新增技能 (Bowmaster 6~8)
    # =========================================================================
        return True
    return False
