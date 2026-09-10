"""
《新楓之谷：放置遠征隊》- 單職業純淨技能特效沙盒 (vfx_sandbox.py)
專為職業技能特效精緻化打造的獨立驗證與除錯工具：
- 乾淨整潔：僅保留當前選中職業，杜絕多餘雜訊
- 上方怪物，下方施法者：完全符合遊戲實戰視角
- 純粹向量：不畫小人人偶，以專屬施法法陣光環與首領標靶呈現
- 支援 24 職業、全 192 招官方正統技能點播
- 逐幀拉條檢視器 (Progress Scrubber) + 慢動作 (0.25x / 0.5x / 1.0x) + 循環播放
"""

import sys
import os

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import math
import random
import time

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QGridLayout, QComboBox, QSlider,
    QCheckBox, QButtonGroup, QRadioButton
)
from PySide6.QtCore import Qt, QTimer, QRect, QRectF, QPoint, QPointF, QSize
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QRadialGradient,
    QPainterPath, QPolygonF
)

from classes import (
    EXPLORER_CLASSES, CYGNUS_CLASSES, RESISTANCE_CLASSES,
    ALL_CLASSES, get_class_info
)
from vfx_renderer import render_maple_vfx

SANDBOX_QSS = """
QWidget {
    background-color: #0d111a;
    color: #e2e8f0;
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 12px;
}

QComboBox {
    background-color: #1a2234;
    border: 1.5px solid #3b82f6;
    border-radius: 6px;
    padding: 6px 12px;
    color: #ffd700;
    font-weight: bold;
    font-size: 13px;
}
QComboBox:hover {
    border-color: #60a5fa;
}
QComboBox QAbstractItemView {
    background-color: #141a29;
    border: 1px solid #2a3447;
    selection-background-color: #25334d;
    selection-color: #ffd700;
    color: #e2e8f0;
    padding: 4px;
}

QPushButton {
    background-color: #1e2638;
    border: 1px solid #334155;
    border-radius: 5px;
    padding: 5px 10px;
    color: #f1f5f9;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #2b3752;
    border-color: #64748b;
}
QPushButton:pressed {
    background-color: #172033;
}

QSlider::groove:horizontal {
    border: 1px solid #334155;
    height: 6px;
    background: #1e293b;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #3b82f6;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #ffd700;
    border: 1px solid #d97706;
    width: 14px;
    margin-top: -4px;
    margin-bottom: -4px;
    border-radius: 7px;
}

QScrollBar:vertical {
    background-color: #0f1420;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background-color: #2a354c;
    min-height: 24px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background-color: #3b4a68;
}
"""


# =========================================================================
# 特效動畫實體
# =========================================================================
class SandboxVFX:
    def __init__(self, skill, caster_pos, target_pos, speed_mult=1.0):
        self.skill = skill
        self.caster_pos = caster_pos      # QPointF
        self.target_pos = target_pos      # QPointF
        self.speed_mult = speed_mult
        self.duration = max(0.65, 0.35 + skill.hit_count * 0.12)
        if getattr(skill, "skill_type", "") in ["aoe_beam", "stack_burst", "screen_slash", "team_buff"]:
            self.duration = 1.25
        self.time = 0.0
        self.progress = 0.0
        self.is_finished = False

        self.seed = random.uniform(0, 100)
        self.color = skill.color
        self.skill_type = getattr(skill, "skill_type", "attack")
        self.effect_name = getattr(skill, "effect_name", "generic_strike")
        self.name = skill.name
        self.hit_count = skill.hit_count

        self.fracture_lines = self._generate_fractures()

    def _generate_fractures(self):
        tx, ty = self.target_pos.x(), self.target_pos.y()
        lines = []
        for _ in range(8):
            angle = random.uniform(0, math.pi * 2)
            length = random.uniform(80, 190)
            mid_len = length * 0.5
            mid_ang = angle + random.uniform(-0.4, 0.4)
            p_start = (tx, ty)
            p_mid = (tx + math.cos(mid_ang) * mid_len, ty + math.sin(mid_ang) * mid_len)
            p_end = (tx + math.cos(angle) * length, ty + math.sin(angle) * length)
            lines.append((p_start, p_mid, p_end))
        return lines

    def update(self, dt):
        self.time += dt * self.speed_mult
        self.progress = min(1.0, self.time / self.duration)
        if self.progress >= 1.0:
            self.is_finished = True

    def set_progress(self, p):
        self.progress = max(0.0, min(1.0, p))
        self.time = self.progress * self.duration
        self.is_finished = (self.progress >= 1.0)


