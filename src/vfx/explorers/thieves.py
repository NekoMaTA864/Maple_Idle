"""
新楓之谷 冒險家 盜賊 (夜使者 / 暗影神偷 / 影武者) 技能特效渲染模組 (thieves.py)
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

THIEVES_EFFECTS = {'assassinate_slash', 'phantom_blow', 'shadow_stars', 'spread_throw', 'blade_storm', 'shadow_assault', 'meso_guard_aura', 'fuma_shuriken', 'showdown_talisman', 'shadow_partner', 'dark_serenity_aura', 'final_cut', 'asura_tempest', 'haunted_edge_slashes', 'smoke_screen', 'savage_blow_six', 'meso_explosion', 'blade_fury', 'boomerang_step', 'assassin_mark_burst', 'karma_blade_aura', 'five_star_barrage', 'blade_tornado_spin', 'trickblade_strike'}


def render_thieves_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty,
                       rot_angle=0.0, seed=0.0, fracture_lines=None, **kwargs) -> bool:
    if eff_name == "shadow_stars":
        # 四連飛鏢：4 枚高速自轉金色四角手裏劍
        for i in range(4):
            phase = min(1.0, (p * 1.5 + i * 0.12))
            sx = cx + (tx - cx) * phase
            sy = cy + (ty - cy) * phase + (i - 1.5) * 12
            _draw_shuriken(painter, sx, sy, rot_angle * 1.5 + i * 45, 12, QColor(255, 215, 60, alpha), core_white=True)
        return True
    elif eff_name == "fuma_shuriken":
        # 風魔手裏劍：巨型八角風魔手裏劍殘影狂轉
        cur_x = cx + (tx - cx) * min(1.0, p * 1.2)
        _draw_shuriken(painter, cur_x, ty, rot_angle * 2.0, 36, QColor(r, g, b, alpha), core_white=True)
        return True
    elif eff_name == "shadow_partner":
        # 達克魯之影：暗影分身 + 紫色粗糲輪廓上飄
        s_off = int(math.sin(p * 6.0) * 5)
        painter.setBrush(QBrush(QColor(30, 0, 50, int(alpha * 0.75))))
        painter.setPen(QPen(QColor(160, 80, 255, alpha), 2.5))
        painter.drawEllipse(QPointF(cx + 30 + s_off, cy - 42), 9, 9)
        body_path = QPainterPath()
        body_path.moveTo(cx + 30 + s_off - 12, cy - 33)
        body_path.cubicTo(cx + 30 + s_off - 16, cy - 10, cx + 30 + s_off + 16, cy - 10, cx + 30 + s_off + 12, cy - 33)
        body_path.closeSubpath()
        painter.drawPath(body_path)
        _draw_physics_particles(painter, cx + 30 + s_off, cy - 20, p, count=8,
                                color=(140, 60, 220), alpha=alpha, seed=13,
                                spread_x=18.0, spread_y=30.0, gravity=10.0, upward=True)
        return True
    elif eff_name == "showdown_talisman":
        # 穢土轉生：撒出巨大招財封印靈符
        t_y = (ty - 100) + 100 * min(1.0, p * 2.0)
        painter.save()
        painter.translate(tx, t_y)
        painter.setBrush(QBrush(QColor(255, 215, 80, alpha)))
        painter.setPen(QPen(QColor(200, 40, 40, alpha), 2))
        painter.drawRect(QRect(-14, -25, 28, 50))
        painter.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        painter.setPen(QColor(200, 40, 40))
        painter.drawText(QRect(-14, -25, 28, 50), Qt.AlignCenter, "封")
        painter.restore()
        return True
    elif eff_name == "spread_throw":
        # 投擲擴散：前方扇形散射數十枚星鏢矩陣
        for ang_idx in range(-4, 5):
            ang = ang_idx * 0.10
            dist = 220 * min(1.0, p * 1.4)
            sx = cx + math.cos(ang) * dist
            sy = cy + math.sin(ang) * dist * 0.6
            _draw_shuriken(painter, sx, sy, rot_angle, 8, QColor(255, 215, 60, alpha))

    # =========================================================================
    # 11. 暗影神偷 (Shadower)
    # =========================================================================
        return True
    elif eff_name == "dark_serenity_aura":
        # 達克魯之影：黑紫色暗夜煙幕繚繞
        for di in range(5):
            dx = cx + math.sin(p * 5.0 + di * 1.5) * 28
            dy = cy - di * 10
            painter.setBrush(QBrush(QColor(160, 90, 255, int(alpha * 0.5))))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(dx, dy), 12, 12)
        return True
    elif eff_name == "assassin_mark_burst":
        # 夜使標記：赤紅刺客蝙蝠印記在敵人身上爆散
        painter.setPen(QPen(QColor(255, 60, 60, alpha), 3))
        painter.drawLine(QPointF(tx - 25, ty - 25), QPointF(tx + 25, ty + 25))
        painter.drawLine(QPointF(tx + 25, ty - 25), QPointF(tx - 25, ty + 25))
        _draw_starburst(painter, tx, ty, 20, QColor(255, 200, 200, alpha), QColor(255, 40, 40, alpha))
        return True
    elif eff_name == "five_star_barrage":
        # 五星投擲：五角陣列疾速暗夜金標轟擊
        for si in range(5):
            sang = si * (math.pi * 2 / 5) + p * 8.0
            sx = tx + math.cos(sang) * (40 * (1.0 - p))
            sy = ty + math.sin(sang) * (20 * (1.0 - p))
            _draw_shuriken(painter, sx, sy, sang * 57.3, 11, QColor(180, 110, 255, alpha), True)

    # =========================================================================
    # 14. 暗影神偷新增技能 (Shadower 6~8)
    # =========================================================================
        return True
    elif eff_name == "assassinate_slash":
        # 致命暗殺：暗影飆刺突進 + X型展開血斬 + 物理碎片
        if p < 0.5:
            rush_p = p / 0.5
            _draw_bloom_line(painter, (cx, cy), (cx + (tx - cx) * rush_p, cy + (ty - cy) * rush_p),
                             base_width=5, color=(130, 30, 200), alpha=int(alpha * 0.7), core_white=False)
        for sign in [-1, 1]:
            painter.save()
            painter.translate(tx, ty)
            painter.rotate(sign * 35)
            painter.setPen(QPen(QColor(220, 30, 50, alpha), 6))
            painter.drawLine(QPointF(-40, 0), QPointF(40, 0))
            painter.setPen(QPen(QColor(255, 255, 255, alpha), 2))
            painter.drawLine(QPointF(-35, 0), QPointF(35, 0))
            painter.restore()
        if p > 0.4:
            cross_p = (p - 0.4) / 0.6
            _draw_ribbon_slash(painter, tx, ty, start_deg=-145, sweep_deg=110,
                               inner_r=15, outer_r=55, color=(220, 30, 50),
                               alpha=int(alpha * cross_p), core_white=False)
            _draw_ribbon_slash(painter, tx, ty, start_deg=35, sweep_deg=110,
                               inner_r=15, outer_r=55, color=(180, 20, 40),
                               alpha=int(alpha * cross_p * 0.8), core_white=False)
            _draw_physics_particles(painter, tx, ty, cross_p, count=14,
                                    color=(220, 30, 50), alpha=alpha, seed=77,
                                    spread_x=50.0, spread_y=35.0, gravity=55.0, upward=False)
        _draw_starburst(painter, tx, ty, int(15 + 25 * p), QColor(255, 255, 255, alpha), QColor(220, 20, 20, alpha))
        return True
    elif eff_name == "meso_explosion":
        # 楓幣炸彈：地面散落金幣連鎖劇烈爆破 + 爆炸震波
        for i in range(10):
            ang = i * (math.pi * 2 / 10) + seed
            dist = 15 + 60 * p
            bx = tx + math.cos(ang) * dist
            by = ty + math.sin(ang) * (dist * 0.5)
            painter.setBrush(QBrush(QColor(255, 215, 0, alpha)))
            painter.setPen(QPen(QColor(255, 255, 255, alpha), 1))
            painter.drawEllipse(QPointF(bx, by), 5, 5)
            if i % 3 == 0:
                _draw_starburst(painter, bx, by, int(5 + 6 * math.sin(p * math.pi)),
                                QColor(255, 255, 200, int(alpha * 0.8)), QColor(255, 180, 20, int(alpha * 0.8)))
        _draw_expanding_shockwave(painter, tx, ty, max_radius=80, p=p,
                                 color=(255, 200, 30), alpha=alpha, aspect=0.55, rings=2)
        return True
    elif eff_name == "smoke_screen":
        # 煙霧彈：灰色戰術煙霧結界
        for i in range(7):
            ang = i * (math.pi * 2 / 7) + seed
            dist = 12 + 45 * p
            painter.setBrush(QBrush(QColor(80, 90, 110, int(alpha * 0.5))))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(tx + math.cos(ang) * dist, ty + math.sin(ang) * dist * 0.6), 24, 18)
        return True
    elif eff_name == "shadow_assault":
        # 暗影瞬步：三道折線突刺殘影破空
        pts = [(cx, cy), (cx + (tx-cx)*0.4, cy - 35), (cx + (tx-cx)*0.8, cy + 30), (tx, ty)]
        painter.setPen(QPen(QColor(180, 50, 255, alpha), 4))
        for i in range(len(pts) - 1):
            painter.drawLine(QPointF(pts[i][0], pts[i][1]), QPointF(pts[i+1][0], pts[i+1][1]))
        return True
    elif eff_name == "boomerang_step":
        # 迴旋斬：金色雙刃氣刃向前呼嘯飛出
        cur_x = cx + (tx - cx) * min(1.0, p * 1.5)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 200, 50, alpha), 4))
        painter.drawArc(QRect(int(cur_x - 25), int(ty - 25), 50, 50), 30 * 16, 120 * 16)

    # =========================================================================
    # 12. 影武者 (Dual Blade)
    # =========================================================================
        return True
    elif eff_name == "trickblade_strike":
        # 切連斬：兩道暗紅殘影瞬殺交錯
        painter.setPen(QPen(QColor(255, 70, 70, alpha), 4))
        painter.drawLine(QPointF(tx - 40, ty + 20), QPointF(tx + 40, ty - 20))
        painter.drawLine(QPointF(tx - 35, ty - 25), QPointF(tx + 35, ty + 25))
        return True
    elif eff_name == "meso_guard_aura":
        # 楓幣護盾：金幣圍繞角色高速旋轉形成金色護罩
        for mi in range(6):
            mang = rot_angle * 0.06 + mi * (math.pi / 3)
            mx = cx + math.cos(mang) * 34
            my = cy + math.sin(mang) * 16
            painter.setBrush(QBrush(QColor(255, 215, 0, alpha)))
            painter.setPen(QPen(QColor(255, 255, 200, alpha), 1))
            painter.drawEllipse(QPointF(mx, my), 5, 5)
        return True
    elif eff_name == "savage_blow_six":
        # 六連斬：六道血色匯光匕首斬痕連環切割
        for si in range(6):
            delay = si * 0.08
            cur_p = max(0.0, min(1.0, (p - delay) / 0.5))
            if cur_p > 0:
                sx = tx + (si - 2.5) * 12
                sy = ty + math.sin(si * 1.8) * 15
                _draw_bloom_line(painter, (sx - 14, sy - 18), (sx + 14, sy + 18),
                                 base_width=4, color=(240, 60, 80), alpha=int(alpha * (1.0 - si * 0.08)), core_white=True)
        if p > 0.7:
            _draw_starburst(painter, tx, ty, int(12 + 12 * math.sin((p - 0.7) / 0.3 * math.pi)),
                            QColor(255, 255, 255, alpha), QColor(255, 60, 80, alpha))
        return True

    # =========================================================================
    # 15. 影武者新增技能 (Dual Blade 6~8)
    # =========================================================================
        return True
    elif eff_name == "phantom_blow":
        # 幽靈一擊：極速前刺雙刀刀幕 + 光爆段段命中閃光
        for i in range(5):
            delay = i * 0.07
            cur_p = max(0.0, min(1.0, (p - delay) / 0.6))
            if cur_p > 0:
                ang_off = (-12 + i * 6) * math.pi / 180.0
                end_x = tx + math.cos(ang_off) * 45
                end_y = ty + math.sin(ang_off) * 20
                col = (240, 240, 255) if i % 2 == 0 else (220, 80, 120)
                _draw_bloom_line(painter, (tx - 40, ty + math.sin(ang_off) * 20), (end_x, end_y),
                                 base_width=4, color=col, alpha=int(alpha * (1.0 - delay)), core_white=True)
        painter.setOpacity(0.3)
        for i in range(3):
            sx = tx + (i - 1) * 8
            painter.setPen(QPen(QColor(200, 150, 255, int(alpha * 0.3)), 3))
            painter.drawLine(QPointF(sx - 40, ty - 10), QPointF(sx + 15, ty + 10))
        painter.setOpacity(1.0)
        if p > 0.75:
            _draw_starburst(painter, tx, ty, int(16 + 14 * math.sin((p - 0.75) / 0.25 * math.pi)),
                            QColor(255, 255, 255, alpha), QColor(220, 80, 120, alpha))
        return True
    elif eff_name == "asura_tempest":
        # 阿修羅：血紅雙刀龍捲風暴
        rad = int(35 + 20 * math.sin(p * math.pi))
        painter.save()
        painter.translate(tx, ty)
        painter.rotate(rot_angle * 1.5)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 40, 60, alpha), 4))
        painter.drawEllipse(QPointF(0, 0), rad, int(rad * 0.4))
        painter.setPen(QPen(QColor(255, 220, 220, alpha), 2))
        painter.drawEllipse(QPointF(0, 0), rad - 8, int((rad - 8) * 0.4))
        painter.restore()
        return True
    elif eff_name == "blade_fury":
        # 暴風之刃：360度紅色刀光圓環裂地
        rad = int(30 + 65 * p)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 60, 80, alpha), max(1, int(5 * (1.0 - p)))))
        painter.drawEllipse(QPointF(tx, ty + 10), rad, int(rad * 0.4))
        return True
    elif eff_name == "final_cut":
        # 閃靈交叉：蓄力前衝撕裂地表留下血線 + 剪刀斬弧面
        _draw_bloom_line(painter, (cx, cy), (tx, ty),
                         base_width=6, color=(180, 20, 40), alpha=int(alpha * 0.6), core_white=False)
        _draw_ribbon_slash(painter, tx, ty, start_deg=-135, sweep_deg=90,
                           inner_r=14, outer_r=55, color=(220, 30, 50),
                           alpha=alpha, core_white=True)
        _draw_ribbon_slash(painter, tx, ty, start_deg=45, sweep_deg=90,
                           inner_r=14, outer_r=55, color=(200, 20, 40),
                           alpha=int(alpha * 0.75), core_white=False)
        _draw_physics_particles(painter, tx, ty, p, count=10,
                                color=(220, 30, 50), alpha=alpha, seed=55,
                                spread_x=40.0, spread_y=28.0, gravity=50.0, upward=False)
        _draw_starburst(painter, tx, ty, int(14 + 16 * math.sin(p * math.pi)),
                        QColor(255, 255, 255, alpha), QColor(220, 30, 50, alpha))
        return True
    elif eff_name == "blade_storm":
        # 終極雙刀：漫天交錯白色與血色刀氣
        for i in range(8):
            ang = (-45 + (i % 3) * 45) * (math.pi / 180)
            sx = tx - 25 + (i * 12)
            painter.setPen(QPen(QColor(255, 60 + i * 20, 60, alpha), 3))
            painter.drawLine(QPointF(sx - 20, ty - 15), QPointF(sx + 20, ty + 15))

    # =========================================================================
    # 13. 拳霸 (Buccaneer)
    # =========================================================================
        return True
    elif eff_name == "blade_tornado_spin":
        # 利刃旋風：雙刀血刃旋風狂暴擴散
        t_rad = int(25 + 65 * p)
        painter.setPen(QPen(QColor(255, 50, 40, alpha), 3.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(tx, ty), t_rad, int(t_rad * 0.4))
        painter.drawEllipse(QPointF(tx, ty), int(t_rad * 0.7), int(t_rad * 0.28))
        return True
    elif eff_name == "haunted_edge_slashes":
        # 業火殘影：修羅怨火雙重十字暴擊
        painter.setPen(QPen(QColor(240, 40, 60, alpha), 5))
        painter.drawLine(QPointF(tx - 35, ty), QPointF(tx + 35, ty))
        painter.drawLine(QPointF(tx, ty - 35), QPointF(tx, ty + 35))
        _draw_starburst(painter, tx, ty, 22, QColor(255, 255, 255, alpha), QColor(255, 60, 80, alpha))
        return True
    elif eff_name == "karma_blade_aura":
        # 死靈附體：背後浮現暗紅修羅怒目鬼面
        painter.setPen(QPen(QColor(255, 60, 60, alpha), 2.5))
        painter.drawArc(QRect(int(cx - 24), int(cy - 48), 48, 48), 30 * 16, 120 * 16)
        painter.setBrush(QBrush(QColor(255, 215, 60, alpha)))
        painter.drawEllipse(QPointF(cx - 10, cy - 35), 4, 4)
        painter.drawEllipse(QPointF(cx + 10, cy - 35), 4, 4)

    # =========================================================================
    # 16. 拳霸新增技能 (Buccaneer 6~8)
    # =========================================================================
        return True
    return False
