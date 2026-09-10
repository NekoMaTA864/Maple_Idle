"""
新楓之谷 冒險家 海盜 (拳霸 / 槍神 / 重砲指揮官) 技能特效渲染模組 (pirates.py)
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

PIRATES_EFFECTS = {'pirate_flag_aura', 'rolling_rainbow', 'bullet_barrage_spit', 'octopunch', 'cannon_bazooka', 'death_trigger', 'serpent_screw_wave', 'lord_of_the_deep', 'energy_blast', 'icbm_missile', 'cannon_barrage', 'pirate_spirit_aura', 'rapid_fire', 'broadside', 'nautilus_barrage', 'eight_legs_cannon', 'monkey_militia', 'nautilus_battleship_strike', 'cannon_overload_blast', 'power_unity', 'time_leap_aura', 'target_lock', 'super_transform', 'poolmaker_artillery'}


def render_pirates_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty,
                       rot_angle=0.0, seed=0.0, fracture_lines=None, **kwargs) -> bool:
    if eff_name == "octopunch":
        # 醒拳連打：極速拳山 + 海藍同心圓衝擊波
        for pi_i in range(6):
            delay = pi_i * 0.08
            cur_p = max(0.0, min(1.0, (p - delay) / 0.5))
            if cur_p > 0:
                px_off = pi_i * 10 - 25
                py_off = math.sin(pi_i * 1.5) * 12
                punch_x = tx + px_off
                punch_y = ty + py_off
                painter.setBrush(QBrush(QColor(60, 180, 255, int(alpha * 0.7))))
                painter.setPen(QPen(QColor(180, 240, 255, alpha), 1.5))
                painter.drawEllipse(QPointF(punch_x, punch_y), int(12 * cur_p), int(12 * cur_p))
                # 每拳同心圆況衝波
                if cur_p > 0.5:
                    _draw_expanding_shockwave(painter, punch_x, punch_y, max_radius=30, p=(cur_p - 0.5) / 0.5,
                                             color=(60, 180, 255), alpha=int(alpha * 0.6), aspect=0.6, rings=1)
        return True
    elif eff_name == "lord_of_the_deep":
        # 海龍突擊：幽靈水龍盤旋和身住空中突進和咬擊
        # 水龍 S 形身體
        drg_x = cx + (tx - cx) * min(1.0, p * 1.4)
        path_dragon = QPainterPath()
        path_dragon.moveTo(drg_x - 40, cy - 20)
        path_dragon.cubicTo(drg_x - 10, cy - 50, drg_x + 20, cy + 10, drg_x + 45, cy - 15)
        path_dragon.cubicTo(drg_x + 50, cy - 5, drg_x + 50, cy + 10, drg_x + 35, cy + 15)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(60, 180, 255, alpha), 8))
        painter.drawPath(path_dragon)
        painter.setPen(QPen(QColor(180, 240, 255, int(alpha * 0.6)), 3))
        painter.drawPath(path_dragon)
        # 水龍大口和咬
        painter.setBrush(QBrush(QColor(20, 100, 200, int(alpha * 0.7))))
        painter.setPen(QPen(QColor(120, 220, 255, alpha), 2))
        painter.drawEllipse(QPointF(drg_x + 45, cy - 18), 12, 8)
        # 水波衝擊
        if p > 0.4:
            hit_p = (p - 0.4) / 0.6
            _draw_expanding_shockwave(painter, tx, ty, max_radius=85, p=hit_p,
                                     color=(60, 180, 255), alpha=alpha, aspect=0.5, rings=2)
            _draw_physics_particles(painter, tx, ty, hit_p, count=14,
                                    color=(120, 210, 255), alpha=alpha, seed=88,
                                    spread_x=60.0, spread_y=35.0, gravity=40.0, upward=False)
        return True
    elif eff_name == "energy_blast":
        # 能量爆發：超高能貫穿離子光束
        bw = int(28 * math.sin(p * math.pi))
        painter.setPen(Qt.NoPen)
        painter.fillRect(QRect(int(cx), int(cy - bw // 2), int(tx - cx + 50), bw), QColor(80, 180, 255, int(alpha * 0.85)))
        return True
    elif eff_name == "power_unity":
        # 能量驅動：能量光球匯聚引爆
        _draw_starburst(painter, cx, cy - 10, int(20 + 35 * p), QColor(255, 255, 255, alpha), QColor(60, 140, 255, alpha))
        return True
    elif eff_name == "super_transform":
        # 傳奇突擊：鬥神霸氣金光昇華
        painter.setPen(QPen(QColor(255, 215, 80, alpha), 4))
        painter.drawLine(QPointF(cx, cy + 20), QPointF(cx, cy - 60))

    # =========================================================================
    # 14. 槍神 (Corsair)
    # =========================================================================
        return True
    elif eff_name == "serpent_screw_wave":
        # 海龍迴旋：藍白水龍盤旋環繞衝撞
        s_rad = int(32 + 10 * math.sin(p * math.pi))
        painter.setPen(QPen(QColor(80, 180, 255, alpha), 4))
        painter.drawArc(QRect(int(tx - s_rad), int(ty - 16), s_rad * 2, 32),
                        int(p * 720 * 16), 180 * 16)
        # 加入水龍綋轉衝擊光晕
        _draw_bloom_line(painter, (tx - s_rad, ty), (tx + s_rad, ty),
                         base_width=6, color=(60, 160, 255), alpha=int(alpha * 0.55), core_white=False)
        if p > 0.5:
            hit_p = (p - 0.5) / 0.5
            _draw_expanding_shockwave(painter, tx, ty, max_radius=55, p=hit_p,
                                     color=(80, 200, 255), alpha=alpha, aspect=0.4, rings=2)
        return True
    elif eff_name == "nautilus_battleship_strike":
        # 諾特勒斯號神威：巨型主力戰艦黑影掠過天際投射天火
        painter.fillRect(QRect(0, 0, int(tx * 2), 60), QColor(30, 40, 70, int(alpha * 0.6)))
        for ni in range(5):
            nx = tx + (ni - 2) * 35
            painter.setPen(QPen(QColor(255, 120, 40, alpha), 4))
            painter.drawLine(QPointF(nx, 30), QPointF(nx, ty))
        return True
    elif eff_name == "time_leap_aura":
        # 時間置換：時鐘齒輪魔法光環在腳下轉動
        painter.setPen(QPen(QColor(140, 210, 255, alpha), 2))
        painter.drawEllipse(QPointF(cx, cy + 10), 36, 16)
        painter.drawLine(QPointF(cx, cy + 10), QPointF(cx + math.cos(rot_angle * 0.05) * 20, (cy + 10) + math.sin(rot_angle * 0.05) * 8))

    # =========================================================================
    # 17. 槍神新增技能 (Corsair 6~8)
    # =========================================================================
        return True
    elif eff_name == "rapid_fire":
        # 迅速射擊：雙槍火舌與飛濣彈殼 + 枕口閃焊
        for i in range(5):
            cur_p = min(1.0, p * 1.5 + i * 0.1)
            bullet_x = cx + (tx - cx) * cur_p
            # 改用 bloom line 更有光暈拖尾感
            _draw_bloom_line(painter, (bullet_x - 18, ty + (i - 2) * 5), (bullet_x, ty + (i - 2) * 5),
                             base_width=3, color=(255, 210, 50), alpha=alpha, core_white=True)
        # 槍口閃光（在槍口付近閃裂）
        flash_alpha = int(alpha * (0.5 + 0.5 * math.sin(p * math.pi * 6)))
        _draw_starburst(painter, cx + 15, cy, int(10 + 6 * math.sin(p * math.pi * 4)),
                        QColor(255, 255, 200, flash_alpha), QColor(255, 180, 50, flash_alpha))
        return True
    elif eff_name == "broadside":
        # 全艦開火：戰艦艇側砲門火砲齊射 + 炸炸炸
        for i in range(3):
            fy = ty - 25 + i * 25
            # 拋物線飛行
            can_x = cx + (tx - cx) * min(1.0, p * 1.6 + i * 0.08)
            _draw_bloom_line(painter, (cx + 20, fy), (can_x, fy),
                             base_width=5, color=(255, 110, 30), alpha=alpha, core_white=True)
            # 落地炸炸
            if p > 0.4 + i * 0.1:
                exp_p = (p - 0.4 - i * 0.1) / 0.5
                exp_p = min(1.0, exp_p)
                _draw_expanding_shockwave(painter, tx, fy, max_radius=40, p=exp_p,
                                         color=(255, 110, 30), alpha=alpha, aspect=0.65, rings=2)
                _draw_starburst(painter, tx, fy, int(12 + 10 * math.sin(exp_p * math.pi)),
                                QColor(255, 255, 200, alpha), QColor(255, 100, 30, alpha))
        return True
    elif eff_name == "target_lock":
        # 靶心瞄準：高精度紅色鎖定十字線
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 50, 50, alpha), 2))
        painter.drawEllipse(QPointF(tx, ty), 22, 22)
        painter.drawLine(QPointF(tx - 30, ty), QPointF(tx + 30, ty))
        painter.drawLine(QPointF(tx, ty - 30), QPointF(tx, ty + 30))
        return True
    elif eff_name == "death_trigger":
        # 死亡標靶：跳彈折射火花
        painter.setPen(QPen(QColor(255, 220, 80, alpha), 2))
        painter.drawLine(QPointF(tx - 25, ty - 25), QPointF(tx + 25, ty + 25))
        painter.drawLine(QPointF(tx - 25, ty + 25), QPointF(tx + 25, ty - 25))
        return True
    elif eff_name == "nautilus_barrage":
        # 召喚水手 / 諾特勒斯號：密集導彈群轟炸
        for i in range(6):
            mx = tx - 50 + i * 20
            my = (ty - 140) + 140 * min(1.0, (p * 2.0 + i * 0.1))
            painter.setBrush(QBrush(QColor(255, 80, 40, alpha)))
            painter.setPen(QPen(QColor(255, 240, 100, alpha), 1))
            painter.drawRoundedRect(QRect(int(mx - 4), int(my - 12), 8, 24), 2, 2)

    # =========================================================================
    # 15. 重砲指揮官 (Cannoneer)
    # =========================================================================
        return True
    elif eff_name == "eight_legs_cannon":
        # 章魚砲台：巨型重機械砲轟出破甲火球
        painter.setBrush(QBrush(QColor(255, 110, 40, alpha)))
        painter.setPen(QPen(QColor(255, 220, 120, alpha), 2))
        painter.drawEllipse(QPointF(tx, ty), 24, 24)
        _draw_starburst(painter, tx, ty, 20, QColor(255, 255, 255, alpha), QColor(255, 90, 30, alpha))
        return True
    elif eff_name == "pirate_flag_aura":
        # 海盜旗幟：身旁插下飄揚的海盜骷髏戰旗
        painter.setPen(QPen(QColor(180, 140, 80, alpha), 3))
        painter.drawLine(QPointF(cx - 25, cy + 15), QPointF(cx - 25, cy - 35))
        painter.setBrush(QBrush(QColor(255, 60, 40, alpha)))
        painter.drawRect(int(cx - 24), int(cy - 35), 24, 16)
        return True
    elif eff_name == "bullet_barrage_spit":
        # 狂暴射擊：漫天彈殼與火光彈道掃射
        for bi in range(6):
            bx = cx + (tx - cx) * min(1.0, p * 1.5 + bi * 0.08)
            by = (cy - 15) + (ty - (cy - 15)) * min(1.0, p * 1.5 + bi * 0.08) + math.sin(bi * 2.0) * 12
            painter.setPen(QPen(QColor(255, 200, 60, alpha), 2.5))
            painter.drawLine(QPointF(bx - 12, by), QPointF(bx, by))

    # =========================================================================
    # 18. 重砲指揮官新增技能 (Cannoneer 6~8)
    # =========================================================================
        return True
    elif eff_name == "cannon_barrage":
        # 【加農砲連擊】：加農巨砲 4 連重轟！穿膛重彈核融尾跡 + 砲口高壓錐形爆風 + 連環破裂衝擊波 + 24 顆高溫炸裂彈片
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        
        # 1. 砲口高壓錐形排氣爆風 (Ribbon Mesh)
        _draw_ribbon_slash(painter, cx, cy, start_deg=-25, sweep_deg=50,
                           inner_r=15, outer_r=55, color=(255, 120, 30), alpha=int(alpha * 0.8), core_white=True)

        # 2. 4 發重加農砲彈與核融尾跡光線 (Bloom Lines)
        for i in range(4):
            delay = i * 0.12
            cur_p = max(0.0, min(1.0, (p - delay) / 0.6))
            if cur_p > 0:
                bx = cx + (tx - cx) * cur_p
                by = cy + (ty - cy) * cur_p + (i - 1.5) * 8
                _draw_bloom_line(painter, (bx - 25, by), (bx, by), base_width=6,
                                 color=(255, 140, 40), alpha=alpha, core_white=True)
                _draw_starburst(painter, bx, by, 8, QColor(255, 255, 255, alpha), QColor(255, 100, 30, alpha))

        # 3. 目標連環衝擊波環
        _draw_expanding_shockwave(painter, tx, ty, max_radius=85, p=p,
                                 color=(255, 140, 40), alpha=alpha, aspect=0.75, rings=3)

        # 4. 24 顆炸裂彈片與火花 (Physics Embers)
        _draw_physics_particles(painter, tx, ty, p, count=24,
                                color=(255, 190, 60), alpha=alpha, seed=432,
                                spread_x=80.0, spread_y=60.0, gravity=75.0, upward=False)
        _draw_starburst(painter, tx, ty, int(24 + 28 * math.sin(p * math.pi)),
                        QColor(255, 255, 240, alpha), QColor(255, 90, 20, alpha))
        return True
    elif eff_name == "icbm_missile":
        # 【巨型火箭砲 (ICBM 核彈)】：洲際重型火箭彈俯衝天降！核爆級蘑菇雲擴散巨環 + 雙向爆風熱浪 + 地面焦痕 + 30 顆金橙火球噴泉
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        my = (ty - 160) + 160 * min(1.0, p * 2.2)

        # 1. 俯衝火箭彈體與推進白熾尾焰 (Bloom Line)
        if p < 0.5:
            _draw_bloom_line(painter, (tx, my - 60), (tx, my), base_width=12,
                             color=(255, 90, 20), alpha=alpha, core_white=True)

        # 2. 砸地核爆蘑菇雲與雙向爆風熱浪 (Ribbon Mesh)
        if p >= 0.35:
            n_p = (p - 0.35) / 0.65
            # 蘑菇雲半球高溫弧面
            _draw_ribbon_slash(painter, tx, ty - 20, start_deg=-150, sweep_deg=120,
                               inner_r=25, outer_r=75, color=(255, 100, 20), alpha=int(alpha * 0.85), core_white=True)
            _draw_ribbon_slash(painter, tx, ty - 20, start_deg=30, sweep_deg=120,
                               inner_r=25, outer_r=75, color=(255, 150, 30), alpha=int(alpha * 0.85), core_white=True)

            # 3. 地面雙層核爆衝擊破裂巨環
            _draw_expanding_shockwave(painter, tx, ty + 12, max_radius=125, p=n_p,
                                     color=(255, 110, 20), alpha=alpha, aspect=0.4, rings=2)

            # 4. 地面高熱焦痕 (Bloom Line)
            _draw_bloom_line(painter, (tx - 55, ty + 12), (tx + 55, ty + 12), base_width=6,
                             color=(255, 160, 40), alpha=int(alpha * (1.0 - n_p * 0.5)), core_white=True)

            # 5. 30 顆密集高溫彈片與金橙火球噴泉 (Physics Embers)
            _draw_physics_particles(painter, tx, ty + 10, n_p, count=30,
                                    color=(255, 180, 50), alpha=alpha, seed=101,
                                    spread_x=95.0, spread_y=70.0, gravity=80.0, upward=False)
            _draw_starburst(painter, tx, ty - 20, int(30 + 35 * math.sin(n_p * math.pi)),
                            QColor(255, 255, 240, alpha), QColor(255, 80, 20, alpha))
        return True
    elif eff_name == "cannon_bazooka":
        # 【加農砲火箭 (重砲爆轟)】：超音速穿膛火箭長程轟射！巨型重砲核融貫穿火軸 + 雙側音爆熱浪流光錐 + 雙層衝擊巨環 + 22 顆火花
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        arr_x = cx + (tx - cx) * min(1.0, p * 1.4)
        arr_y = cy + (ty - cy) * min(1.0, p * 1.4)

        # 1. 貫穿全屏的重砲長程穿膛核融火軸 (Bloom Line)
        _draw_bloom_line(painter, (cx, cy), (arr_x, arr_y), base_width=13,
                         color=(255, 110, 30), alpha=alpha, core_white=True)

        # 2. 兩側向後高速噴湧的音爆帶狀流光錐 (Ribbon Mesh)
        _draw_ribbon_slash(painter, arr_x - 15, arr_y, start_deg=-150, sweep_deg=50,
                           inner_r=12, outer_r=48, color=(255, 160, 40), alpha=int(alpha * 0.8), core_white=True)
        _draw_ribbon_slash(painter, arr_x - 15, arr_y, start_deg=100, sweep_deg=50,
                           inner_r=12, outer_r=48, color=(255, 160, 40), alpha=int(alpha * 0.8), core_white=True)

        # 3. 目標雙層衝擊巨環
        if p > 0.4:
            _draw_expanding_shockwave(painter, tx, ty, max_radius=95, p=(p - 0.4) / 0.6,
                                     color=(255, 130, 30), alpha=alpha, aspect=0.75, rings=2)
            _draw_physics_particles(painter, tx, ty, (p - 0.4) / 0.6, count=22,
                                    color=(255, 180, 50), alpha=alpha, seed=654,
                                    spread_x=75.0, spread_y=60.0, gravity=80.0, upward=False)
            _draw_starburst(painter, tx, ty, 24, QColor(255, 255, 240, alpha), QColor(255, 80, 20, alpha))
        return True
    elif eff_name == "rolling_rainbow":
        # 【滾動彩虹 (七彩狂怒激光)】：彩虹旋轉加農重砲狂怒連擊！多色彩虹旋轉帶狀風暴 + 貫穿稜鏡核融光束 + 3環彩虹衝擊巨環 + 28 顆彩虹星屑噴泉
        painter.setCompositionMode(QPainter.CompositionMode_Plus)

        # 1. 砲口旋轉彩虹稜鏡能量環 (施法者處)
        _draw_magic_circle(painter, cx, cy, int(26 + 6 * math.sin(p * math.pi)), rot_angle * 0.1, QColor(255, 215, 80, alpha))
        _draw_starburst(painter, cx, cy, int(18 + 10 * math.sin(p * math.pi)),
                        QColor(255, 255, 255, alpha), QColor(255, 120, 50, alpha))

        # 2. 貫穿戰場的白熾核融稜鏡加農激光束 (Bloom Line)
        _draw_bloom_line(painter, (cx, cy), (tx, ty), base_width=14,
                         color=(255, 230, 80), alpha=alpha, core_white=True)

        # 3. 旋轉彩虹帶狀風暴切削 (Ribbon Mesh - 七彩動態旋轉弧光)
        rainbow_hues = [
            (255, 60, 80),   # 狂怒赤紅
            (255, 150, 40),  # 太陽橙金
            (255, 230, 50),  # 熾金輝光
            (60, 240, 120),  # 翡翠碧綠
            (50, 210, 255),  # 蒼藍蒼空
            (200, 80, 255),  # 幻紫靈光
        ]
        spin_base = (rot_angle * 1.5) % 360
        for ri, r_col in enumerate(rainbow_hues):
            arc_offset = ri * 60
            _draw_ribbon_slash(painter, tx, ty,
                               start_deg=(spin_base + arc_offset) % 360,
                               sweep_deg=85,
                               inner_r=22 + (ri % 3) * 12,
                               outer_r=58 + (ri % 3) * 18,
                               color=r_col, alpha=int(alpha * 0.8), core_white=True)

        # 4. 目標命中點 3 重彩虹擴散衝擊巨環
        _draw_expanding_shockwave(painter, tx, ty, max_radius=110, p=p,
                                 color=(255, 210, 70), alpha=alpha, aspect=0.75, rings=3)

        # 5. 28 顆繽紛彩虹高能光子微粒噴泉 (Physics Embers)
        _draw_physics_particles(painter, tx, ty, p, count=28,
                                color=(255, 235, 100), alpha=alpha, seed=777,
                                spread_x=85.0, spread_y=65.0, gravity=70.0, upward=False)
        _draw_starburst(painter, tx, ty, int(30 + 35 * math.sin(p * math.pi)),
                        QColor(255, 255, 255, alpha), QColor(255, 140, 40, alpha))
        return True
    elif eff_name == "monkey_militia":
        # 【百寶猴箱 (猴子援軍)】：召喚猴子砲兵隊投彈支援！3 枚迫擊高爆彈拋物線投射 + 目標連環小型爆破 + 20 顆煙火火屑
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        
        # 1. 施法者身側砲兵支援陣地
        _draw_magic_circle(painter, cx + 18, cy + 12, int(28 + 6 * math.sin(p * math.pi)), rot_angle * 0.06, QColor(255, 170, 70, alpha))

        # 2. 3 枚迫擊砲彈拋物線飛越 (Bloom Lines)
        for mi in range(3):
            m_delay = mi * 0.12
            cur_mp = max(0.0, min(1.0, (p - m_delay) / 0.6))
            if cur_mp > 0:
                mx = (cx + 20) + (tx - (cx + 20)) * cur_mp
                arc_h = math.sin(cur_mp * math.pi) * 65
                my = cy + (ty - cy) * cur_mp - arc_h
                _draw_bloom_line(painter, (mx - 15, my + 6), (mx, my), base_width=4,
                                 color=(255, 180, 50), alpha=alpha, core_white=True)
                _draw_starburst(painter, mx, my, 7, QColor(255, 255, 255, alpha), QColor(255, 140, 30, alpha))

        # 3. 落地 3 連小型爆破波環
        if p > 0.4:
            exp_p = (p - 0.4) / 0.6
            for mi in range(3):
                ox = tx - 30 + mi * 30
                _draw_expanding_shockwave(painter, ox, ty, max_radius=55, p=exp_p,
                                         color=(255, 150, 40), alpha=alpha, aspect=0.7, rings=2)
            _draw_physics_particles(painter, tx, ty, exp_p, count=20,
                                    color=(255, 200, 70), alpha=alpha, seed=321,
                                    spread_x=70.0, spread_y=50.0, gravity=65.0, upward=False)
            _draw_starburst(painter, tx, ty, 22, QColor(255, 255, 240, alpha), QColor(255, 100, 30, alpha))
        return True

    # =========================================================================
    # 16. 聖魂劍士 (Dawn Warrior)
    # =========================================================================
        return True
    elif eff_name == "poolmaker_artillery":
        # 【砲擊支援】：呼叫砲兵陣地天降地毯式轟炸！5 枚高爆巨砲彈呼嘯俯衝 + 連環落點衝擊巨環 + 26 顆熔岩碎屑噴泉
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        
        # 1. 5 枚迫擊砲彈自高空呼嘯俯衝 (Bloom Lines)
        for ai in range(5):
            a_delay = ai * 0.1
            a_p = max(0.0, min(1.0, (p - a_delay) / 0.6))
            if a_p > 0:
                ax = tx - 45 + ai * 22
                ay_drop = (ty - 130) + 130 * a_p
                _draw_bloom_line(painter, (ax - 8, ay_drop - 30), (ax, ay_drop), base_width=5,
                                 color=(255, 120, 30), alpha=alpha, core_white=True)

        # 2. 地面連環落點衝擊波
        if p > 0.35:
            imp_p = (p - 0.35) / 0.65
            _draw_expanding_shockwave(painter, tx, ty + 8, max_radius=90, p=imp_p,
                                     color=(255, 140, 30), alpha=alpha, aspect=0.45, rings=2)
            _draw_physics_particles(painter, tx, ty + 8, imp_p, count=26,
                                    color=(255, 180, 50), alpha=alpha, seed=543,
                                    spread_x=85.0, spread_y=60.0, gravity=80.0, upward=False)
            _draw_starburst(painter, tx, ty, 22, QColor(255, 255, 240, alpha), QColor(255, 90, 20, alpha))
        return True
    elif eff_name == "pirate_spirit_aura":
        # 【海盜精神】：激發無畏加農水手豪情！腳底金色航海羅盤法陣 + 雙側旋轉海盜錨流光 + 貫天豪氣金光 + 20 顆升騰戰意火花
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        
        # 1. 腳底航海羅盤金色法陣
        _draw_magic_circle(painter, cx, cy + 14, int(36 + 8 * math.sin(p * math.pi)), rot_angle * 0.05, QColor(255, 180, 50, alpha))

        # 2. 雙側海盜金錨流光帶 (Ribbon Mesh)
        deg_p = rot_angle * 0.08
        _draw_ribbon_slash(painter, cx, cy - 8, start_deg=deg_p - 40, sweep_deg=80,
                           inner_r=28, outer_r=44, color=(255, 200, 60), alpha=int(alpha * 0.75), core_white=True)
        _draw_ribbon_slash(painter, cx, cy - 8, start_deg=deg_p + 140, sweep_deg=80,
                           inner_r=28, outer_r=44, color=(255, 160, 40), alpha=int(alpha * 0.75), core_white=True)

        # 3. 貫天海盜豪情金曜光柱 (Bloom Line)
        _draw_bloom_line(painter, (cx, cy + 14), (cx, cy - 80), base_width=14,
                         color=(255, 190, 70), alpha=int(alpha * 0.75), core_white=True)

        # 4. 20 顆升騰火紅戰意火花粒子 (Physics Souls)
        _draw_physics_particles(painter, cx, cy + 10, p, count=20,
                                color=(255, 210, 80), alpha=alpha, seed=678,
                                spread_x=35.0, spread_y=65.0, gravity=20.0, upward=True)
        _draw_starburst(painter, cx, cy - 20, 18, QColor(255, 255, 255, alpha), QColor(255, 160, 40, alpha))
        return True
    elif eff_name == "cannon_overload_blast":
        # 【過載填裝 (核能過載)】：汽缸全壓過載！發射超載熾熱火核熔岩巨砲 + 雙向過載排氣帶狀流光 + 雙層核爆衝擊巨環 + 28 顆熔岩碎屑
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        
        # 1. 貫穿目標超載高壓核融火線 (Bloom Line)
        _draw_bloom_line(painter, (cx, cy), (tx, ty), base_width=18,
                         color=(255, 60, 20), alpha=alpha, core_white=True)

        # 2. 雙向旋轉過載排氣帶狀流光 (Ribbon Mesh)
        deg_ov = rot_angle * 0.12
        _draw_ribbon_slash(painter, tx, ty, start_deg=deg_ov, sweep_deg=140,
                           inner_r=25, outer_r=85, color=(255, 120, 30), alpha=alpha, core_white=True)
        _draw_ribbon_slash(painter, tx, ty, start_deg=deg_ov + 180, sweep_deg=140,
                           inner_r=25, outer_r=85, color=(255, 120, 30), alpha=alpha, core_white=True)

        # 3. 核心熔岩核爆球
        rg = QRadialGradient(tx, ty, 38)
        rg.setColorAt(0.0, QColor(255, 255, 255, alpha))
        rg.setColorAt(0.4, QColor(255, 110, 30, int(alpha * 0.9)))
        rg.setColorAt(1.0, QColor(255, 40, 10, 0))
        painter.setBrush(QBrush(rg))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(tx, ty), 38, 38)

        # 4. 雙層核爆破裂巨環
        _draw_expanding_shockwave(painter, tx, ty, max_radius=110, p=p,
                                 color=(255, 100, 20), alpha=alpha, aspect=0.75, rings=2)

        # 5. 28 顆高溫熔岩碎屑與火花 (Physics Embers)
        _draw_physics_particles(painter, tx, ty, p, count=28,
                                color=(255, 170, 40), alpha=alpha, seed=876,
                                spread_x=90.0, spread_y=65.0, gravity=85.0, upward=False)
        _draw_starburst(painter, tx, ty, int(28 + 32 * math.sin(p * math.pi)),
                        QColor(255, 255, 240, alpha), QColor(255, 70, 20, alpha))
        return True

    # =========================================================================
    # 19. 聖魂劍士新增技能 (Dawn Warrior 6~8)
    # =========================================================================
        return True
    return False
