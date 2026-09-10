"""
新楓之谷 冒險家 法師 (火毒 / 冰雷 / 主教) 技能特效渲染模組 (mages.py)
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

MAGES_EFFECTS = {'paralyze_cloud', 'chain_lightning', 'frozen_orb', 'meditation_aura', 'flame_haze', 'ice_age', 'divine_punish_light', 'genesis_holy_pillar', 'thunder_storm_bolts', 'blessed_harmony_aura', 'holy_symbol', 'peacemaker', 'meteor_shower', 'megiddo_fireball', 'mist_eruption', 'lightning_sphere', 'holy_heal_wave', 'speed_cast_aura', 'blizzard_storm', 'holy_magic_shell', 'poison_mist', 'freezing_breath_cone', 'poison_nova', 'angel_ray'}


def render_mages_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty,
                       rot_angle=0.0, seed=0.0, fracture_lines=None, **kwargs) -> bool:
    if eff_name == "poison_mist":
        # 劇毒迷霧：翻騰墨綠與紫黑劇毒毒雲
        for i in range(8):
            ang = i * (math.pi * 2 / 8) + seed
            dist = 18 + 55 * p
            mx = tx + math.cos(ang) * dist
            my = ty + math.sin(ang) * (dist * 0.6)
            painter.setBrush(QBrush(QColor(80, 220, 60, int(alpha * 0.6))))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(mx, my), 22, 16)
        return True
    elif eff_name == "poison_nova":
        # 劇毒新星：360度環形擴散劇毒氣泡星環
        rad = int(25 + 95 * p)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(60, 240, 90, alpha), 3))
        painter.drawEllipse(QPointF(tx, ty), rad, rad)
        for i in range(12):
            ang = i * (math.pi * 2 / 12) + seed
            bx = tx + math.cos(ang) * rad
            by = ty + math.sin(ang) * rad
            painter.setBrush(QBrush(QColor(180, 60, 255, alpha)))
            painter.drawEllipse(QPointF(bx, by), 6, 6)
        return True
    elif eff_name == "meteor_shower":
        # 火焰流星：天降燃燒赤紅隕石呼嘯墜地
        met_x = (tx + 80) - 80 * min(1.0, p * 2.0)
        met_y = (ty - 160) + 160 * min(1.0, p * 2.0)
        painter.setPen(QPen(QColor(255, 60, 20, int(alpha * 0.7)), 8))
        painter.drawLine(QPointF(met_x + 40, met_y - 80), QPointF(met_x, met_y))
        painter.setBrush(QBrush(QColor(255, 200, 50, alpha)))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawEllipse(QPointF(met_x, met_y), 22, 22)
        return True
    elif eff_name == "flame_haze":
        # 炙炎爆破：烈火與毒霧化成的燃燒火霧波浪
        rad = int(30 + 60 * p)
        rg = QRadialGradient(tx, ty, rad)
        rg.setColorAt(0.0, QColor(255, 100, 20, alpha))
        rg.setColorAt(0.6, QColor(200, 40, 180, int(alpha * 0.7)))
        rg.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(rg))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(tx, ty), rad, rad)
        return True
    elif eff_name == "mist_eruption":
        # 劇毒爆發：全場火毒連鎖核爆
        rad = int(40 + 120 * p)
        _draw_starburst(painter, tx, ty, rad, QColor(255, 255, 255, alpha), QColor(255, 80, 40, alpha))

    # =========================================================================
    # 8. 冰雷大魔導士 (Ice/Lightning)
    # =========================================================================
        return True
    elif eff_name == "paralyze_cloud":
        # 致命毒霧：濃綠色腐蝕毒柱噴發
        for pi in range(5):
            px = tx + (pi - 2) * 16 + math.sin(p * 8.0 + pi) * 6
            py = ty + 15 - p * 75 - pi * 4
            p_rad = int(12 + 10 * p)
            painter.setBrush(QBrush(QColor(120, 240, 70, int(alpha * 0.6))))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(px, py), p_rad, p_rad)
        return True
    elif eff_name == "meditation_aura":
        # 魔力吸收：腳下藍紅雙重魔法陣旋轉
        _draw_magic_circle(painter, cx, cy + 12, 34, rot_angle * 0.04, QColor(255, 130, 60, alpha))
        _draw_magic_circle(painter, cx, cy + 12, 22, -rot_angle * 0.06, QColor(100, 240, 150, alpha))
        return True
    elif eff_name == "megiddo_fireball":
        # 梅吉多之火：藍焰幽冥魔球向目標轟擊，周身伴隨青焰螺旋
        fly_p = min(1.0, p * 2.2)
        fx = cx + (tx - cx) * fly_p
        fy = (cy - 10) + (ty - (cy - 10)) * fly_p
        painter.save()
        painter.translate(fx, fy)
        for ai in range(4):
            ang = rot_angle * 0.05 + ai * (math.pi / 2)
            ax = math.cos(ang) * (14 + 6 * math.sin(p * math.pi))
            ay = math.sin(ang) * 10
            painter.setBrush(QBrush(QColor(60, 180, 255, int(alpha * 0.7))))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(ax, ay), 5, 5)
        rg = QRadialGradient(0, 0, 20)
        rg.setColorAt(0.0, QColor(255, 255, 255, alpha))
        rg.setColorAt(0.4, QColor(80, 160, 255, int(alpha * 0.9)))
        rg.setColorAt(0.8, QColor(30, 40, 180, int(alpha * 0.5)))
        rg.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(rg))
        painter.drawEllipse(QPointF(0, 0), 18, 18)
        painter.restore()
        return True
    elif eff_name == "chain_lightning":
        # 連鎖閃電：碎形分叉藍紫連鎖高壓電弧
        painter.setPen(QPen(QColor(60, 140, 255, alpha), 4))
        p1 = (cx, cy)
        p2 = (tx, ty)
        painter.drawLine(QPointF(p1[0], p1[1]), QPointF(p1[0] + (p2[0]-p1[0])*0.3, p1[1]-25))
        painter.drawLine(QPointF(p1[0] + (p2[0]-p1[0])*0.3, p1[1]-25), QPointF(p1[0] + (p2[0]-p1[0])*0.6, p1[1]+25))
        painter.drawLine(QPointF(p1[0] + (p2[0]-p1[0])*0.6, p1[1]+25), QPointF(p2[0], p2[1]))
        painter.setPen(QPen(QColor(255, 255, 255, alpha), 1.5))
        painter.drawLine(QPointF(p1[0], p1[1]), QPointF(p2[0], p2[1]))
        return True
    elif eff_name == "blizzard_storm":
        # 極地暴風雪：尖銳冰錐傾瀉而下
        for i in range(7):
            ix = tx - 60 + i * 20
            iy = (ty - 130) + 130 * min(1.0, (p * 2.0 + i * 0.1))
            painter.setBrush(QBrush(QColor(180, 235, 255, alpha)))
            painter.setPen(QPen(QColor(255, 255, 255, alpha), 1))
            poly = QPolygonF([QPointF(ix, iy - 25), QPointF(ix + 6, iy), QPointF(ix, iy + 10), QPointF(ix - 6, iy)])
            painter.drawPolygon(poly)
        return True
    elif eff_name == "ice_age":
        # 冰河紀元：地表極霜蔓延與冰河裂紋
        crack_w = int(140 * min(1.0, p * 1.8))
        painter.setPen(QPen(QColor(140, 220, 255, alpha), 3))
        painter.drawLine(QPointF(tx - crack_w // 2, ty + 15), QPointF(tx + crack_w // 2, ty + 15))
        painter.setPen(QPen(QColor(255, 255, 255, alpha), 1.5))
        painter.drawLine(QPointF(tx - crack_w // 3, ty + 15), QPointF(tx + crack_w // 3, ty + 15))
        return True
    elif eff_name == "lightning_sphere":
        # 閃電球：高速自轉雷電核心聚能球
        painter.save()
        painter.translate(tx, ty)
        painter.rotate(rot_angle)
        painter.setBrush(QBrush(QColor(60, 160, 255, int(alpha * 0.7))))
        painter.setPen(QPen(QColor(240, 255, 255, alpha), 2))
        painter.drawEllipse(QPointF(0, 0), 25, 25)
        for ang_i in [0, 90, 180, 270]:
            painter.rotate(ang_i)
            painter.drawLine(QPointF(0, -32), QPointF(0, -25))
        painter.restore()
        return True
    elif eff_name == "frozen_orb":
        # 寒霜領域：旋轉冰霜晶球向八方噴射碎冰
        rad = int(24 + 10 * math.sin(p * math.pi))
        painter.setBrush(QBrush(QColor(200, 240, 255, alpha)))
        painter.setPen(QPen(QColor(80, 180, 255, alpha), 2))
        painter.drawEllipse(QPointF(tx, ty), rad, rad)
        for i in range(8):
            ang = i * (math.pi / 4) + rot_angle * 0.04
            dist = rad + 25 * p
            painter.setPen(QPen(QColor(255, 255, 255, alpha), 2))
            painter.drawPoint(QPointF(tx + math.cos(ang) * dist, ty + math.sin(ang) * dist))

    # =========================================================================
    # 9. 主教 (Bishop)
    # =========================================================================
        return True
    elif eff_name == "freezing_breath_cone":
        # 急凍吐息：極寒冰錐扇形噴湧
        for bi in range(6):
            b_ang = -0.6 + bi * 0.24
            bx = cx + math.cos(b_ang) * (80 * p)
            by = cy + math.sin(b_ang) * (80 * p)
            painter.setPen(QPen(QColor(180, 240, 255, alpha), 3))
            painter.drawLine(QPointF(cx, cy), QPointF(bx, by))
        return True
    elif eff_name == "speed_cast_aura":
        # 極速詠唱：湛藍閃電電弧在角色周圍躍動
        for li in range(4):
            lx = cx + random.randint(-25, 25)
            ly = cy - 25 + random.randint(-20, 20)
            painter.setPen(QPen(QColor(120, 220, 255, alpha), 2))
            painter.drawLine(QPointF(cx, cy - 10), QPointF(lx, ly))
        return True
    elif eff_name == "thunder_storm_bolts":
        # 雷霆風暴：三道天際落雷垂直轟頂
        for ti in range(3):
            tx_bolt = tx + (ti - 1) * 28
            painter.setPen(QPen(QColor(100, 200, 255, alpha), 4))
            painter.drawLine(QPointF(tx_bolt, ty - 120), QPointF(tx_bolt, ty))
            painter.setPen(QPen(QColor(255, 255, 255, alpha), 2))
            painter.drawLine(QPointF(tx_bolt, ty - 120), QPointF(tx_bolt, ty))

    # =========================================================================
    # 12. 主教新增技能 (Bishop 6~8)
    # =========================================================================
        return True
    elif eff_name == "angel_ray":
        # 【天使之箭】：聖潔大天使六翼展開！直貫目標白金核融聖矢 + 目標處急救聖十字 + 衝擊波環 + 升騰金曜甘霖
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        
        # 1. 施法起點聖光羽翼展開 (Ribbon Mesh)
        wing_span = 35 * math.sin(p * math.pi)
        _draw_ribbon_slash(painter, cx, cy, start_deg=-140, sweep_deg=70,
                           inner_r=15, outer_r=15 + wing_span, color=(255, 230, 120), alpha=int(alpha * 0.8), core_white=True)
        _draw_ribbon_slash(painter, cx, cy, start_deg=70, sweep_deg=70,
                           inner_r=15, outer_r=15 + wing_span, color=(255, 230, 120), alpha=int(alpha * 0.8), core_white=True)

        # 2. 直貫目標的三層核融白金聖矢光束 (Bloom Line)
        beam_w = int(18 * math.sin(p * math.pi))
        _draw_bloom_line(painter, (cx, cy), (tx, ty), base_width=max(4, beam_w),
                         color=(255, 215, 80), alpha=alpha, core_white=True)

        # 3. 目標處急救翡翠聖十字 (Bloom Lines)
        cross_sz = int(22 * math.sin(p * math.pi))
        _draw_bloom_line(painter, (tx - cross_sz, ty), (tx + cross_sz, ty), base_width=4,
                         color=(140, 255, 190), alpha=alpha, core_white=True)
        _draw_bloom_line(painter, (tx, ty - cross_sz * 1.3), (tx, ty + cross_sz * 1.3), base_width=4,
                         color=(140, 255, 190), alpha=alpha, core_white=True)

        # 4. 目標衝擊波環與升騰金色治癒甘霖 (Physics Particles)
        _draw_expanding_shockwave(painter, tx, ty, max_radius=75, p=p,
                                 color=(255, 220, 90), alpha=alpha, aspect=0.7, rings=2)
        _draw_physics_particles(painter, tx, ty, p, count=18,
                                color=(255, 240, 140), alpha=alpha, seed=333,
                                spread_x=45.0, spread_y=60.0, gravity=25.0, upward=True)
        _draw_starburst(painter, tx, ty, int(20 + 26 * math.sin(p * math.pi)),
                        QColor(255, 255, 255, alpha), QColor(255, 220, 80, alpha))
        return True
    elif eff_name == "holy_symbol":
        # 【神聖祈禱】：遠征隊核心神聖光環！地面雙層八角金曜星陣 + 貫天核融神聖光柱 + 巨大金曜聖十字 + 24 顆升騰祈禱金光
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        
        # 1. 地面雙層八芒神聖祈禱法陣
        _draw_magic_circle(painter, cx, cy + 16, int(42 + 10 * math.sin(p * math.pi)), rot_angle * 0.05, QColor(255, 215, 60, alpha))
        _draw_magic_circle(painter, cx, cy + 16, int(22 + 6 * math.sin(p * math.pi)), -rot_angle * 0.07, QColor(255, 245, 150, int(alpha * 0.7)))

        # 2. 貫天神聖核融光柱升騰 (Bloom Line)
        beam_w = int(26 + 12 * math.sin(p * math.pi))
        _draw_bloom_line(painter, (cx, cy + 16), (cx, cy - 88), base_width=beam_w,
                         color=(255, 215, 70), alpha=int(alpha * 0.85), core_white=True)

        # 3. 巨大金色神聖十字聖印 (Bloom Lines)
        cross_cy = cy - 26
        _draw_bloom_line(painter, (cx - 24, cross_cy), (cx + 24, cross_cy), base_width=5.5,
                         color=(255, 235, 120), alpha=alpha, core_white=True)
        _draw_bloom_line(painter, (cx, cross_cy - 34), (cx, cross_cy + 22), base_width=6.0,
                         color=(255, 235, 120), alpha=alpha, core_white=True)
        _draw_starburst(painter, cx, cross_cy, 22, QColor(255, 255, 255, alpha), QColor(255, 210, 60, alpha))

        # 4. 24 顆冉冉升騰金曜祈禱星光粒子 (Physics Souls)
        _draw_physics_particles(painter, cx, cy + 12, p, count=24,
                                color=(255, 245, 160), alpha=alpha, seed=777,
                                spread_x=38.0, spread_y=75.0, gravity=22.0, upward=True)
        return True
    elif eff_name == "genesis_holy_pillar":
        # 【天怒】：九天神怒！全螢幕天界金曜核融聖柱貫地 + 4 柱伴生天罰 + 碎形聖電 + 地動衝擊巨環 + 30 顆金曜火花噴泉
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        ground_y = ty + 14
        
        # 1. 天際與地面雙層八芒神罰法陣
        cir_rad = int(45 + 45 * math.sin(p * math.pi))
        _draw_magic_circle(painter, tx, ground_y, cir_rad, rot_angle * 0.05, QColor(255, 215, 70, alpha))
        _draw_magic_circle(painter, tx, 18, int(cir_rad * 0.65), -rot_angle * 0.07, QColor(255, 245, 140, int(alpha * 0.6)))

        # 2. 5 柱貫天神聖天罰核融白金聖柱 (Bloom Lines)
        strikes = [
            (tx, 0.0, 24, 111),
            (tx - 65, -16.0, 11, 222),
            (tx + 62, 16.0, 11, 333),
            (tx - 34, -8.0, 13, 444),
            (tx + 32, 8.0, 13, 555),
        ]
        for sx, x_drift, width, seed in strikes:
            # 碎形神聖雷芒
            _draw_crackling_lightning(painter, (sx + x_drift * 0.3, 0), (sx + x_drift, ground_y), p,
                                      QColor(255, 230, 90), alpha, jitter=12.0, steps=7, seed=seed)
            # 白金核融聖柱本體
            _draw_bloom_line(painter, (sx, 0), (sx, ground_y), base_width=width,
                             color=(255, 215, 80), alpha=alpha, core_white=True)

        # 3. 地面雙層地動衝擊破裂巨環與裂地金痕
        _draw_expanding_shockwave(painter, tx, ground_y, max_radius=130, p=p,
                                 color=(255, 235, 120), alpha=alpha, aspect=0.35, rings=2)
        _draw_bloom_line(painter, (tx - 60, ground_y), (tx + 60, ground_y), base_width=5,
                         color=(255, 245, 180), alpha=int(alpha * (1.0 - p * 0.4)), core_white=True)

        # 4. 30 顆地面反彈跳動的聖光金曜火花噴泉 (Physics Embers)
        _draw_physics_particles(painter, tx, ground_y - 5, p, count=30,
                                color=(255, 240, 130), alpha=alpha, seed=888,
                                spread_x=95.0, spread_y=65.0, gravity=180.0, upward=False)
        _draw_starburst(painter, tx, ground_y - 15, int(28 + 36 * math.sin(p * math.pi)),
                        QColor(255, 255, 255, alpha), QColor(255, 215, 60, alpha))
        return True
    elif eff_name == "holy_magic_shell":
        # 【神聖之盾】：立體半球琉璃晶格聖盾力場！半球雙層防禦弧面 + 六角菱形晶格 + 脈衝防護波 + 升騰守護金曜
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        
        # 1. 半球雙層琉璃防護弧面 (Ribbon Mesh)
        _draw_ribbon_slash(painter, cx, cy, start_deg=0, sweep_deg=180,
                           inner_r=36, outer_r=50, color=(255, 235, 140), alpha=alpha, core_white=True)

        # 2. 半球外圍 6 顆懸浮旋轉菱形守護晶格
        for ri in range(6):
            r_ang = math.pi + ri * (math.pi / 5) + rot_angle * 0.04
            rx = cx + math.cos(r_ang) * 45
            ry = cy - 6 + math.sin(r_ang) * 35
            painter.setBrush(QBrush(QColor(255, 245, 180, alpha)))
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(QPolygonF([QPointF(rx, ry - 3.5), QPointF(rx + 3.5, ry), QPointF(rx, ry + 3.5), QPointF(rx - 3.5, ry)]))

        # 3. 半球頂點白熾神聖核心光輝
        _draw_starburst(painter, cx, cy - 40, 18, QColor(255, 255, 255, alpha), QColor(255, 220, 100, alpha))

        # 4. 防護脈衝擴散波環與升騰守護微粒
        _draw_expanding_shockwave(painter, cx, cy - 10, max_radius=65, p=p,
                                 color=(255, 230, 130), alpha=alpha, aspect=0.85, rings=1)
        _draw_physics_particles(painter, cx, cy + 10, p, count=18,
                                color=(255, 240, 160), alpha=alpha, seed=333,
                                spread_x=35.0, spread_y=55.0, gravity=20.0, upward=True)
        return True
    elif eff_name == "peacemaker":
        # 【祈禱聖泉 (和平使者)】：神聖白鴿光彈破空穿梭！白金雙翼帶狀流光 + 螺旋聖泉洗滌波環 + 20 顆神聖純淨光點
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        cur_x = cx + (tx - cx) * min(1.0, p * 1.3)
        cur_y = cy - 10 + (ty - (cy - 10)) * min(1.0, p * 1.3) + math.sin(p * 8.0) * 14

        # 1. 白金聖鴿雙翼扇面帶狀流光 (Ribbon Mesh)
        deg_p = rot_angle * 0.1
        _draw_ribbon_slash(painter, cur_x, cur_y, start_deg=deg_p - 40, sweep_deg=80,
                           inner_r=12, outer_r=36, color=(255, 235, 120), alpha=int(alpha * 0.85), core_white=True)
        _draw_ribbon_slash(painter, cur_x, cur_y, start_deg=deg_p + 140, sweep_deg=80,
                           inner_r=12, outer_r=36, color=(255, 235, 120), alpha=int(alpha * 0.85), core_white=True)

        # 2. 光彈核心白熾聖光球
        rg = QRadialGradient(cur_x, cur_y, 16)
        rg.setColorAt(0.0, QColor(255, 255, 255, alpha))
        rg.setColorAt(0.4, QColor(255, 225, 90, int(alpha * 0.9)))
        rg.setColorAt(1.0, QColor(255, 180, 50, 0))
        painter.setBrush(QBrush(rg))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cur_x, cur_y), 16, 16)

        # 核心十字微芒
        _draw_bloom_line(painter, (cur_x - 18, cur_y), (cur_x + 18, cur_y), base_width=3,
                         color=(255, 240, 140), alpha=alpha, core_white=True)
        _draw_bloom_line(painter, (cur_x, cur_y - 18), (cur_x, cur_y + 18), base_width=3,
                         color=(255, 240, 140), alpha=alpha, core_white=True)

        # 3. 命中目標時的螺旋聖泉洗滌波環與神聖微粒
        if p > 0.45:
            _draw_expanding_shockwave(painter, tx, ty, max_radius=85, p=(p - 0.45) / 0.55,
                                     color=(255, 230, 120), alpha=alpha, aspect=0.7, rings=3)
            _draw_physics_particles(painter, tx, ty, (p - 0.45) / 0.55, count=20,
                                    color=(255, 245, 160), alpha=alpha, seed=999,
                                    spread_x=65.0, spread_y=55.0, gravity=40.0, upward=False)
            _draw_starburst(painter, tx, ty, 20, QColor(255, 255, 255, alpha), QColor(255, 215, 70, alpha))
        return True

    # =========================================================================
    # 10. 夜使者 (Night Lord)
    # =========================================================================
        return True
    elif eff_name == "holy_heal_wave":
        # 【群體治癒】：全隊翡翠聖潔甘霖擴散！雙層碧綠治癒波紋 + 升騰白熾翡翠聖十字 + 22 顆治癒生命微粒
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        
        # 1. 施法者腳底翡翠生命法陣
        _draw_magic_circle(painter, cx, cy + 12, int(32 + 10 * math.sin(p * math.pi)), rot_angle * 0.05, QColor(100, 255, 170, alpha))

        # 2. 中央升騰而起的翡翠白金聖十字架 (Bloom Lines)
        cross_y = cy - 25 - int(25 * p)
        c_len = int(18 + 8 * math.sin(p * math.pi))
        _draw_bloom_line(painter, (cx - c_len, cross_y), (cx + c_len, cross_y), base_width=4.5,
                         color=(120, 255, 180), alpha=alpha, core_white=True)
        _draw_bloom_line(painter, (cx, cross_y - c_len * 1.3), (cx, cross_y + c_len), base_width=5.0,
                         color=(120, 255, 180), alpha=alpha, core_white=True)

        # 3. 雙層翡翠治癒擴散波
        _draw_expanding_shockwave(painter, cx, cy, max_radius=95, p=p,
                                 color=(130, 255, 190), alpha=alpha, aspect=0.55, rings=2)

        # 4. 22 顆緩慢升騰浮力的治癒甘霖光球 (Physics Particles)
        _draw_physics_particles(painter, cx, cy + 10, p, count=22,
                                color=(160, 255, 200), alpha=alpha, seed=222,
                                spread_x=50.0, spread_y=60.0, gravity=18.0, upward=True)
        _draw_starburst(painter, cx, cross_y, 16, QColor(255, 255, 255, alpha), QColor(120, 255, 180, alpha))
        return True
    elif eff_name == "blessed_harmony_aura":
        # 【天祝】：大主教神聖祈福！腳底雙層八芒金曜法陣 + 頭頂懸浮核融白金聖十字 + 4 顆環繞祈禱聖符 + 升騰天祝甘霖
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        
        # 1. 腳底雙層八芒神聖祝福法陣
        _draw_magic_circle(painter, cx, cy + 14, int(36 + 8 * math.sin(p * math.pi)), rot_angle * 0.05, QColor(255, 215, 70, alpha))
        _draw_magic_circle(painter, cx, cy + 14, int(18 + 4 * math.sin(p * math.pi)), -rot_angle * 0.08, QColor(255, 245, 140, int(alpha * 0.7)))

        # 2. 頭頂懸浮核融白金聖十字架 (Bloom Lines)
        cross_y = cy - 48
        _draw_bloom_line(painter, (cx - 18, cross_y), (cx + 18, cross_y), base_width=4.5,
                         color=(255, 230, 90), alpha=alpha, core_white=True)
        _draw_bloom_line(painter, (cx, cross_y - 25), (cx, cross_y + 18), base_width=5.0,
                         color=(255, 230, 90), alpha=alpha, core_white=True)
        _draw_starburst(painter, cx, cross_y, 16, QColor(255, 255, 255, alpha), QColor(255, 215, 80, alpha))

        # 3. 4 顆環繞旋轉祈禱聖符 (帶狀拖尾)
        rx = 35 + 5 * math.sin(p * math.pi)
        ry = 14 + 3 * math.sin(p * math.pi)
        for i in range(4):
            ang = rot_angle * 0.09 + i * (math.pi / 2)
            ox = cx + math.cos(ang) * rx
            oy = cy - 10 + math.sin(ang) * ry
            _draw_starburst(painter, ox, oy, 7, QColor(255, 255, 255, alpha), QColor(255, 220, 80, alpha))
            deg = math.degrees(ang)
            _draw_ribbon_slash(painter, cx, cy - 10, start_deg=deg - 45, sweep_deg=45,
                               inner_r=rx - 4, outer_r=rx + 4, color=(255, 210, 80), alpha=int(alpha * 0.5), core_white=False)

        # 4. 貫天神聖金光與升騰天祝甘霖
        _draw_bloom_line(painter, (cx, cy + 14), (cx, cy - 75), base_width=14,
                         color=(255, 225, 100), alpha=int(alpha * 0.65), core_white=True)
        _draw_physics_particles(painter, cx, cy + 10, p, count=20,
                                color=(255, 240, 150), alpha=alpha, seed=555,
                                spread_x=35.0, spread_y=65.0, gravity=20.0, upward=True)
        return True
    elif eff_name == "divine_punish_light":
        # 【神聖懲罰】：天界審判神矛天降貫穿！核融白金光柱轟鳴 + 雙向破裂聖焰弧光 + 審判雙層衝擊巨環 + 金曜神火飛濺
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        
        # 1. 天際激射而下的核融白金神矛 (Bloom Line)
        _draw_bloom_line(painter, (tx, ty - 125), (tx, ty + 10), base_width=16,
                         color=(255, 230, 90), alpha=alpha, core_white=True)

        # 2. 矛尖刺入瞬間激起的雙向扇面帶狀聖焰 (Ribbon Mesh)
        _draw_ribbon_slash(painter, tx, ty, start_deg=-150, sweep_deg=65,
                           inner_r=18, outer_r=68, color=(255, 215, 80), alpha=int(alpha * 0.85), core_white=True)
        _draw_ribbon_slash(painter, tx, ty, start_deg=85, sweep_deg=65,
                           inner_r=18, outer_r=68, color=(255, 215, 80), alpha=int(alpha * 0.85), core_white=True)

        # 3. 審判雙層衝擊破裂巨環
        _draw_expanding_shockwave(painter, tx, ty, max_radius=95, p=p,
                                 color=(255, 220, 100), alpha=alpha, aspect=0.7, rings=2)

        # 4. 24 顆神界審判金曜火花粒子 (Physics Embers)
        _draw_physics_particles(painter, tx, ty, p, count=24,
                                color=(255, 245, 140), alpha=alpha, seed=666,
                                spread_x=80.0, spread_y=60.0, gravity=85.0, upward=False)
        _draw_starburst(painter, tx, ty, int(25 + 30 * math.sin(p * math.pi)),
                        QColor(255, 255, 255, alpha), QColor(255, 200, 60, alpha))

    # =========================================================================
    # 13. 夜使者新增技能 (Night Lord 6~8)
    # =========================================================================
        return True
    return False
