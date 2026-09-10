"""
新楓之谷 皇家騎士團 - 聖魂劍士 (Dawn Warrior) 技能特效模組
"""

import math
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QRadialGradient
)
from vfx_core import (
    _draw_starburst, _draw_magic_circle, _draw_bloom_line,
    _draw_ribbon_slash, _draw_expanding_shockwave, _draw_physics_particles
)

DAWN_WARRIOR_EFFECTS = {
    "soluna_slash", "eclipse_blast", "solar_slash", "styx_crossing",
    "cosmos_stars", "flaring_sun_cleave", "soluna_time_aura", "soul_penetrate_thrust"
}


def render_dawn_warrior_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty,
                            rot_angle=0.0, seed=0.0, fracture_lines=None, **kwargs) -> bool:
    if eff_name == "cosmos_stars":
        # 【宇宙之雨】：召喚群星宇宙之輝！多重星軌彗星神珠公轉拖尾 + 天降流星核融光柱 + 24 顆宇宙星辰微粒
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        _draw_magic_circle(painter, cx, cy + 12, int(32 + 8 * math.sin(p * math.pi)), rot_angle * 0.05, QColor(140, 180, 255, alpha))

        orbs_data = [
            (QColor(255, 220, 90, alpha), 48, 22, 0.0),
            (QColor(120, 210, 255, alpha), 38, 16, math.pi * 0.66),
            (QColor(220, 140, 255, alpha), 56, 26, math.pi * 1.33),
        ]
        for col, rx, ry, off in orbs_data:
            ang = rot_angle * 0.08 + off
            ox = tx + math.cos(ang) * rx
            oy = ty + math.sin(ang) * ry
            _draw_starburst(painter, ox, oy, 10, QColor(255, 255, 255, alpha), col)
            deg = math.degrees(ang)
            _draw_ribbon_slash(painter, tx, ty, start_deg=deg - 55, sweep_deg=55,
                               inner_r=rx - 5, outer_r=rx + 5, color=col, alpha=int(alpha * 0.65), core_white=False)

        if p > 0.35:
            for mi in range(4):
                mx = tx - 40 + mi * 26
                my_end = ty + 10
                _draw_bloom_line(painter, (mx - 15, my_end - 80), (mx, my_end), base_width=5,
                                 color=(255, 230, 130), alpha=alpha, core_white=True)

        _draw_expanding_shockwave(painter, tx, ty, max_radius=85, p=p,
                                 color=(180, 210, 255), alpha=alpha, aspect=0.65, rings=2)
        _draw_physics_particles(painter, tx, ty, p, count=24,
                                color=(240, 230, 180), alpha=alpha, seed=444,
                                spread_x=75.0, spread_y=60.0, gravity=30.0, upward=False)
        return True

    elif eff_name == "eclipse_blast":
        # 【日蝕】：全屏日蝕黑洞降臨！引力坍縮黑曜暗核 + 雙層白熾高熱太陽日冕環 + 空間十字撕裂 + 28 顆高能日炎微粒
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        rad = int(35 + 75 * math.sin(p * math.pi))

        deg_e = rot_angle * 0.08
        _draw_ribbon_slash(painter, tx, ty, start_deg=deg_e, sweep_deg=175,
                           inner_r=rad - 6, outer_r=rad + 18, color=(255, 140, 40), alpha=alpha, core_white=True)
        _draw_ribbon_slash(painter, tx, ty, start_deg=deg_e + 180, sweep_deg=175,
                           inner_r=rad - 6, outer_r=rad + 18, color=(255, 100, 30), alpha=alpha, core_white=True)

        rg = QRadialGradient(tx, ty, rad)
        rg.setColorAt(0.0, QColor(15, 8, 25, int(alpha * 0.95)))
        rg.setColorAt(0.65, QColor(255, 120, 30, int(alpha * 0.85)))
        rg.setColorAt(0.9, QColor(255, 230, 100, int(alpha * 0.6)))
        rg.setColorAt(1.0, QColor(255, 80, 20, 0))
        painter.setBrush(QBrush(rg))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(tx, ty), rad, rad)

        _draw_bloom_line(painter, (tx - rad * 1.3, ty), (tx + rad * 1.3, ty), base_width=5,
                         color=(255, 220, 110), alpha=alpha, core_white=True)
        _draw_bloom_line(painter, (tx, ty - rad * 1.3), (tx, ty + rad * 1.3), base_width=5,
                         color=(255, 220, 110), alpha=alpha, core_white=True)

        _draw_expanding_shockwave(painter, tx, ty, max_radius=120, p=p,
                                 color=(255, 150, 40), alpha=alpha, aspect=0.75, rings=2)
        _draw_physics_particles(painter, tx, ty, p, count=28,
                                color=(255, 190, 60), alpha=alpha, seed=888,
                                spread_x=90.0, spread_y=70.0, gravity=50.0, upward=False)
        _draw_starburst(painter, tx, ty, int(30 + 35 * math.sin(p * math.pi)),
                        QColor(255, 255, 240, alpha), QColor(255, 120, 30, alpha))
        return True

    elif eff_name == "flaring_sun_cleave":
        # 【烈日斬】：凝聚耀眼旭日狂焰垂直重劈！150° 厚實熾金赤焰帶狀流光 + 裂地熔岩地痕 + 雙層日炎衝擊巨環 + 22 顆太陽火花
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        _draw_ribbon_slash(painter, tx, ty, start_deg=-165, sweep_deg=150,
                           inner_r=25, outer_r=82, color=(255, 110, 30), alpha=alpha, core_white=True)

        _draw_bloom_line(painter, (tx, ty - 65), (tx, ty + 50), base_width=8,
                         color=(255, 170, 40), alpha=alpha, core_white=True)

        _draw_expanding_shockwave(painter, tx, ty + 10, max_radius=85, p=p,
                                 color=(255, 140, 30), alpha=alpha, aspect=0.55, rings=2)

        _draw_physics_particles(painter, tx, ty + 10, p, count=22,
                                color=(255, 200, 60), alpha=alpha, seed=777,
                                spread_x=80.0, spread_y=60.0, gravity=80.0, upward=False)
        _draw_starburst(painter, tx, ty, int(24 + 28 * math.sin(p * math.pi)),
                        QColor(255, 255, 240, alpha), QColor(255, 100, 20, alpha))
        return True

    elif eff_name == "solar_slash":
        # 【極月舞蹈】：極月霜藍 3 段迴旋月牙舞斬！3 重交錯霜藍帶狀流光 + 核融霜白十字 + 衝擊波紋 + 20 顆碎月星屑
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        slash_angles = [(-110, 130), (30, 130), (-40, 130)]
        for idx, (start_a, swp) in enumerate(slash_angles):
            deg_s = start_a + p * 40
            c_blue = (120 + idx * 25, 200 + idx * 20, 255)
            _draw_ribbon_slash(painter, tx, ty, start_deg=deg_s, sweep_deg=swp,
                               inner_r=25 + idx * 6, outer_r=68 + idx * 8, color=c_blue, alpha=alpha, core_white=True)

        _draw_bloom_line(painter, (tx - 35, ty), (tx + 35, ty), base_width=4,
                         color=(180, 235, 255), alpha=alpha, core_white=True)
        _draw_bloom_line(painter, (tx, ty - 35), (tx, ty + 35), base_width=4,
                         color=(180, 235, 255), alpha=alpha, core_white=True)

        _draw_expanding_shockwave(painter, tx, ty, max_radius=80, p=p,
                                 color=(140, 215, 255), alpha=alpha, aspect=0.7, rings=2)
        _draw_physics_particles(painter, tx, ty, p, count=20,
                                color=(190, 240, 255), alpha=alpha, seed=520,
                                spread_x=70.0, spread_y=55.0, gravity=50.0, upward=False)
        _draw_starburst(painter, tx, ty, int(22 + 26 * math.sin(p * math.pi)),
                        QColor(255, 255, 255, alpha), QColor(100, 200, 255, alpha))
        return True

    elif eff_name == "soluna_slash":
        # 【日月交替】：旭日狂焰與極月星輝雙姿態對斬！雙色太極 160° 厚實帶狀流光 + 日月核心核融爆裂 + 26 顆金藍交織火花
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        deg_sun = -135 + p * 35
        _draw_ribbon_slash(painter, tx - 10, ty, start_deg=deg_sun, sweep_deg=160,
                           inner_r=26, outer_r=80, color=(255, 120, 30), alpha=alpha, core_white=True)

        deg_moon = 45 - p * 35
        _draw_ribbon_slash(painter, tx + 10, ty, start_deg=deg_moon, sweep_deg=160,
                           inner_r=26, outer_r=80, color=(80, 195, 255), alpha=alpha, core_white=True)

        _draw_bloom_line(painter, (tx - 45, ty - 30), (tx + 45, ty + 30), base_width=5.5,
                         color=(255, 230, 140), alpha=alpha, core_white=True)
        _draw_bloom_line(painter, (tx + 40, ty - 30), (tx - 40, ty + 30), base_width=5.5,
                         color=(140, 220, 255), alpha=alpha, core_white=True)

        _draw_expanding_shockwave(painter, tx, ty, max_radius=95, p=p,
                                 color=(255, 200, 100), alpha=alpha, aspect=0.65, rings=2)

        _draw_physics_particles(painter, tx - 10, ty, p, count=13,
                                color=(255, 180, 50), alpha=alpha, seed=771,
                                spread_x=75.0, spread_y=60.0, gravity=70.0, upward=False)
        _draw_physics_particles(painter, tx + 10, ty, p, count=13,
                                color=(100, 210, 255), alpha=alpha, seed=772,
                                spread_x=75.0, spread_y=60.0, gravity=70.0, upward=False)
        _draw_starburst(painter, tx, ty, int(26 + 30 * math.sin(p * math.pi)),
                        QColor(255, 255, 255, alpha), QColor(255, 215, 60, alpha))
        return True

    elif eff_name == "soluna_time_aura":
        # 【日月星辰】：天界日月渾天儀星象陣法！雙層日月星盤 + 日月二星雙軌公轉帶狀拖尾 + 貫天星柱 + 20 顆升騰靈氣
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        _draw_magic_circle(painter, cx, cy + 15, int(40 + 8 * math.sin(p * math.pi)), rot_angle * 0.05, QColor(255, 180, 50, alpha))
        _draw_magic_circle(painter, cx, cy + 15, int(22 + 5 * math.sin(p * math.pi)), -rot_angle * 0.07, QColor(90, 200, 255, int(alpha * 0.75)))

        rx = 42 + 6 * math.sin(p * math.pi)
        ry = 18 + 3 * math.sin(p * math.pi)
        ang_sun = rot_angle * 0.08
        sx = cx + math.cos(ang_sun) * rx
        sy = cy - 8 + math.sin(ang_sun) * ry
        _draw_starburst(painter, sx, sy, 11, QColor(255, 255, 255, alpha), QColor(255, 170, 40, alpha))
        _draw_ribbon_slash(painter, cx, cy - 8, start_deg=math.degrees(ang_sun) - 50, sweep_deg=50,
                           inner_r=rx - 5, outer_r=rx + 5, color=(255, 160, 40), alpha=int(alpha * 0.6), core_white=False)

        ang_moon = ang_sun + math.pi
        mx = cx + math.cos(ang_moon) * rx
        my = cy - 8 + math.sin(ang_moon) * ry
        _draw_starburst(painter, mx, my, 11, QColor(255, 255, 255, alpha), QColor(100, 210, 255, alpha))
        _draw_ribbon_slash(painter, cx, cy - 8, start_deg=math.degrees(ang_moon) - 50, sweep_deg=50,
                           inner_r=rx - 5, outer_r=rx + 5, color=(90, 200, 255), alpha=int(alpha * 0.6), core_white=False)

        _draw_bloom_line(painter, (cx, cy + 15), (cx, cy - 80), base_width=15,
                         color=(255, 210, 120), alpha=int(alpha * 0.75), core_white=True)

        _draw_physics_particles(painter, cx, cy + 12, p, count=20,
                                color=(240, 230, 180), alpha=alpha, seed=333,
                                spread_x=36.0, spread_y=70.0, gravity=20.0, upward=True)
        return True

    elif eff_name == "soul_penetrate_thrust":
        # 【光魂刺擊】：召喚光之劍魂連續 3 次極速穿心突刺！3 道白金核融突刺光束 + 錐形熱浪網格 + 衝擊波紋 + 20 顆星光微粒
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        for si in range(3):
            sy = ty + (si - 1) * 18
            _draw_bloom_line(painter, (tx - 65, sy), (tx + 40, sy), base_width=7,
                             color=(210, 180, 255), alpha=alpha, core_white=True)

        _draw_ribbon_slash(painter, tx + 15, ty, start_deg=-140, sweep_deg=50,
                           inner_r=15, outer_r=55, color=(160, 210, 255), alpha=int(alpha * 0.8), core_white=True)
        _draw_ribbon_slash(painter, tx + 15, ty, start_deg=90, sweep_deg=50,
                           inner_r=15, outer_r=55, color=(160, 210, 255), alpha=int(alpha * 0.8), core_white=True)

        _draw_expanding_shockwave(painter, tx, ty, max_radius=78, p=p,
                                 color=(180, 200, 255), alpha=alpha, aspect=0.7, rings=2)
        _draw_physics_particles(painter, tx, ty, p, count=20,
                                color=(220, 210, 255), alpha=alpha, seed=654,
                                spread_x=70.0, spread_y=50.0, gravity=60.0, upward=False)
        _draw_starburst(painter, tx + 20, ty, 20, QColor(255, 255, 255, alpha), QColor(160, 180, 255, alpha))
        return True

    elif eff_name == "styx_crossing":
        # 【靈魂裂斬 (極致冥河斬)】：太古光魂巨刃天降怒劈！貫穿大地引爆極凍深淵 + 6 道裂地冰霜金痕 + 衝擊巨環 + 28 顆星芒碎岩
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        ground_y = ty + 16

        _draw_bloom_line(painter, (tx, ty - 130), (tx, ground_y), base_width=18,
                         color=(100, 205, 255), alpha=alpha, core_white=True)

        _draw_ribbon_slash(painter, tx, ty - 10, start_deg=-160, sweep_deg=140,
                           inner_r=25, outer_r=85, color=(140, 220, 255), alpha=int(alpha * 0.85), core_white=True)

        f_len = 30 + 80 * p
        fractures = [
            (tx, ground_y, tx - f_len * 0.85, ground_y + 12),
            (tx, ground_y, tx + f_len * 0.85, ground_y + 12),
            (tx, ground_y, tx - f_len * 0.45, ground_y - 10),
            (tx, ground_y, tx + f_len * 0.45, ground_y - 10),
            (tx, ground_y, tx - f_len * 0.15, ground_y + 18),
            (tx, ground_y, tx + f_len * 0.15, ground_y + 18),
        ]
        for x1, y1, x2, y2 in fractures:
            _draw_bloom_line(painter, (x1, y1), (x2, y2), base_width=3.5,
                             color=(120, 215, 255), alpha=int(alpha * (1.0 - p * 0.4)), core_white=True)

        _draw_expanding_shockwave(painter, tx, ground_y, max_radius=115, p=p,
                                 color=(110, 220, 255), alpha=alpha, aspect=0.35, rings=2)

        _draw_physics_particles(painter, tx, ground_y, p, count=28,
                                color=(180, 240, 255), alpha=alpha, seed=999,
                                spread_x=90.0, spread_y=65.0, gravity=60.0, upward=False)
        _draw_starburst(painter, tx, ground_y, int(26 + 32 * math.sin(p * math.pi)),
                        QColor(255, 255, 255, alpha), QColor(80, 200, 255, alpha))
        return True

    return False

