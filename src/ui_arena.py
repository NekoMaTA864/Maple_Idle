"""
《新楓之谷：放置遠征隊》QPainter 戰鬥動態畫布元件 (ui_arena.py)
"""
import math
import time
import random
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect, QRectF, QPoint, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QRadialGradient
)
from settings import (
    COLOR_HP_RED, COLOR_ACTION_BAR, COLOR_SHIELD_BLUE, COLOR_GOLD,
    COLOR_HEAL_GREEN, COLOR_BOSS_PURPLE
)
from classes import ALL_CLASSES
from vfx_renderer import render_maple_vfx, render_aura_halo

class CombatArenaWidget(QWidget):
    """即時動態繪製特效、螢幕震動、受擊白閃與楓之谷風格跳字 (硬體抗鋸齒)"""
    def __init__(self, combat_mgr, parent=None):
        super().__init__(parent)
        self.combat_mgr = combat_mgr
        self.setMinimumHeight(440)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        # 螢幕震動、打擊反饋與遊戲內部動畫時鐘
        self.shake_x = 0
        self.shake_y = 0
        self.shake_timer = 0.0
        self.shake_power = 0.0
        self.flash_timer = 0.0
        self.global_rot_angle = 0.0
        self.game_time = 0.0

    def trigger_shake(self, power=3.5, duration=0.22):
        self.shake_power = power
        self.shake_timer = duration

    def trigger_flash(self, duration=0.08):
        self.flash_timer = duration

    def update_vfx_timer(self, dt):
        self.game_time += dt
        self.global_rot_angle += 720.0 * dt
        if self.shake_timer > 0:
            self.shake_timer = max(0.0, self.shake_timer - dt)
            ratio = self.shake_timer / 0.22
            self.shake_x = random.randint(-int(self.shake_power * ratio), int(self.shake_power * ratio))
            self.shake_y = random.randint(-int(self.shake_power * ratio), int(self.shake_power * ratio))
        else:
            self.shake_x = 0
            self.shake_y = 0

        if self.flash_timer > 0:
            self.flash_timer = max(0.0, self.flash_timer - dt)

    def _get_canvas_monster_pos(self, idx, total, w, y=75):
        if total <= 1:
            ratios = [0.50]
        elif total == 2:
            ratios = [0.38, 0.62]
        elif total == 3:
            ratios = [0.26, 0.50, 0.74]
        elif total == 4:
            ratios = [0.18, 0.39, 0.61, 0.82]
        else:
            ratios = [0.14, 0.32, 0.50, 0.68, 0.86]
        r = ratios[idx] if idx < len(ratios) else 0.5
        return QPoint(int(w * r), y)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            self._paint_event_impl(painter, event)
        finally:
            if painter.isActive():
                painter.end()

    def _paint_event_impl(self, painter, event):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        w = self.width()
        h = self.height()

        # 應用螢幕震動位移
        if self.shake_timer > 0:
            painter.translate(self.shake_x, self.shake_y)

        # 1. 戰鬥場景大畫布底圖與氛圍背景
        grad_bg = QLinearGradient(0, 0, 0, h)
        grad_bg.setColorAt(0.0, QColor(13, 17, 26))
        grad_bg.setColorAt(1.0, QColor(22, 28, 42))
        painter.fillRect(QRect(0, 0, w, h), QBrush(grad_bg))
        painter.setPen(QPen(QColor(42, 54, 76), 1))
        painter.drawRoundedRect(QRect(0, 0, w - 1, h - 1), 6, 6)

        # 頂部戰場資訊列 (區域名稱、層數與 ARC / AUT 壓制/增傷標籤)
        zone = self.combat_mgr.get_current_zone()
        arc_req = zone.get("arc_req", 0)
        aut_req = zone.get("aut_req", 0)
        player = self.combat_mgr.player

        painter.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
        farm_tag = " [🔄 循環刷怪中]" if getattr(self.combat_mgr, "repeat_current_zone", False) else ""
        z_title = f"{zone['name']}  [第 {self.combat_mgr.current_floor}/{self.combat_mgr.max_floors} 層]{farm_tag}"
        painter.setPen(QColor(220, 230, 245))
        painter.drawText(QRect(12, 8, 360, 20), Qt.AlignLeft, z_title)

        if arc_req > 0:
            p_arc = player.get_total_arc()
            is_overpower = p_arc >= int(arc_req * 1.5)
            is_qualified = p_arc >= arc_req
            if is_overpower:
                status_txt = f"★ ARC: {p_arc}/{arc_req} (1.5x 增傷壓制 | 減傷為 1 點)"
                tag_col = QColor(255, 215, 0)
            elif is_qualified:
                status_txt = f"ARC: {p_arc}/{arc_req} (達標 100% 輸出)"
                tag_col = QColor(100, 220, 255)
            else:
                ratio_pct = max(10, int((p_arc / arc_req) * 100))
                status_txt = f"ARC: {p_arc}/{arc_req} (不足！傷害衰減至 {ratio_pct}%)"
                tag_col = QColor(255, 100, 100)
            painter.setPen(tag_col)
            painter.drawText(QRect(w - 380, 8, 368, 20), Qt.AlignRight, status_txt)
        elif aut_req > 0:
            p_aut = player.get_total_aut()
            is_qualified = p_aut >= aut_req
            if is_qualified:
                status_txt = f"★ AUT: {p_aut}/{aut_req} (原初達標 100%)"
                tag_col = QColor(255, 180, 50)
            else:
                status_txt = f"AUT: {p_aut}/{aut_req} (未達標！嚴重減傷)"
                tag_col = QColor(255, 90, 90)
            painter.setPen(tag_col)
            painter.drawText(QRect(w - 380, 8, 368, 20), Qt.AlignRight, status_txt)

        # 戰場地面基準線 (動態根據畫布高度拉開 Y 軸)
        ground_y = int(h * 0.82)
        painter.setPen(QPen(QColor(52, 70, 102, 160), 1.5))
        painter.drawLine(10, ground_y, w - 10, ground_y)

        # 隊伍席位中心 (7 人陣型：左翼 3 夥伴 + 中央 👑 核心主角 + 右翼 3 夥伴)
        slot_ratio_map = {
            0: 0.50,  # 👑 核心主角 (居中王者站位)
            1: 0.36,  # ⚔️ 夥伴 1
            2: 0.23,  # 🛡️ 夥伴 2
            3: 0.10,  # 🏹 夥伴 3
            4: 0.64,  # 🔮 夥伴 4
            5: 0.77,  # 🗡️ 夥伴 5
            6: 0.90,  # 💣 夥伴 6
        }
        team_len = len(self.combat_mgr.player.team)
        slot_positions = [QPoint(int(w * slot_ratio_map.get(idx, 0.5)), int(h * 0.78)) for idx in range(team_len)]

        slot_colors = [
            QColor(255, 215, 0),    # 👑 席位0 主角 (耀眼純金)
            QColor(49, 130, 206),   # 席位1 藍
            QColor(128, 90, 213),   # 席位2 紫
            QColor(56, 161, 105),   # 席位3 綠
            QColor(221, 107, 32),   # 席位4 橙
            QColor(214, 158, 46),   # 席位5 金棕
            QColor(237, 100, 166),  # 席位6 粉紅
        ]

        # 隊友腳下光環平台 (主角具備更大且耀眼的金色光環)
        for idx, sp in enumerate(slot_positions):
            col = slot_colors[idx % len(slot_colors)]
            radius = 52 if idx == 0 else 38
            rg_s = QRadialGradient(sp.x(), sp.y() + 18, radius)
            rg_s.setColorAt(0.0, QColor(col.red(), col.green(), col.blue(), 65 if idx == 0 else 40))
            rg_s.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(rg_s))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(sp.x(), sp.y() + 18), radius, 14 if idx == 0 else 11)

        # 繪製隊員標識 (主角冠冕與標籤)
        for idx, sp in enumerate(slot_positions):
            if idx < len(self.combat_mgr.player.team):
                m_member = self.combat_mgr.player.team[idx]
                if idx == 0:
                    f_lbl = f"👑 {m_member.name}"
                    b_w, b_h = 76, 22
                else:
                    f_lbl = f"[{idx}] {m_member.name[:3]}"
                    b_w, b_h = 58, 20
            else:
                f_lbl = f"[{idx}]"
                b_w, b_h = 50, 20

            f_col = slot_colors[idx % len(slot_colors)]
            painter.setBrush(QBrush(f_col))
            painter.setPen(QPen(QColor(255, 255, 255, 220 if idx == 0 else 180), 1.5 if idx == 0 else 1))
            painter.drawRoundedRect(QRectF(sp.x() - b_w // 2, sp.y() - b_h // 2, b_w, b_h), 5 if idx == 0 else 4, 5 if idx == 0 else 4)
            painter.setFont(QFont("Microsoft YaHei UI", 8 if idx == 0 else 7, QFont.Bold))
            painter.setPen(QColor(20, 20, 30) if idx == 0 else QColor(255, 255, 255))
            painter.drawText(QRectF(sp.x() - b_w // 2, sp.y() - b_h // 2, b_w, b_h), Qt.AlignCenter, f_lbl)

        # 繪製怪物群體 (支援 1~5 隻多怪物波次、菁英怪光芒與專屬即時血條，位置隨畫布動態自適應)
        monsters = self.combat_mgr.monsters if self.combat_mgr.monsters else ([self.combat_mgr.monster] if self.combat_mgr.monster else [])
        total_m = max(1, len(monsters))
        monster_base_y = max(70, int(h * 0.25))

        for idx, m in enumerate(monsters):
            m_pos = self._get_canvas_monster_pos(idx, total_m, w, y=monster_base_y)

            # 怪物腳底光環
            is_elite = getattr(m, "is_elite", False)
            rg_m = QRadialGradient(m_pos.x(), m_pos.y() + 32, 55 if m.is_boss else 45)
            if m.is_boss:
                rg_m.setColorAt(0.0, QColor(180, 40, 200, 55))
            elif is_elite:
                rg_m.setColorAt(0.0, QColor(255, 200, 40, 60))
            else:
                rg_m.setColorAt(0.0, QColor(220, 60, 60, 40))
            rg_m.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(rg_m))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(m_pos.x(), m_pos.y() + 32), 55 if m.is_boss else 45, 14)

            if m.is_alive:
                m_bob = math.sin(self.game_time * 3.5 + idx * 0.9) * 3.0
                m_draw_y = m_pos.y() + m_bob

                # 怪物徽記
                if m.is_boss:
                    b_w, b_h = 86, 26
                    b_col = QColor(*COLOR_BOSS_PURPLE)
                    m_text = f"[BOSS] {m.name}"
                elif is_elite:
                    b_w, b_h = 84, 24
                    b_col = QColor(214, 158, 46)
                    m_text = f"[菁英] {m.name}"
                else:
                    b_w, b_h = 68, 20
                    b_col = QColor(229, 62, 62)
                    m_text = m.name[:4]

                painter.setBrush(QBrush(b_col))
                painter.setPen(QPen(QColor(255, 255, 255, 200), 1))
                painter.drawRoundedRect(QRectF(m_pos.x() - b_w // 2, m_draw_y - b_h // 2, b_w, b_h), 4, 4)
                painter.setFont(QFont("Microsoft YaHei UI", 8 if not m.is_boss else 9, QFont.Bold))
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(QRectF(m_pos.x() - b_w // 2, m_draw_y - b_h // 2, b_w, b_h), Qt.AlignCenter, m_text)

                # 頭頂血條 (即時微型血條)
                bar_w = 64 if not m.is_boss else 86
                bar_x = m_pos.x() - bar_w // 2
                bar_y = m_draw_y - b_h // 2 - 8
                painter.setBrush(QBrush(QColor(20, 24, 33, 200)))
                painter.setPen(Qt.NoPen)
                painter.drawRect(bar_x, bar_y, bar_w, 4)
                hp_ratio = max(0.0, min(1.0, m.hp / max(1, m.max_hp)))
                painter.setBrush(QBrush(QColor(229, 62, 62)))
                painter.drawRect(bar_x, bar_y, int(bar_w * hp_ratio), 4)
            else:
                # 怪物已陣亡：繪製半透明 [討伐]
                painter.setFont(QFont("Microsoft YaHei UI", 8, QFont.Normal))
                painter.setPen(QColor(100, 116, 139, 140))
                painter.drawText(QRectF(m_pos.x() - 35, m_pos.y() - 10, 70, 20), Qt.AlignCenter, "[已殲滅]")

        # 繪製主隊長/隊員常駐增益光環 (Buff Aura Halo)
        if hasattr(self.combat_mgr.player, "team_buffs"):
            for bid, b_info in self.combat_mgr.player.team_buffs.items():
                if b_info.get("timer", 0) > 0:
                    b_type = b_info.get("type", "atk")
                    b_timer = b_info.get("timer", 0)
                    b_max = b_info.get("max_timer", 8.0)
                    for s_idx, sp in enumerate(slot_positions):
                        render_aura_halo(
                            painter, sp.x(), sp.y() + 5,
                            buff_type=b_type,
                            buff_timer=b_timer,
                            max_timer=b_max,
                            rot_angle=self.global_rot_angle,
                            game_time=self.game_time
                        )

        # 全螢幕大招暗角黑幕 (Vignette)
        vfx_list = self.combat_mgr.vfx_mgr.effects
        has_screen_ultimate = any(eff.kind in ["holy", "aoe_beam", "dimension_rift", "dark_genesis_thunder"] and eff.progress < 0.7 for eff in vfx_list)
        if has_screen_ultimate:
            painter.fillRect(QRect(0, 0, w, h), QColor(0, 0, 0, 120))

        # 繪製高度差異化戰場視覺特效 (Visual Effects)
        for eff in vfx_list:
            p = eff.progress
            is_target_monster = (eff.target_y < 160 or getattr(eff, 'target_monster_idx', None) is not None)
            if is_target_monster:
                t_midx = getattr(eff, 'target_monster_idx', None)
                if t_midx is not None:
                    m_pos = self._get_canvas_monster_pos(t_midx, total_m, w, y=monster_base_y)
                    tx = m_pos.x()
                    ty = m_pos.y()
                elif hasattr(eff, 'target_x') and eff.target_x > 0:
                    tx = int(eff.target_x * (w / 1140.0))
                    ty = monster_base_y
                else:
                    tx = w // 2
                    ty = monster_base_y
            else:
                t_slot = getattr(eff, 'target_slot', None)
                if t_slot is not None and 0 <= t_slot < len(slot_positions):
                    tx = slot_positions[t_slot].x()
                    ty = slot_positions[t_slot].y()
                else:
                    tx = slot_positions[0].x()
                    ty = slot_positions[0].y()

            s_slot = getattr(eff, 'source_slot', None)
            if s_slot is not None and 0 <= s_slot < len(slot_positions) and is_target_monster:
                cx = slot_positions[s_slot].x()
                cy = slot_positions[s_slot].y()
            elif not is_target_monster and s_slot is not None:
                # 怪物施法攻擊玩家
                m_pos = self._get_canvas_monster_pos(s_slot, total_m, w, y=monster_base_y)
                cx = m_pos.x()
                cy = m_pos.y()
            else:
                scaled_x = int(eff.x * (w / 1140.0))
                closest_slot = min(slot_positions, key=lambda sp: abs(sp.x() - scaled_x))
                cx = closest_slot.x()
                cy = closest_slot.y()

            render_maple_vfx(
                painter, eff.kind, p, eff.color,
                cx, cy, tx, ty,
                rot_angle=self.global_rot_angle,
                seed=eff.seed,
                fracture_lines=getattr(eff, "fracture_lines", None)
            )

        # 繪製受擊白閃 (Hit Flash)
        if self.flash_timer > 0:
            painter.setBrush(QBrush(QColor(255, 255, 255, 165)))
            painter.setPen(Qt.NoPen)
            center_m_pos = self._get_canvas_monster_pos(0, total_m, w, y=monster_base_y)
            painter.drawEllipse(center_m_pos, 30, 30)

        # 繪製浮空傷害與戰技文字 (支援 monster_0 ~ monster_4 及 slot_0 ~ slot_4)
        popups = self.combat_mgr.floating_popups
        for pop in popups:
            t = pop["target"]
            if t == "monster":
                m_p = self._get_canvas_monster_pos(0, total_m, w, y=monster_base_y)
                bx, by = m_p.x(), m_p.y() + 15
            elif t.startswith("monster_"):
                try:
                    m_i = int(t.split("_")[1])
                    m_p = self._get_canvas_monster_pos(m_i, total_m, w, y=monster_base_y)
                    bx, by = m_p.x(), m_p.y() + 15
                except Exception:
                    m_p = self._get_canvas_monster_pos(0, total_m, w, y=monster_base_y)
                    bx, by = m_p.x(), m_p.y() + 15
            elif t.startswith("slot_"):
                try:
                    s_i = int(t.split("_")[1])
                    if 0 <= s_i < len(slot_positions):
                        bx, by = slot_positions[s_i].x(), slot_positions[s_i].y() - 15
                    else:
                        bx, by = w // 2, monster_base_y
                except Exception:
                    bx, by = w // 2, monster_base_y
            elif t in ["tank", "hero"]:
                bx, by = slot_positions[0].x(), slot_positions[0].y() - 15
            elif t == "healer":
                bx, by = slot_positions[min(3, len(slot_positions) - 1)].x(), slot_positions[min(3, len(slot_positions) - 1)].y() - 15
            else:
                bx, by = w // 2, monster_base_y

            px = int(bx + pop["offset_x"])
            py = int(by + pop["offset_y"])
            ratio = max(0.0, pop["life"] / pop["max_life"])
            alpha = int(255 * ratio)

            is_crit = pop.get("is_crit", False)
            pop_text = pop["text"]

            if is_crit:
                font = QFont("Microsoft YaHei UI", 12, QFont.Bold)
                painter.setFont(font)
                disp_text = f"★ {pop_text}"
                painter.setPen(QColor(0, 0, 0, alpha))
                for ox, oy in [(-1, -1), (1, -1), (-1, 1), (1, 1), (0, 2)]:
                    painter.drawText(QRect(px - 100 + ox, py - 12 + oy, 200, 24), Qt.AlignCenter, disp_text)

                painter.setPen(QColor(255, 215, 0, alpha))
                painter.drawText(QRect(px - 100, py - 12, 200, 24), Qt.AlignCenter, disp_text)
            else:
                font = QFont("Microsoft YaHei UI", 10, QFont.Normal)
                painter.setFont(font)
                cr, cg, cb = pop["color"][:3]
                painter.setPen(QColor(0, 0, 0, int(alpha * 0.8)))
                painter.drawText(QRect(px - 90 + 1, py - 12 + 1, 180, 24), Qt.AlignCenter, pop_text)

                painter.setPen(QColor(cr, cg, cb, alpha))
                painter.drawText(QRect(px - 90, py - 12, 180, 24), Qt.AlignCenter, pop_text)


