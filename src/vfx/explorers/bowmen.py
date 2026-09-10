"""
新楓之谷 冒險家 弓箭手 (箭神 / 神射手 / 開拓者) 技能特效渲染模組 (bowmen.py)
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

BOWMEN_EFFECTS = {'curse_transition_mark', 'arrow_platter_turret', 'repeater_cross', 'advanced_final_arrow', 'raven_tempest', 'ancient_guidance_aura', 'split_arrow', 'cardinal_deluge', 'bullseye_aura', 'piercing_arrow', 'quiver_cartridge_aura', 'pain_focus', 'obsidian_barrier', 'relic_unbound', 'sniper_laser', 'arrow_stream', 'freezer_ice_arrow', 'sharp_eyes', 'hurricane_barrage', 'triple_impact_blast', 'cardinal_burst', 'inhuman_speed', 'charged_arrow_blast', 'phoenix_strike'}


def render_bowmen_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty,
                       rot_angle=0.0, seed=0.0, fracture_lines=None, **kwargs) -> bool:
    if eff_name == "hurricane_barrage":
        # 暴風神射：連續高速風靈箭羽流
        for i in range(6):
            phase = (p * 3.0 + i * 0.16) % 1.0
            ax = cx + (tx - cx) * phase
            ay = cy + (ty - cy) * phase + math.sin(phase * 15 + i) * 8
            painter.setPen(QPen(QColor(80, 240, 150, alpha), 3))
            painter.drawLine(QPointF(ax - 22, ay), QPointF(ax, ay))
            painter.setPen(QPen(QColor(255, 255, 255, alpha), 1.5))
            painter.drawLine(QPointF(ax - 12, ay), QPointF(ax, ay))
        return True
    elif eff_name == "sharp_eyes":
        # 會心之眼：金色鷹眼準星透鏡聚焦
        rad = int(35 + 15 * math.sin(p * math.pi))
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 215, 60, alpha), 2.5))
        painter.drawEllipse(QPointF(tx, ty), rad, rad)
        painter.drawLine(QPointF(tx - rad - 10, ty), QPointF(tx + rad + 10, ty))
        painter.drawLine(QPointF(tx, ty - rad - 10), QPointF(tx, ty + rad + 10))
        _draw_starburst(painter, tx, ty, 16, QColor(255, 255, 255, alpha), QColor(255, 215, 0, alpha))
        return True
    elif eff_name == "arrow_stream":
        # 箭流席捲：扇形 7 道強光巨矢齊射貫穿
        for ang_idx in range(-3, 4):
            ang_rad = ang_idx * 0.12
            cur_p = min(1.0, p * 1.4)
            dist = 300 * cur_p
            ax = cx + math.cos(ang_rad) * dist
            ay = cy + math.sin(ang_rad) * dist * 0.5
            painter.setPen(QPen(QColor(60, 220, 210, alpha), 3))
            painter.drawLine(QPointF(ax - 28, ay), QPointF(ax, ay))
        return True
    elif eff_name == "inhuman_speed":
        # 殘影之矢：幽靈殘影雙重連鎖速射
        for sign in [-1, 1]:
            ax = cx + (tx - cx) * min(1.0, p * 1.5)
            ay = cy + (ty - cy) * min(1.0, p * 1.5) + sign * 18
            painter.setPen(QPen(QColor(120, 200, 255, int(alpha * 0.6)), 8))
            painter.drawLine(QPointF(cx, cy), QPointF(ax, ay))
            painter.setPen(QPen(QColor(255, 255, 255, alpha), 2))
            painter.drawLine(QPointF(ax - 30, ay), QPointF(ax, ay))
        return True
    elif eff_name == "phoenix_strike":
        # 火鳳凰：赤炎神鳥展翅俯衝 + 燃燒羽毛爆散
        ph_x = cx + (tx - cx) * min(1.0, p * 1.3)
        ph_y = (cy - 100) + (ty - (cy - 100)) * min(1.0, p * 1.3)
        painter.save()
        painter.translate(ph_x, ph_y)
        painter.rotate(25)
        # 鳳凰身體
        path = QPainterPath()
        path.moveTo(0, 0)
        path.lineTo(-45, -25)
        path.lineTo(-20, 0)
        path.lineTo(-45, 25)
        path.closeSubpath()
        painter.setBrush(QBrush(QColor(255, 80, 20, alpha)))
        painter.setPen(QPen(QColor(255, 220, 80, alpha), 2))
        painter.drawPath(path)
        # 雙翼展開
        for wing_sign in [-1, 1]:
            w_path = QPainterPath()
            w_path.moveTo(-20, 0)
            w_path.cubicTo(-10, wing_sign * 35, 15, wing_sign * 28, 0, wing_sign * 8)
            painter.setPen(QPen(QColor(255, 140, 40, int(alpha * 0.8)), 2))
            painter.setBrush(QBrush(QColor(255, 100, 20, int(alpha * 0.5))))
            painter.drawPath(w_path)
        painter.restore()
        # 燃燒羽毛粒子拖尾
        _draw_physics_particles(painter, ph_x, ph_y, p, count=14,
                                color=(255, 100, 30), alpha=alpha, seed=55,
                                spread_x=40.0, spread_y=25.0, gravity=30.0, upward=False)
        # 命中爆炸
        if p > 0.6:
            hit_p = (p - 0.6) / 0.4
            _draw_expanding_shockwave(painter, tx, ty, max_radius=75, p=hit_p,
                                     color=(255, 80, 20), alpha=alpha, aspect=0.6, rings=2)
            _draw_starburst(painter, tx, ty, int(18 + 20 * math.sin(hit_p * math.pi)),
                            QColor(255, 255, 200, alpha), QColor(255, 80, 20, alpha))
        return True
    elif eff_name == "advanced_final_arrow":
        # 進階終極攻擊：巨型熾金穿甲光矢高速貫穿
        ax = cx + (tx - cx) * min(1.0, p * 2.0)
        ay = cy + (ty - cy) * min(1.0, p * 2.0)
        painter.setPen(QPen(QColor(120, 255, 180, alpha), 3.5))
        painter.drawLine(QPointF(ax - 35, ay), QPointF(ax, ay))
        _draw_starburst(painter, ax, ay, 16, QColor(255, 255, 255, alpha), QColor(100, 240, 160, alpha))
        return True
    elif eff_name == "quiver_cartridge_aura":
        # 魔幻箭筒：身後三枚特殊箭羽浮空發光
        for qi in range(3):
            qx = cx - 25 + qi * 25
            qy = (cy - 35) + math.sin(p * 6.0 + qi * 2.0) * 8
            painter.setPen(QPen(QColor(255, 180, 80, alpha), 2))
            painter.drawLine(QPointF(qx, qy), QPointF(qx, qy - 20))
            painter.setBrush(QBrush(QColor(255, 220, 100, alpha)))
            painter.drawEllipse(QPointF(qx, qy - 22), 3, 3)
        return True
    elif eff_name == "arrow_platter_turret":
        # 狂暴箭雨：固定箭座噴湧暴風箭雨
        for fi in range(4):
            fx = cx + 25 + fi * 15
            fy = (cy - 10) - fi * 5
            painter.setPen(QPen(QColor(140, 240, 170, int(alpha * 0.8)), 2))
            painter.drawLine(QPointF(fx, fy), QPointF(tx, ty - 15 + fi * 8))

    # =========================================================================
    # 8. 神射手新增技能 (Marksman 6~8)
    # =========================================================================
        return True
    elif eff_name == "sniper_laser":
        # 必殺狙擊：紅色瞄準線瞬間激射超強白亮激光
        painter.setPen(QPen(QColor(255, 50, 50, int(alpha * 0.4)), 1, Qt.DashLine))
        painter.drawLine(QPointF(cx, cy), QPointF(tx, ty))
        if p > 0.15:
            beam_p = (p - 0.15) / 0.85
            beam_w = max(2, int(18 * (1.0 - beam_p)))
            painter.setPen(QPen(QColor(255, 255, 255, alpha), beam_w))
            painter.drawLine(QPointF(cx, cy), QPointF(tx, ty))
            _draw_starburst(painter, tx, ty, int(18 + 45 * (1.0 - beam_p)), QColor(255, 255, 255, alpha), QColor(255, 60, 60, alpha))
        return True
    elif eff_name == "split_arrow":
        # 分裂之箭：中心擊中後向八方以 45° 散射出 8 枚碎裂小箭
        if p < 0.4:
            arr_x = cx + (tx - cx) * (p / 0.4)
            arr_y = cy + (ty - cy) * (p / 0.4)
            painter.setPen(QPen(QColor(100, 200, 255, alpha), 4))
            painter.drawLine(QPointF(arr_x - 20, arr_y), QPointF(arr_x, arr_y))
        else:
            split_p = (p - 0.4) / 0.6
            for i in range(8):
                ang = i * (math.pi / 4)
                dist = 20 + 80 * split_p
                sx = tx + math.cos(ang) * dist
                sy = ty + math.sin(ang) * dist
                painter.setPen(QPen(QColor(80, 180, 255, int(alpha * (1.0 - split_p * 0.5))), 2))
                painter.drawLine(QPointF(sx - math.cos(ang) * 12, sy - math.sin(ang) * 12), QPointF(sx, sy))
        return True
    elif eff_name == "piercing_arrow":
        # 穿越箭：藍白高能超長穿甲光矢
        arr_x = cx + (tx - cx) * min(1.0, p * 1.5)
        painter.setPen(QPen(QColor(60, 160, 255, int(alpha * 0.7)), 8))
        painter.drawLine(QPointF(arr_x - 60, ty), QPointF(arr_x, ty))
        painter.setPen(QPen(QColor(255, 255, 255, alpha), 3))
        painter.drawLine(QPointF(arr_x - 45, ty), QPointF(arr_x + 10, ty))
        return True
    elif eff_name == "pain_focus":
        # 痛擊：弱點標記與幾何暗紅破片
        for i in range(6):
            ang = i * (math.pi / 3) + seed
            dist = 15 + 45 * p
            painter.setPen(QPen(QColor(255, 60, 60, alpha), 2))
            painter.drawLine(QPointF(tx, ty), QPointF(tx + math.cos(ang) * dist, ty + math.sin(ang) * dist))
        return True
    elif eff_name == "repeater_cross":
        # 巨弩衝擊：雙重重裝十字弩矢交錯射擊 + 命中冰爆
        for offset in [-12, 12]:
            cur_x = cx + (tx - cx) * min(1.0, p * 1.4)
            _draw_bloom_line(painter, (cx, cy + offset), (cur_x, ty + offset),
                             base_width=5, color=(100, 200, 255), alpha=alpha, core_white=True)
        # 命中冰霜爆炸
        if p > 0.5:
            hit_p = (p - 0.5) / 0.5
            _draw_expanding_shockwave(painter, tx, ty, max_radius=65, p=hit_p,
                                     color=(100, 200, 255), alpha=alpha, aspect=0.5, rings=2)
            _draw_physics_particles(painter, tx, ty, hit_p, count=10,
                                    color=(180, 230, 255), alpha=alpha, seed=22,
                                    spread_x=45.0, spread_y=30.0, gravity=40.0, upward=False)
        return True
    elif eff_name == "charged_arrow_blast":
        # 蓄力一擊：超粗高能脈衝巨型電光箭
        beam_w = int(14 * math.sin(p * math.pi))
        painter.setPen(QPen(QColor(255, 160, 50, int(alpha * 0.5)), beam_w + 8))
        painter.drawLine(QPointF(cx, cy - 15), QPointF(tx, ty))
        painter.setPen(QPen(QColor(255, 255, 230, alpha), max(2, beam_w)))
        painter.drawLine(QPointF(cx, cy - 15), QPointF(tx, ty))
        return True
    elif eff_name == "bullseye_aura":
        # 精準瞄準：巨型紅色紅外十字準星鎖定怪物中心
        painter.save()
        painter.translate(tx, ty)
        painter.setPen(QPen(QColor(255, 80, 80, alpha), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, 0), 28, 28)
        painter.drawLine(-38, 0, 38, 0)
        painter.drawLine(0, -38, 0, 38)
        painter.restore()
        return True
    elif eff_name == "freezer_ice_arrow":
        # 極凍之箭：極地冰鳥破空呼嘯凍結 + 冰晶展翅
        ix = cx + (tx - cx) * min(1.0, p * 1.8)
        iy = cy + (ty - cy) * min(1.0, p * 1.8)
        # 冰藍箭矢主體
        painter.setPen(QPen(QColor(140, 230, 255, alpha), 4))
        painter.drawLine(QPointF(ix - 25, iy), QPointF(ix, iy))
        # 翅翼展開 (mini ice wings)
        for wing_sign in [-1, 1]:
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(200, 240, 255, int(alpha * 0.7)), 2))
            painter.drawArc(QRect(int(ix - 22), int(iy - 14), 20, 28), -wing_sign * 45 * 16, wing_sign * 120 * 16)
        _draw_starburst(painter, tx, ty, int(22 * math.sin(p * math.pi)),
                        QColor(255, 255, 255, alpha), QColor(120, 220, 255, alpha))
        # 命中冰爆
        if p > 0.6:
            hit_p = (p - 0.6) / 0.4
            _draw_expanding_shockwave(painter, tx, ty, max_radius=60, p=hit_p,
                                     color=(120, 210, 255), alpha=alpha, aspect=0.55, rings=2)
            _draw_physics_particles(painter, tx, ty, hit_p, count=12,
                                    color=(180, 240, 255), alpha=alpha, seed=33,
                                    spread_x=45.0, spread_y=30.0, gravity=40.0, upward=False)
        return True
    elif eff_name == "cardinal_burst":
        # 主要射擊：赤紅古代方塊能量爆裂箭
        cur_x = cx + (tx - cx) * min(1.0, p * 1.4)
        painter.save()
        painter.translate(cur_x, ty)
        painter.rotate(rot_angle * 0.5)
        painter.setBrush(QBrush(QColor(255, 50, 80, alpha)))
        painter.setPen(QPen(QColor(255, 220, 220, alpha), 1.5))
        painter.drawRect(QRect(-12, -12, 24, 24))
        painter.restore()
        if p > 0.4:
            rg = QRadialGradient(tx, ty, 45)
            rg.setColorAt(0.0, QColor(255, 100, 120, int(alpha * 0.8)))
            rg.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(rg))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(tx, ty), 45, 45)
        return True
    elif eff_name == "cardinal_deluge":
        # 狂風分裂：青藍尋敵激流箭羽
        for i in range(4):
            ctrl_y = cy - 40 + i * 25
            curve_p = min(1.0, (p * 1.3 + i * 0.1))
            u = 1.0 - curve_p
            bx = (u**2) * cx + 2 * u * curve_p * (cx + (tx - cx) * 0.5) + (curve_p**2) * tx
            by = (u**2) * cy + 2 * u * curve_p * ctrl_y + (curve_p**2) * ty
            painter.setPen(QPen(QColor(40, 180, 255, alpha), 3))
            painter.drawPoint(QPointF(bx, by))
            painter.drawLine(QPointF(bx - 12, by), QPointF(bx, by))
        return True
    elif eff_name == "relic_unbound":
        # 遺物解放：三色方尖碑古代神光光柱
        colors_3 = [QColor(255, 60, 80), QColor(60, 180, 255), QColor(160, 80, 255)]
        for i, col in enumerate(colors_3):
            ox = tx - 35 + i * 35
            b_w = int(24 * math.sin(p * math.pi))
            painter.fillRect(QRect(ox - b_w // 2, 0, b_w, int(ty + 20)), QColor(col.red(), col.green(), col.blue(), int(alpha * 0.75)))
        return True
    elif eff_name == "raven_tempest":
        # 渡鴉風暴：暗夜渡鴉盤旋與暗紫旋風
        for i in range(4):
            ang = i * (math.pi / 2) + rot_angle * 0.05
            rx = tx + math.cos(ang) * 45
            ry = ty + math.sin(ang) * 22
            _draw_shuriken(painter, rx, ry, ang * 57.3, 14, QColor(140, 50, 220, alpha))
        return True
    elif eff_name == "obsidian_barrier":
        # 黑曜石屏障：懸浮菱形水晶防禦結界
        painter.save()
        painter.translate(cx, cy - 10)
        painter.setBrush(QBrush(QColor(40, 20, 60, int(alpha * 0.7))))
        painter.setPen(QPen(QColor(180, 80, 255, alpha), 2))
        poly = QPolygonF([QPointF(0, -35), QPointF(25, 0), QPointF(0, 35), QPointF(-25, 0)])
        painter.drawPolygon(poly)
        painter.restore()

    # =========================================================================
    # 7. 火毒大魔導士 (Fire/Poison)
    # =========================================================================
        return True
    elif eff_name == "triple_impact_blast":
        # 三重衝擊：三大古代紫黑光球連環俯衝
        for ti in range(3):
            t_prog = min(1.0, max(0.0, p * 1.5 - ti * 0.15))
            b_x = cx + (tx - cx) * t_prog + (ti - 1) * 20
            b_y = (cy - 60) + (ty - (cy - 60)) * t_prog
            painter.setBrush(QBrush(QColor(190, 80, 255, alpha)))
            painter.setPen(QPen(QColor(255, 200, 255, alpha), 1.5))
            painter.drawEllipse(QPointF(b_x, b_y), 9, 9)
        return True
    elif eff_name == "ancient_guidance_aura":
        # 古代導引：三色古代遺物浮石 + 旋轉法陣
        colors_3 = [QColor(255, 80, 100, alpha), QColor(80, 180, 255, alpha), QColor(160, 80, 255, alpha)]
        for ai in range(3):
            a_ang = rot_angle * 0.03 + ai * (math.pi * 2 / 3)
            ax = cx + math.cos(a_ang) * 32
            ay = (cy - 30) + math.sin(a_ang) * 14
            # 菱形遺物寶石
            painter.save()
            painter.translate(ax, ay)
            painter.rotate(rot_angle * 1.2 + ai * 30)
            poly = QPolygonF([QPointF(0, -7), QPointF(5, 0), QPointF(0, 7), QPointF(-5, 0)])
            painter.setBrush(QBrush(colors_3[ai]))
            painter.setPen(QPen(QColor(255, 255, 255, int(alpha * 0.7)), 1))
            painter.drawPolygon(poly)
            painter.restore()
        # 古代符文陣
        _draw_magic_circle(painter, cx, cy + 8, int(25 + 5 * math.sin(p * math.pi)),
                           rot_angle * 0.03, QColor(200, 100, 255, int(alpha * 0.65)))
        return True
    elif eff_name == "curse_transition_mark":
        # 詛咒轉移：紫色詛咒電弧鎖鏈束縛 + 印記
        painter.setPen(QPen(QColor(140, 60, 220, alpha), 2.5, Qt.DashLine))
        painter.drawEllipse(QPointF(tx, ty), 32, 16)
        painter.drawEllipse(QPointF(tx, ty), 22, 28)
        # 詛咒電弧（角色到目標）
        _draw_crackling_lightning(painter, QPointF(cx, cy), QPointF(tx, ty),
                                  p, (160, 80, 255), int(alpha * 0.8), jitter=10.0, seed=11)
        # 目標詛咒印記閃光
        _draw_starburst(painter, tx, ty, int(12 + 10 * math.sin(p * math.pi)),
                        QColor(220, 160, 255, alpha), QColor(140, 50, 220, alpha))
        return True
    return False
