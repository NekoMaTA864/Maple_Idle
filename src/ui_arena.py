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
from arena_layout import ArenaLayout
from combat_avatar import CombatAvatar, draw_enemy_emblem
from vfx_prototype import AreaEffect, ImpactEffect, PrototypeEffect

class CombatArenaWidget(QWidget):
    """即時動態繪製特效、螢幕震動、受擊白閃與楓之谷風格跳字 (硬體抗鋸齒)"""
    def __init__(self, combat_mgr, parent=None, show_debug_anchors=False):
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
        self.combat_avatar = CombatAvatar("hero")
        self.show_debug_anchors = bool(show_debug_anchors)
        self.skill_slots = [
            {"label": f"S{index + 1}", "cooldown": 0.0, "max_cooldown": 0.0,
             "color": color}
            for index, color in enumerate(((255, 215, 90), (176, 132, 255), (255, 145, 70), (130, 236, 210)))
        ]

    def trigger_shake(self, power=3.5, duration=0.22):
        self.shake_power = power
        self.shake_timer = duration

    def trigger_flash(self, duration=0.08):
        self.flash_timer = duration

    def set_skill_cooldown(self, slot_idx, remaining, total=None):
        """Set presentation-only cooldown data for one of the four prototype slots."""
        if not 0 <= int(slot_idx) < len(self.skill_slots):
            return
        slot = self.skill_slots[int(slot_idx)]
        slot["cooldown"] = max(0.0, float(remaining))
        if total is not None:
            slot["max_cooldown"] = max(0.0, float(total))

    def set_skill_label(self, slot_idx, label):
        if 0 <= int(slot_idx) < len(self.skill_slots):
            self.skill_slots[int(slot_idx)]["label"] = str(label)

    def set_combat_avatar(self, avatar_id):
        """Select a weapon-symbol avatar without touching gameplay state."""
        self.combat_avatar.set_avatar(avatar_id)

    def trigger_avatar_attack(self):
        self.combat_avatar.trigger_attack()

    def avatar_anchor(self, name="center"):
        layout = ArenaLayout(self.width(), self.height())
        return self.combat_avatar.anchor(name, layout.player_position())

    def enemy_anchor(self, name="center", index=0, total=None):
        layout = ArenaLayout(self.width(), self.height())
        monster_total = total if total is not None else max(1, len(getattr(self.combat_mgr, "monsters", [])))
        return layout.enemy_anchor(name, index=index, total=monster_total)

    def set_debug_anchors(self, visible):
        self.show_debug_anchors = bool(visible)

    def update_vfx_timer(self, dt):
        self.game_time += dt
        self.combat_avatar.update(dt)
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

        for slot in self.skill_slots:
            if slot["cooldown"] > 0.0:
                slot["cooldown"] = max(0.0, slot["cooldown"] - dt)

    def _get_canvas_monster_pos(self, idx, total, w, y=75):
        layout = ArenaLayout(w, self.height())
        x_pos, y_pos = layout.enemy_position(idx, total)
        return QPoint(int(x_pos), int(y_pos))

    def _draw_skill_bar(self, painter, layout):
        """Draw four presentation-only skill slots below the primary player."""
        positions = layout.skill_positions(len(self.skill_slots))
        painter.save()
        for index, (x_pos, y_pos) in enumerate(positions):
            slot = self.skill_slots[index]
            color = QColor(*slot["color"])
            cooldown = max(0.0, float(slot["cooldown"]))
            max_cooldown = max(0.0, float(slot["max_cooldown"]))
            ready = cooldown <= 0.0
            box = QRectF(x_pos - 29, y_pos - 25, 58, 50)

            painter.setBrush(QBrush(QColor(18, 25, 39, 220)))
            painter.setPen(QPen(QColor(104, 220, 170, 210) if ready else QColor(71, 85, 105, 190), 1.2))
            painter.drawRoundedRect(box, 8, 8)

            painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 210)))
            painter.setPen(QPen(QColor(255, 255, 255, 210), 1.0))
            painter.drawEllipse(QPointF(x_pos, y_pos - 5), 13, 13)
            painter.setFont(QFont("Microsoft YaHei UI", 8, QFont.Bold))
            painter.setPen(QColor(20, 25, 35))
            painter.drawText(QRectF(x_pos - 18, y_pos - 17, 36, 24), Qt.AlignCenter, slot["label"])

            if not ready:
                overlay_ratio = min(1.0, cooldown / max_cooldown) if max_cooldown else 1.0
                overlay_height = 42.0 * overlay_ratio
                painter.setBrush(QBrush(QColor(5, 8, 15, 155)))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(QRectF(x_pos - 27, y_pos + 23 - overlay_height, 54, overlay_height), 6, 6)
                painter.setFont(QFont("Microsoft YaHei UI", 8, QFont.Bold))
                painter.setPen(QColor(255, 245, 210))
                painter.drawText(QRectF(x_pos - 27, y_pos + 4, 54, 18), Qt.AlignCenter, f"{cooldown:.1f}s")
            else:
                painter.setFont(QFont("Microsoft YaHei UI", 6, QFont.Bold))
                painter.setPen(QColor(104, 220, 170, 180))
                painter.drawText(QRectF(x_pos - 27, y_pos + 9, 54, 14), Qt.AlignCenter, "READY")
        painter.restore()

    def _draw_debug_anchors(self, painter, layout, total_m):
        """Optional anchor overlay; hidden in normal Arena and Gallery mode."""
        avatar_center = layout.player_position()
        points = [
            ("avatar.center", self.combat_avatar.anchor("center", avatar_center), (120, 220, 255)),
            ("avatar.attack_origin", self.combat_avatar.anchor("attack_origin", avatar_center), (255, 190, 90)),
            ("avatar.tip", self.combat_avatar.anchor("tip", avatar_center), (255, 240, 150)),
            ("avatar.ground", self.combat_avatar.anchor("ground", avatar_center), (120, 255, 180)),
        ]
        for enemy_idx in range(min(3, total_m)):
            enemy = layout.enemy_anchors(enemy_idx, total_m)
            points.extend([
                (f"enemy{enemy_idx}.hit", enemy["hit"], (255, 120, 150)),
                (f"enemy{enemy_idx}.ground", enemy["ground"], (180, 140, 255)),
            ])
        points.append(("companion.staging", layout.companion_position(), (130, 170, 205)))

        painter.save()
        painter.setFont(QFont("Microsoft YaHei UI", 6, QFont.Normal))
        for label, (x_pos, y_pos), rgb in points:
            painter.setPen(QPen(QColor(*rgb, 220), 1.0))
            painter.setBrush(QBrush(QColor(*rgb, 125)))
            painter.drawEllipse(QPointF(x_pos, y_pos), 3.0, 3.0)
            painter.drawLine(QPointF(x_pos - 6, y_pos), QPointF(x_pos + 6, y_pos))
            painter.drawLine(QPointF(x_pos, y_pos - 6), QPointF(x_pos, y_pos + 6))
            painter.drawText(QRectF(x_pos + 7, y_pos - 8, 118, 14), Qt.AlignLeft, label)
        painter.restore()

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
        layout = ArenaLayout(w, h)

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
        ground_y = int(layout.player_y + 30)
        painter.setPen(QPen(QColor(52, 70, 102, 160), 1.5))
        painter.drawLine(10, ground_y, w - 10, ground_y)

        # Render localized ground effects before actor bodies.
        vfx_list = self.combat_mgr.vfx_mgr.effects
        for eff in vfx_list:
            if isinstance(eff, AreaEffect):
                eff.draw(painter)

        # Render one primary player body in the prototype shell; the full
        # expedition team remains in gameplay state and information panels.
        player_x, player_y = layout.player_position()
        slot_positions = [QPoint(int(player_x), int(player_y))]

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

        # The primary combat representation is a weapon/class symbol, not a
        # full character sprite or a large nameplate.
        self.combat_avatar.draw(painter, (player_x, player_y))
        if self.combat_mgr.player.team:
            avatar_label = self.combat_avatar.definition.label
            painter.setFont(QFont("Microsoft YaHei UI", 7, QFont.Bold))
            painter.setPen(QColor(228, 235, 248, 190))
            painter.drawText(QRectF(player_x - 80, player_y - 70, 160, 16), Qt.AlignCenter, avatar_label)

        if self.combat_mgr.player.team:
            primary = self.combat_mgr.player.team[0]
            max_hp = max(1, int(primary.get_max_hp(self.combat_mgr.player)))
            hp_ratio = max(0.0, min(1.0, float(primary.current_hp) / max_hp))
            hp_x = int(player_x - 58)
            hp_y = int(player_y + 15)
            painter.setBrush(QBrush(QColor(18, 24, 34, 230)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(hp_x, hp_y, 116, 7), 3, 3)
            painter.setBrush(QBrush(QColor(80, 205, 140)))
            painter.drawRoundedRect(QRectF(hp_x, hp_y, 116 * hp_ratio, 7), 3, 3)
            painter.setFont(QFont("Microsoft YaHei UI", 7, QFont.Bold))
            painter.setPen(QColor(190, 240, 215))
            painter.drawText(QRectF(hp_x - 8, hp_y + 8, 132, 14), Qt.AlignCenter,
                             f"PLAYER HP {int(primary.current_hp)}/{max_hp}")

        # Companion staging remains an invisible layout anchor in normal play.

        # 繪製怪物群體 (支援 1~5 隻多怪物波次、菁英怪光芒與專屬即時血條，位置隨畫布動態自適應)
        monsters = self.combat_mgr.monsters if self.combat_mgr.monsters else ([self.combat_mgr.monster] if self.combat_mgr.monster else [])
        total_m = max(1, len(monsters))
        monster_base_y = int(layout.enemy_y)

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

                # Enemy presentation is an abstract core/emblem; the name is
                # secondary information rather than the enemy body.
                draw_enemy_emblem(
                    painter, (m_pos.x(), m_draw_y), m.is_boss, is_elite,
                    self.game_time + idx * 0.17,
                )
                if m.is_boss:
                    m_text = f"BOSS · {m.name}"
                    label_color = QColor(222, 190, 255, 220)
                elif is_elite:
                    m_text = f"ELITE · {m.name}"
                    label_color = QColor(255, 218, 125, 210)
                else:
                    m_text = m.name[:12]
                    label_color = QColor(218, 185, 198, 190)
                painter.setFont(QFont("Microsoft YaHei UI", 7 if not m.is_boss else 8, QFont.Bold))
                painter.setPen(label_color)
                painter.drawText(QRectF(m_pos.x() - 100, m_draw_y + (40 if m.is_boss else 31), 200, 16), Qt.AlignCenter, m_text)

                # 頭頂血條 (即時微型血條)
                bar_w = 64 if not m.is_boss else 86
                bar_x = m_pos.x() - bar_w // 2
                bar_y = m_draw_y - (52 if m.is_boss else 41)
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
        has_screen_ultimate = any(eff.kind in ["holy", "aoe_beam", "dimension_rift", "dark_genesis_thunder"] and eff.progress < 0.7 for eff in vfx_list)
        if has_screen_ultimate:
            painter.fillRect(QRect(0, 0, w, h), QColor(0, 0, 0, 120))

        # 繪製高度差異化戰場視覺特效 (Visual Effects)
        for eff in vfx_list:
            if isinstance(eff, (AreaEffect, ImpactEffect)):
                continue
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

        for eff in vfx_list:
            if isinstance(eff, PrototypeEffect) and not isinstance(eff, (AreaEffect, ImpactEffect)):
                eff.draw(painter)

        # Impact/explosion is a distinct layer above the attack travel.
        for eff in vfx_list:
            if isinstance(eff, ImpactEffect):
                eff.draw(painter)

        if self.show_debug_anchors:
            self._draw_debug_anchors(painter, layout, total_m)

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

        # Final layer: the skill UI stays above all actor/VFX/popup pixels.
        self._draw_skill_bar(painter, layout)