# =========================================================================
# 受擊金字瀑布
# =========================================================================
class DamagePopup:
    def __init__(self, text, x, y, is_crit=True, color=(255, 215, 0)):
        self.text = text
        self.x = x + random.uniform(-25, 25)
        self.y = y + random.uniform(-10, 10)
        self.is_crit = is_crit
        self.color = color
        self.life = 0.85
        self.max_life = 0.85
        self.offset_y = 0.0

    def update(self, dt, speed_mult=1.0):
        self.life -= dt * speed_mult
        progress = 1.0 - (self.life / self.max_life)
        self.offset_y = -42.0 * math.sin(progress * math.pi * 0.5)

    @property
    def is_dead(self):
        return self.life <= 0


# =========================================================================
# 純淨特效沙盒畫布 (無小人、上方首領怪物、下方施法光環)
# =========================================================================
class PureVFXCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 480)
        self.setStyleSheet("background-color: #0b0f17; border-radius: 8px;")

        self.current_vfx = None
        self.popups = []

        self.speed_mult = 1.0
        self.is_paused = False
        self.enable_shake = True
        self.enable_flash = True
        self.enable_crit_font = True
        self.enable_vignette = True

        self.shake_x = 0
        self.shake_y = 0
        self.shake_timer = 0.0
        self.flash_timer = 0.0
        self.monster_wobble_timer = 0.0

        self.caster_pos = QPointF(300, 400)
        self.target_pos = QPointF(300, 140)
        self.global_rot_angle = 0.0
        self.class_color = (66, 153, 225)

    def trigger_shake(self, power=6.0, duration=0.22):
        if self.enable_shake:
            self.shake_timer = duration
            self.shake_power = power

    def trigger_flash(self, duration=0.08):
        if self.enable_flash:
            self.flash_timer = duration

    def play_skill_vfx(self, skill):
        self.popups.clear()
        vfx = SandboxVFX(skill, self.caster_pos, self.target_pos, self.speed_mult)
        self.current_vfx = vfx

        if getattr(skill, "skill_type", "") in ["aoe_beam", "stack_burst", "screen_slash"]:
            self.trigger_shake(power=8.0, duration=0.32)
            self.trigger_flash(0.10)
        else:
            self.trigger_shake(power=4.0, duration=0.18)
            self.trigger_flash(0.05)

        self.monster_wobble_timer = 0.25

        # 產生經典楓之谷瀑布跳字
        hit_count = max(1, skill.hit_count)
        base_dmg = int(skill.dmg_mult * 28000 + random.randint(100, 800))
        for h in range(hit_count):
            dmg = int(base_dmg / hit_count * random.uniform(0.92, 1.08))
            is_crit = (random.random() < 0.88)
            px = self.target_pos.x() + (h * 6) - (hit_count * 3)
            py = self.target_pos.y() - 40 - (h * 20)
            self.popups.append(DamagePopup(f"{dmg:,}", px, py, is_crit=is_crit, color=skill.color))

    def update_frame(self, dt):
        self.global_rot_angle += 720.0 * dt * self.speed_mult

        if self.shake_timer > 0:
            self.shake_timer = max(0.0, self.shake_timer - dt * self.speed_mult)
            ratio = self.shake_timer / 0.22
            self.shake_x = random.randint(-int(5.0 * ratio), int(5.0 * ratio))
            self.shake_y = random.randint(-int(5.0 * ratio), int(5.0 * ratio))
        else:
            self.shake_x = 0
            self.shake_y = 0

        if self.flash_timer > 0:
            self.flash_timer = max(0.0, self.flash_timer - dt * self.speed_mult)

        if self.monster_wobble_timer > 0:
            self.monster_wobble_timer = max(0.0, self.monster_wobble_timer - dt * self.speed_mult)

        if self.current_vfx and not self.is_paused:
            self.current_vfx.update(dt)

        for p in self.popups:
            p.update(dt, self.speed_mult)
        self.popups = [p for p in self.popups if not p.is_dead]

        self.update()

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

        # 上方首領怪物，下方施法角色
        self.target_pos = QPointF(w * 0.50, h * 0.28)
        self.caster_pos = QPointF(w * 0.50, h * 0.76)

        if self.current_vfx:
            self.current_vfx.caster_pos = self.caster_pos
            self.current_vfx.target_pos = self.target_pos

        if self.enable_shake and self.shake_timer > 0:
            painter.translate(self.shake_x, self.shake_y)

        # 1. 戰鬥沙盒背景與科技網格
        self._draw_background(painter, w, h)

        # 2. 全屏暗角爆發氛圍
        if self.enable_vignette and self.current_vfx and getattr(self.current_vfx, "skill_type", "") in ["aoe_beam", "stack_burst"]:
            if self.current_vfx.progress < 0.7:
                painter.fillRect(QRect(0, 0, w, h), QColor(0, 0, 0, 130))

        # 3. 繪製施法光環 (無小人，純向量幾何法陣)
        self._draw_caster_aura(painter, self.caster_pos)

        # 4. 繪製上方目標首領 (簡潔高科技首領標靶與血條)
        self._draw_target_monster(painter, self.target_pos)

        # 5. 繪製當前技能純向量 VFX
        if self.current_vfx:
            vfx = self.current_vfx
            render_maple_vfx(
                painter, vfx.effect_name, vfx.progress, vfx.color,
                vfx.caster_pos.x(), vfx.caster_pos.y(),
                vfx.target_pos.x(), vfx.target_pos.y(),
                rot_angle=self.global_rot_angle,
                seed=vfx.seed,
                fracture_lines=vfx.fracture_lines
            )

        # 6. 受擊白閃
        if self.enable_flash and self.flash_timer > 0:
            painter.setBrush(QBrush(QColor(255, 255, 255, 160)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(self.target_pos, 50, 50)

        # 7. 受擊飄字瀑布
        self._draw_damage_popups(painter)

    def _draw_background(self, painter, w, h):
        # 深色星空微漸層
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor(10, 14, 22))
        grad.setColorAt(0.5, QColor(14, 18, 30))
        grad.setColorAt(1.0, QColor(8, 11, 18))
        painter.fillRect(QRect(0, 0, w, h), QBrush(grad))

        # 輕柔微網格
        painter.setPen(QPen(QColor(255, 255, 255, 12), 1, Qt.DotLine))
        grid_sz = 40
        for x in range(0, w, grid_sz):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, grid_sz):
            painter.drawLine(0, y, w, y)

        # 上下方聚光環
        for pos, col, rad in [(self.target_pos, QColor(255, 80, 80, 20), 140), (self.caster_pos, QColor(60, 160, 255, 22), 160)]:
            rg = QRadialGradient(pos.x(), pos.y(), rad)
            rg.setColorAt(0.0, col)
            rg.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(rg))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(pos, rad, rad * 0.55)

    def _draw_caster_aura(self, painter, pos):
        """施法者位置：純向量幾何法陣與光輝基底 (不畫小人)"""
        cx, cy = pos.x(), pos.y()
        r, g, b = self.class_color[:3]

        painter.save()
        painter.translate(cx, cy)

        # 外圈旋轉幾何魔法陣
        painter.save()
        painter.rotate(self.global_rot_angle * 0.15)
        painter.setPen(QPen(QColor(r, g, b, 120), 1.5, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, 0), 46, 20)
        painter.restore()

        # 內圈光環
        painter.setPen(QPen(QColor(r, g, b, 200), 2))
        painter.drawEllipse(QPointF(0, 0), 32, 14)

        # 核心聚能光柱基座
        rg = QRadialGradient(0, 0, 26)
        rg.setColorAt(0.0, QColor(255, 255, 255, 180))
        rg.setColorAt(0.5, QColor(r, g, b, 100))
        rg.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(rg))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(0, 0), 26, 12)

        # 角色位置標示文字徽記
        painter.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
        painter.setPen(QColor(255, 255, 255, 210))
        painter.drawText(QRect(-60, 18, 120, 20), Qt.AlignCenter, "【施法起點】")

        painter.restore()

    def _draw_target_monster(self, painter, pos):
        """上方目標首領：首領符印、血條與受擊晃動 (乾淨不干擾)"""
        tx, ty = pos.x(), pos.y()
        painter.save()

        wobble_x = 0
        if self.monster_wobble_timer > 0:
            ratio = self.monster_wobble_timer / 0.25
            wobble_x = math.sin(ratio * math.pi * 6) * 7.0

        painter.translate(tx + wobble_x, ty)

        # 首領暗紫發光體
        rg = QRadialGradient(0, 0, 55)
        rg.setColorAt(0.0, QColor(147, 51, 234, 180))
        rg.setColorAt(0.6, QColor(88, 28, 135, 120))
        rg.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(rg))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(0, 0), 55, 55)

        # 首領符印外環 (反向自轉)
        painter.save()
        painter.rotate(-self.global_rot_angle * 0.2)
        painter.setPen(QPen(QColor(216, 180, 254, 190), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, 0), 34, 34)

        for ang_deg in [0, 90, 180, 270]:
            rad = math.radians(ang_deg)
            px = math.cos(rad) * 34
            py = math.sin(rad) * 34
            painter.setBrush(QBrush(QColor(250, 204, 21)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(px, py), 3, 3)
        painter.restore()

        # 核心暗金骷髏/印記
        painter.setFont(QFont("Microsoft YaHei UI", 16, QFont.Bold))
        painter.setPen(QColor(255, 215, 0))
        painter.drawText(QRect(-24, -20, 48, 40), Qt.AlignCenter, "☠")

        painter.restore()

        # 首領血條與名稱
        hp_w = 120
        hp_h = 8
        hx = int(tx - hp_w / 2)
        hy = int(ty - 55)
        painter.fillRect(QRect(hx, hy, hp_w, hp_h), QColor(20, 20, 20, 220))
        painter.fillRect(QRect(hx, hy, int(hp_w * 0.85), hp_h), QColor(239, 68, 68))
        painter.setPen(QPen(QColor(255, 255, 255, 140), 1))
        painter.drawRect(QRect(hx, hy, hp_w, hp_h))

        painter.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
        painter.setPen(QColor(248, 250, 252))
        painter.drawText(QRect(hx - 20, hy - 18, hp_w + 40, 16), Qt.AlignCenter, "測試首領木人樁 Lv.260")

    def _draw_damage_popups(self, painter):
        if not self.enable_crit_font:
            return

        for pop in self.popups:
            px = int(pop.x)
            py = int(pop.y + pop.offset_y)
            ratio = max(0.0, pop.life / pop.max_life)
            alpha = int(255 * ratio)

            disp_text = f"★ {pop.text}" if pop.is_crit else pop.text

            font = QFont("Microsoft YaHei UI", 13 if pop.is_crit else 11, QFont.Bold)
            painter.setFont(font)

            painter.setPen(QColor(0, 0, 0, alpha))
            for ox, oy in [(-1, -1), (1, -1), (-1, 1), (1, 1), (0, 2)]:
                painter.drawText(QRect(px - 100 + ox, py - 14 + oy, 200, 28), Qt.AlignCenter, disp_text)

            if pop.is_crit:
                painter.setPen(QColor(255, 215, 0, alpha))
            else:
                r, g, b = pop.color[:3]
                painter.setPen(QColor(r, g, b, alpha))

            painter.drawText(QRect(px - 100, py - 14, 200, 28), Qt.AlignCenter, disp_text)


# =========================================================================
# 特效沙盒主視窗 (Single-Class VFX Sandbox)
# =========================================================================
class SingleClassVFXSandbox(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("《新楓之谷：放置遠征隊》- 單職業純淨技能特效沙盒 (Pure VFX Sandbox)")
        self.resize(1160, 780)
        self.setMinimumSize(960, 660)
        self.setStyleSheet(SANDBOX_QSS)

        self.current_class_id = "battle_mage"
        self.current_skill = None
        self.auto_loop = False
        self.auto_loop_timer = 0.0

        self._build_ui()

        # 16ms 動畫循環 (~60 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.last_time = time.time()
        self.timer.start(16)

        # 預設選中反抗軍代表：煉獄巫師
        self._on_class_combo_changed("battle_mage")

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # ---------------------------------------------------------------------
        # 左側面板：單一職業專屬清單 (無多餘職業干擾)
        # ---------------------------------------------------------------------
        left_panel = QFrame()
        left_panel.setFixedWidth(360)
        left_panel.setStyleSheet("background-color: #131825; border: 1px solid #2a3447; border-radius: 8px;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        title_lbl = QLabel("<b style='font-size: 15px; color: #ffd700;'>【單職業純淨檢視】</b>")
        left_layout.addWidget(title_lbl)

        # 24 職業下拉選擇器
        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("選擇職業:"))
        self.class_combo = QComboBox()

        factions = [
            ("【末日反抗軍】", RESISTANCE_CLASSES),
            ("【冒險家】", EXPLORER_CLASSES),
            ("【皇家騎士團】", CYGNUS_CLASSES),
        ]
        for f_label, c_dict in factions:
            for cid, cinfo in c_dict.items():
                self.class_combo.addItem(f"{f_label} {cinfo['name']} ({cinfo['branch']})", cid)

        self.class_combo.currentIndexChanged.connect(self._on_combo_index_changed)
        sel_row.addWidget(self.class_combo, 1)
        left_layout.addLayout(sel_row)

        # 職業簡介卡
        self.class_info_card = QFrame()
        self.class_info_card.setStyleSheet("background-color: #1a2234; border: 1px solid #334155; border-radius: 6px; padding: 8px;")
        ci_layout = QVBoxLayout(self.class_info_card)
        ci_layout.setSpacing(4)
        self.lbl_class_name = QLabel("<b>煉獄巫師</b>")
        self.lbl_class_name.setStyleSheet("font-size: 14px; color: #60a5fa;")
        ci_layout.addWidget(self.lbl_class_name)

        self.lbl_class_desc = QLabel("黑魔法近戰法師，聯盟光環守護全隊，鬥王杖擊橫掃四方")
        self.lbl_class_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.lbl_class_desc.setWordWrap(True)
        ci_layout.addWidget(self.lbl_class_desc)
        left_layout.addWidget(self.class_info_card)

        # 職業專屬 8 招技能卡牌列表
        left_layout.addWidget(QLabel("<b style='color: #f6ad55; font-size: 12px;'>【職業技能列表】 (點擊立即播放特效):</b>"))

        self.skill_scroll = QScrollArea()
        self.skill_scroll.setWidgetResizable(True)
        self.skill_scroll.setStyleSheet("background: transparent; border: none;")
        self.skill_container = QWidget()
        self.skill_layout = QVBoxLayout(self.skill_container)
        self.skill_layout.setContentsMargins(0, 0, 0, 0)
        self.skill_layout.setSpacing(6)
        self.skill_scroll.setWidget(self.skill_container)
        left_layout.addWidget(self.skill_scroll, 1)

        main_layout.addWidget(left_panel)

        # ---------------------------------------------------------------------
        # 右側面板：頂部資訊、中央畫布、底部拉條與控制器
        # ---------------------------------------------------------------------
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)

        # 頂部技能即時資訊條
        self.info_bar = QFrame()
        self.info_bar.setStyleSheet("background-color: #131825; border: 1px solid #2a3447; border-radius: 6px; padding: 6px;")
        ib_layout = QHBoxLayout(self.info_bar)
        ib_layout.setContentsMargins(10, 6, 10, 6)

        self.lbl_curr_skill_name = QLabel("<b style='color: #ffd700; font-size: 14px;'>請選擇技能</b>")
        ib_layout.addWidget(self.lbl_curr_skill_name)

        self.lbl_curr_skill_tag = QLabel("[標籤]")
        self.lbl_curr_skill_tag.setStyleSheet("color: #60a5fa; font-weight: bold; padding: 2px 6px; background: #1e293b; border-radius: 4px;")
        ib_layout.addWidget(self.lbl_curr_skill_tag)

        self.lbl_curr_skill_desc = QLabel("技能演算機制描述")
        self.lbl_curr_skill_desc.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        self.lbl_curr_skill_desc.setWordWrap(True)
        ib_layout.addWidget(self.lbl_curr_skill_desc, 1)

        right_layout.addWidget(self.info_bar)

        # 中央純淨畫布 (無小人，上方怪物，下方角色)
        self.canvas = PureVFXCanvas(self)
        right_layout.addWidget(self.canvas, 1)

        # 底部進度拉條 (逐幀檢視器)
        scrub_box = QFrame()
        scrub_box.setStyleSheet("background-color: #131825; border: 1px solid #2a3447; border-radius: 6px;")
        scrub_layout = QHBoxLayout(scrub_box)
        scrub_layout.setContentsMargins(10, 6, 10, 6)
        scrub_layout.setSpacing(10)

        scrub_layout.addWidget(QLabel("<b style='color: #ffd700;'>進度拉條:</b>"))

        self.scrub_slider = QSlider(Qt.Horizontal)
        self.scrub_slider.setRange(0, 1000)
        self.scrub_slider.setValue(0)
        self.scrub_slider.sliderMoved.connect(self._on_slider_moved)
        scrub_layout.addWidget(self.scrub_slider, 1)

        self.lbl_progress = QLabel("0.0%")
        self.lbl_progress.setFixedWidth(50)
        self.lbl_progress.setStyleSheet("font-weight: bold; color: #60a5fa;")
        scrub_layout.addWidget(self.lbl_progress)

        right_layout.addWidget(scrub_box)

        # 控制工具列
        ctrl_bar = QFrame()
        ctrl_bar.setStyleSheet("background-color: #131825; border: 1px solid #2a3447; border-radius: 6px;")
        cb_layout = QHBoxLayout(ctrl_bar)
        cb_layout.setContentsMargins(10, 8, 10, 8)
        cb_layout.setSpacing(10)

        self.btn_play_pause = QPushButton("⏸ 暫停")
        self.btn_play_pause.clicked.connect(self._toggle_pause)
        cb_layout.addWidget(self.btn_play_pause)

        btn_replay = QPushButton("⏮ 重新播放")
        btn_replay.clicked.connect(self._replay_current)
        cb_layout.addWidget(btn_replay)

        self.btn_loop = QPushButton("🔁 循環播放: 關")
        self.btn_loop.clicked.connect(self._toggle_loop)
        cb_layout.addWidget(self.btn_loop)

        cb_layout.addWidget(QLabel("速率:"))
        self.btn_speed_025 = QPushButton("0.25x")
        self.btn_speed_05 = QPushButton("0.5x")
        self.btn_speed_10 = QPushButton("1.0x (原速)")

        for b, m in [(self.btn_speed_025, 0.25), (self.btn_speed_05, 0.5), (self.btn_speed_10, 1.0)]:
            b.clicked.connect(lambda _, mult=m: self._set_speed(mult))
            cb_layout.addWidget(b)

        self._set_speed(1.0)

        self.chk_shake = QCheckBox("震屏")
        self.chk_shake.setChecked(True)
        self.chk_shake.toggled.connect(lambda c: setattr(self.canvas, "enable_shake", c))
        cb_layout.addWidget(self.chk_shake)

        self.chk_flash = QCheckBox("受擊白閃")
        self.chk_flash.setChecked(True)
        self.chk_flash.toggled.connect(lambda c: setattr(self.canvas, "enable_flash", c))
        cb_layout.addWidget(self.chk_flash)

        self.chk_crit = QCheckBox("暴擊飄字")
        self.chk_crit.setChecked(True)
        self.chk_crit.toggled.connect(lambda c: setattr(self.canvas, "enable_crit_font", c))
        cb_layout.addWidget(self.chk_crit)

        right_layout.addWidget(ctrl_bar)

        main_layout.addLayout(right_layout, 1)

    def _on_combo_index_changed(self, idx):
        class_id = self.class_combo.currentData()
        if class_id:
            self._on_class_combo_changed(class_id)

    def _on_class_combo_changed(self, class_id):
        self.current_class_id = class_id
        cinfo = get_class_info(class_id)
        if not cinfo:
            return

        self.canvas.class_color = cinfo.get("color", (66, 153, 225))
        self.lbl_class_name.setText(f"<b style='color: #ffd700; font-size: 15px;'>{cinfo['name']}</b> <span style='color: #94a3b8;'>({cinfo['branch']})</span>")
        self.lbl_class_desc.setText(cinfo.get("desc", ""))

        # 清空舊技能按鈕
        while self.skill_layout.count() > 0:
            child = self.skill_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        skills = cinfo.get("skills", [])
        for sk in skills:
            sf = QFrame()
            sf.setStyleSheet("background-color: #1a2234; border: 1px solid #334155; border-radius: 6px; padding: 6px;")
            s_lay = QVBoxLayout(sf)
            s_lay.setContentsMargins(6, 4, 6, 4)
            s_lay.setSpacing(3)

            r1 = QHBoxLayout()
            tag = getattr(sk, "tag_name", "主動")
            if not tag.startswith("["):
                tag = f"[{tag}]"
            r, g, b = sk.color[:3]
            lbl_tag = QLabel(f"<b>{tag}</b>")
            lbl_tag.setStyleSheet(f"color: rgb({r},{g},{b}); font-size: 11px;")
            r1.addWidget(lbl_tag)

            lbl_name = QLabel(f"<b>{sk.name}</b>")
            lbl_name.setStyleSheet("color: #f1f5f9; font-size: 12px;")
            r1.addWidget(lbl_name)

            r1.addStretch()

            btn_cast = QPushButton("▶ 施放")
            btn_cast.setStyleSheet("background-color: #2563eb; color: white; border: 1px solid #3b82f6; padding: 2px 8px;")
            btn_cast.clicked.connect(lambda _, s=sk: self._cast_skill(s))
            r1.addWidget(btn_cast)
            s_lay.addLayout(r1)

            lbl_desc = QLabel(sk.desc)
            lbl_desc.setStyleSheet("color: #94a3b8; font-size: 10px;")
            lbl_desc.setWordWrap(True)
            s_lay.addWidget(lbl_desc)

            self.skill_layout.addWidget(sf)

        self.skill_layout.addStretch()

        # 自動播放該職業的第一招技能
        if skills:
            self._cast_skill(skills[0])

    def _cast_skill(self, skill):
        self.current_skill = skill
        r, g, b = skill.color[:3]
        self.lbl_curr_skill_name.setText(f"<b style='color: rgb({r},{g},{b}); font-size: 15px;'>{skill.name}</b>")
        tag = getattr(skill, "tag_name", "主動")
        self.lbl_curr_skill_tag.setText(tag if tag.startswith("[") else f"[{tag}]")
        self.lbl_curr_skill_desc.setText(f"{skill.desc} | CD: {skill.cooldown}s | 連擊: {skill.hit_count}段 | 傷害: {int(skill.dmg_mult*100)}%")

        self.canvas.is_paused = False
        self.btn_play_pause.setText("⏸ 暫停")
        self.canvas.play_skill_vfx(skill)

    def _toggle_pause(self):
        self.canvas.is_paused = not self.canvas.is_paused
        self.btn_play_pause.setText("▶ 繼續" if self.canvas.is_paused else "⏸ 暫停")

    def _replay_current(self):
        if self.current_skill:
            self._cast_skill(self.current_skill)

    def _toggle_loop(self):
        self.auto_loop = not self.auto_loop
        if self.auto_loop:
            self.btn_loop.setText("🔁 循環播放: 開")
            self.btn_loop.setStyleSheet("background-color: #1e3a8a; color: #93c5fd; border: 1px solid #3b82f6;")
        else:
            self.btn_loop.setText("🔁 循環播放: 關")
            self.btn_loop.setStyleSheet("background-color: #1e2638; color: #f1f5f9; border: 1px solid #334155;")

    def _set_speed(self, mult):
        self.canvas.speed_mult = mult
        for b, m in [(self.btn_speed_025, 0.25), (self.btn_speed_05, 0.5), (self.btn_speed_10, 1.0)]:
            if m == mult:
                b.setStyleSheet("background-color: #1d4ed8; color: #ffd700; border: 1px solid #ffd700; font-weight: bold;")
            else:
                b.setStyleSheet("background-color: #1e2638; color: #cbd5e1; border: 1px solid #334155;")

    def _on_slider_moved(self, val):
        if self.canvas.current_vfx:
            p = val / 1000.0
            self.canvas.current_vfx.set_progress(p)
            self.canvas.is_paused = True
            self.btn_play_pause.setText("▶ 繼續")
            self.lbl_progress.setText(f"{p * 100:.1f}%")
            self.canvas.update()

    def _on_tick(self):
        now = time.time()
        dt = min(0.1, now - self.last_time)
        self.last_time = now

        self.canvas.update_frame(dt)

        if self.canvas.current_vfx:
            p = self.canvas.current_vfx.progress
            if not self.scrub_slider.isSliderDown():
                self.scrub_slider.setValue(int(p * 1000))
                self.lbl_progress.setText(f"{p * 100:.1f}%")

            if self.canvas.current_vfx.is_finished:
                if self.auto_loop and not self.canvas.is_paused:
                    self.auto_loop_timer += dt
                    if self.auto_loop_timer >= 0.35:
                        self.auto_loop_timer = 0.0
                        self._replay_current()


def main():
    app = QApplication(sys.argv)
    window = SingleClassVFXSandbox()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

