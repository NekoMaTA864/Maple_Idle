"""
新楓之谷 反抗軍 - 爆拳槍神 (Blaster) 技能特效模組
"""

import math
import random
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient, QRadialGradient
)
from vfx_core import (
    _draw_starburst, _draw_magic_circle, _draw_bloom_line,
    _draw_ribbon_slash, _draw_expanding_shockwave, _draw_physics_particles
)

BLASTER_EFFECTS = {
    "magnum_punch", "bunker_buster", "double_blast", "hurricane_blaster",
    "vulcan_punch", "shotgun_punch_blast", "ammo_overdrive_aura", "rocket_punch_propel"
}


def render_blaster_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty,
                       rot_angle=0.0, seed=0.0, fracture_lines=None, **kwargs) -> bool:
    if eff_name == "ammo_overdrive_aura":
        # 【彈藥充填】：彈夾全速上膛！背後 6 枚高能旋轉金屬彈巢 + 機械齒輪力場法陣 + 升騰高壓蒸氣火花
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        _draw_magic_circle(painter, cx, cy + 14, int(35 + 8 * math.sin(p * math.pi)), rot_angle * 0.04, QColor(255, 170, 50, alpha))

        rx = 34 + 6 * math.sin(p * math.pi)
        ry = 16 + 4 * math.sin(p * math.pi)
        for ai in range(6):
            aang = rot_angle * 0.08 + ai * (math.pi / 3)
            ax = cx + math.cos(aang) * rx
            ay = cy - 14 + math.sin(aang) * ry

            rg = QRadialGradient(ax, ay, 9)
            rg.setColorAt(0.0, QColor(255, 255, 255, alpha))
            rg.setColorAt(0.5, QColor(255, 180, 50, alpha))
            rg.setColorAt(1.0, QColor(255, 120, 20, 0))
            painter.setBrush(QBrush(rg))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(ax, ay), 9, 9)

            deg = math.degrees(aang)
            _draw_ribbon_slash(painter, cx, cy - 14, start_deg=deg - 45, sweep_deg=45,
                               inner_r=rx - 5, outer_r=rx + 5, color=(255, 160, 40), alpha=int(alpha * 0.5), core_white=False)

        _draw_bloom_line(painter, (cx - 24, cy - 14), (cx + 24, cy - 14), base_width=3,
                         color=(255, 200, 60), alpha=int(alpha * 0.7), core_white=True)

        _draw_expanding_shockwave(painter, cx, cy - 6, max_radius=52, p=p,
                                 color=(255, 180, 60), alpha=alpha, aspect=0.7, rings=1)
        _draw_physics_particles(painter, cx, cy + 10, p, count=16,
                                color=(255, 210, 80), alpha=alpha, seed=123,
                                spread_x=30.0, spread_y=60.0, gravity=25.0, upward=True)
        return True

    elif eff_name == "bunker_buster":
        # 【燃燒重拳】：聚能汽缸超壓引爆！過熱鋼樁核融直刺貫穿 + 雙向狂暴蒸氣排氣火舌 + 地動衝擊巨環 + 金屬碎屑熔岩噴泉
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        stake_w = int(22 * math.sin(p * math.pi))
        _draw_bloom_line(painter, (tx - 85, ty), (tx + 25, ty), base_width=max(4, stake_w),
                         color=(255, 80, 20), alpha=alpha, core_white=True)

        _draw_ribbon_slash(painter, tx - 30, ty, start_deg=-150, sweep_deg=70,
                           inner_r=20, outer_r=65, color=(255, 140, 30), alpha=int(alpha * 0.8), core_white=True)
        _draw_ribbon_slash(painter, tx - 30, ty, start_deg=80, sweep_deg=70,
                           inner_r=20, outer_r=65, color=(255, 140, 30), alpha=int(alpha * 0.8), core_white=True)

        _draw_expanding_shockwave(painter, tx, ty, max_radius=110, p=p,
                                 color=(255, 120, 30), alpha=alpha, aspect=0.7, rings=2)

        _draw_physics_particles(painter, tx, ty, p, count=28,
                                color=(255, 180, 40), alpha=alpha, seed=456,
                                spread_x=85.0, spread_y=65.0, gravity=90.0, upward=False)
        _draw_starburst(painter, tx, ty, int(26 + 32 * math.sin(p * math.pi)),
                        QColor(255, 255, 240, alpha), QColor(255, 90, 30, alpha))
        return True

    elif eff_name == "double_blast":
        # 【雙重重擊】：雙手巨砲 2 連破空轟鳴！雙向交錯帶狀錐形熱浪 + 雙管核融穿甲光柱 + 雙重衝擊波 + 噴射火花
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        _draw_ribbon_slash(painter, tx - 15, ty, start_deg=-135, sweep_deg=110,
                           inner_r=22, outer_r=68, color=(255, 120, 30), alpha=alpha, core_white=True)
        _draw_ribbon_slash(painter, tx + 15, ty, start_deg=25, sweep_deg=110,
                           inner_r=22, outer_r=68, color=(255, 170, 40), alpha=alpha, core_white=True)

        _draw_bloom_line(painter, (tx - 55, ty - 12), (tx + 25, ty - 12), base_width=6,
                         color=(255, 90, 20), alpha=alpha, core_white=True)
        _draw_bloom_line(painter, (tx - 55, ty + 12), (tx + 25, ty + 12), base_width=6,
                         color=(255, 140, 30), alpha=alpha, core_white=True)

        _draw_expanding_shockwave(painter, tx, ty, max_radius=85, p=p,
                                 color=(255, 150, 40), alpha=alpha, aspect=0.75, rings=2)

        _draw_physics_particles(painter, tx, ty, p, count=20,
                                color=(255, 190, 50), alpha=alpha, seed=234,
                                spread_x=70.0, spread_y=50.0, gravity=70.0, upward=False)
        _draw_starburst(painter, tx, ty, int(22 + 25 * math.sin(p * math.pi)),
                        QColor(255, 255, 240, alpha), QColor(255, 120, 30, alpha))
        return True

    elif eff_name == "hurricane_blaster":
        # 【旋風衝擊】：重裝連續 4 段旋轉極速重拳 + 360° 雙層帶狀火焰氣旋 + 連環爆裂衝擊波 + 旋轉飛舞火花
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        deg1 = rot_angle * 0.12
        _draw_ribbon_slash(painter, tx, ty, start_deg=deg1, sweep_deg=160,
                           inner_r=28, outer_r=75, color=(255, 110, 30), alpha=alpha, core_white=True)
        _draw_ribbon_slash(painter, tx, ty, start_deg=deg1 + 180, sweep_deg=160,
                           inner_r=35, outer_r=82, color=(255, 180, 50), alpha=int(alpha * 0.85), core_white=True)

        offsets = [(-20, -15, 20, 15), (20, -15, -20, 15), (0, -25, 0, 25), (-25, 0, 25, 0)]
        ox1, oy1, ox2, oy2 = offsets[int(p * 3.99)]
        _draw_bloom_line(painter, (tx + ox1, ty + oy1), (tx + ox2, ty + oy2), base_width=6,
                         color=(255, 200, 70), alpha=alpha, core_white=True)

        _draw_expanding_shockwave(painter, tx, ty, max_radius=88, p=p,
                                 color=(255, 140, 40), alpha=alpha, aspect=0.85, rings=3)

        _draw_physics_particles(painter, tx, ty, p, count=22,
                                color=(255, 190, 60), alpha=alpha, seed=345,
                                spread_x=75.0, spread_y=60.0, gravity=30.0, upward=False)
        _draw_starburst(painter, tx, ty, int(24 + 28 * math.sin(p * math.pi)),
                        QColor(255, 255, 240, alpha), QColor(255, 100, 30, alpha))
        return True

    elif eff_name == "magnum_punch":
        # 【重拳擺動】：左輪彈巢極速旋轉！高壓錐形核融火舌 + 破甲帶狀流光揮擊 + 衝擊波環 + 飛濺黃金彈殼
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        _draw_bloom_line(painter, (tx - 65, ty), (tx + 18, ty), base_width=10,
                         color=(255, 110, 30), alpha=alpha, core_white=True)

        _draw_ribbon_slash(painter, tx - 10, ty, start_deg=-120, sweep_deg=140,
                           inner_r=25, outer_r=70, color=(255, 160, 40), alpha=alpha, core_white=True)

        _draw_expanding_shockwave(painter, tx, ty, max_radius=78, p=p,
                                 color=(255, 130, 30), alpha=alpha, aspect=0.7, rings=2)

        _draw_physics_particles(painter, tx - 15, ty, p, count=20,
                                color=(255, 200, 60), alpha=alpha, seed=678,
                                spread_x=65.0, spread_y=55.0, gravity=80.0, upward=False)
        _draw_starburst(painter, tx, ty, int(22 + 26 * math.sin(p * math.pi)),
                        QColor(255, 255, 240, alpha), QColor(255, 120, 40, alpha))
        return True

    elif eff_name == "rocket_punch_propel":
        # 【火箭鐵拳】：汽缸火箭推進！超重裝鋼鐵重拳破空衝撞 + 尾部核融噴射尾焰 + 推進流光帶 + 撞擊衝擊巨環
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        r_prog = min(1.0, p * 1.5)
        rx = cx + (tx - cx) * r_prog
        ry = cy + (ty - cy) * r_prog

        _draw_bloom_line(painter, (rx - 45, ry), (rx, ry), base_width=12,
                         color=(255, 90, 20), alpha=alpha, core_white=True)

        _draw_ribbon_slash(painter, rx - 20, ry, start_deg=-150, sweep_deg=60,
                           inner_r=15, outer_r=45, color=(255, 140, 30), alpha=int(alpha * 0.75), core_white=True)
        _draw_ribbon_slash(painter, rx - 20, ry, start_deg=90, sweep_deg=60,
                           inner_r=15, outer_r=45, color=(255, 140, 30), alpha=int(alpha * 0.75), core_white=True)

        painter.save()
        painter.translate(rx, ry)
        fist_grad = QLinearGradient(-15, -12, 15, 12)
        fist_grad.setColorAt(0.0, QColor(255, 230, 150, alpha))
        fist_grad.setColorAt(0.5, QColor(255, 120, 30, alpha))
        fist_grad.setColorAt(1.0, QColor(40, 20, 10, alpha))
        painter.setBrush(QBrush(fist_grad))
        painter.setPen(QPen(QColor(255, 200, 80, alpha), 1.5))
        painter.drawRoundedRect(QRectF(-15, -12, 30, 24), 5, 5)
        painter.restore()

        if p > 0.4:
            _draw_expanding_shockwave(painter, tx, ty, max_radius=80, p=(p - 0.4) / 0.6,
                                     color=(255, 140, 40), alpha=alpha, aspect=0.75, rings=2)
            _draw_physics_particles(painter, tx, ty, (p - 0.4) / 0.6, count=20,
                                    color=(255, 180, 50), alpha=alpha, seed=789,
                                    spread_x=70.0, spread_y=55.0, gravity=75.0, upward=False)
        return True

    elif eff_name == "shotgun_punch_blast":
        # 【霰彈重拳】：零距離扣下擊錘重拳直轟！10 道扇形核融穿甲彈片 + 錐形爆裂熱浪 + 零距離衝擊巨環 + 金屬鐵屑飛濺
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        for si in range(10):
            sang = -0.55 + si * 0.12
            beam_len = 65 * math.sin(p * math.pi)
            sx = tx + math.cos(sang) * beam_len
            sy = ty + math.sin(sang) * beam_len
            _draw_bloom_line(painter, (tx - 15, ty), (sx, sy), base_width=3.5,
                             color=(255, 120, 30), alpha=alpha, core_white=True)

        _draw_ribbon_slash(painter, tx - 10, ty, start_deg=-35, sweep_deg=70,
                           inner_r=18, outer_r=62, color=(255, 160, 40), alpha=int(alpha * 0.8), core_white=True)

        _draw_expanding_shockwave(painter, tx, ty, max_radius=92, p=p,
                                 color=(255, 130, 30), alpha=alpha, aspect=0.8, rings=2)

        _draw_physics_particles(painter, tx, ty, p, count=26,
                                color=(255, 190, 50), alpha=alpha, seed=890,
                                spread_x=85.0, spread_y=60.0, gravity=85.0, upward=False)
        _draw_starburst(painter, tx, ty, int(24 + 28 * math.sin(p * math.pi)),
                        QColor(255, 255, 240, alpha), QColor(255, 100, 30, alpha))
        return True

    elif eff_name == "vulcan_punch":
        # 【火神衝擊】：火藥極速過載運轉！加特林重拳狂轟 + 8 道交錯核融火線 + 連環爆裂衝擊波 + 高溫火花噴泉
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        _draw_magic_circle(painter, cx, cy + 12, int(30 + 8 * math.sin(p * math.pi)), rot_angle * 0.06, QColor(255, 140, 40, int(alpha * 0.7)))

        for vi in range(8):
            v_seed = vi * 37
            rnd = random.Random(v_seed + int(p * 25.0))
            vx1 = tx + rnd.uniform(-40, -10)
            vy1 = ty + rnd.uniform(-25, 25)
            vx2 = tx + rnd.uniform(10, 40)
            vy2 = ty + rnd.uniform(-25, 25)
            _draw_bloom_line(painter, (vx1, vy1), (vx2, vy2), base_width=4.5,
                             color=(255, 120, 30), alpha=alpha, core_white=True)

        deg_v = rot_angle * 0.15
        _draw_ribbon_slash(painter, tx, ty, start_deg=deg_v, sweep_deg=100,
                           inner_r=20, outer_r=65, color=(255, 160, 40), alpha=int(alpha * 0.75), core_white=True)

        _draw_expanding_shockwave(painter, tx, ty, max_radius=85, p=p,
                                 color=(255, 130, 30), alpha=alpha, aspect=0.75, rings=3)
        _draw_physics_particles(painter, tx, ty, p, count=24,
                                color=(255, 190, 50), alpha=alpha, seed=999,
                                spread_x=80.0, spread_y=60.0, gravity=80.0, upward=False)
        _draw_starburst(painter, tx, ty, int(22 + 28 * math.sin(p * math.pi)),
                        QColor(255, 255, 240, alpha), QColor(255, 90, 20, alpha))
        return True

    return False

