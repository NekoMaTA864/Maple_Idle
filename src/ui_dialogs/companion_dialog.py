"""
新楓之谷：放置冒險記 - 6 位隨行夥伴編隊與 17 職戰地後援彈窗 (companion_dialog.py)
支援 6 位夥伴自由選派、每位夥伴 2 招王牌技能配置，以及 17 位戰地後援全域屬性總覽。
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame, QComboBox, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt
from classes import ALL_CLASSES
from legion_system import LEGION_EFFECTS, calc_legion_bonuses


class CompanionDialog(QDialog):
    """6 位夥伴編隊與戰地後援管理彈窗"""
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.setWindowTitle("👥 隨行夥伴編隊與 🏛️ 戰地後援聯盟")
        self.resize(920, 720)
        self.setStyleSheet("""
            QDialog { background-color: #121620; color: #e2e8f0; font-family: 'Microsoft YaHei UI', sans-serif; }
            QFrame#card { background-color: #1a202c; border: 1px solid #2d3748; border-radius: 6px; }
            QComboBox { background-color: #2b3548; color: #edf2f7; border: 1px solid #4a5568; border-radius: 4px; padding: 4px; font-size: 11px; }
            QPushButton { background-color: #2b3548; color: #edf2f7; border: 1px solid #4a5568; border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: bold; }
            QPushButton:hover { background-color: #3b4760; border-color: #63b3ed; }
        """)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 頂部主角資訊
        hero = self.player.team[0]
        top_bar = QHBoxLayout()
        lbl_hero = QLabel(f"👑 核心主角：<b style='color: #f6e05e; font-size: 14px;'>{hero.name}</b> (Lv.{self.player.level}) ｜ 兩側護衛夥伴：<b>6 位</b>")
        lbl_hero.setStyleSheet("font-size: 13px; color: #edf2f7;")
        top_bar.addWidget(lbl_hero)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        # 1. 6 位隨行夥伴卡片區 (左 3 夥伴 + 右 3 夥伴)
        sec_comp = QLabel("⚔️ 隨行護衛夥伴陣型 (每位夥伴精選配置 2 招王牌招式)：")
        sec_comp.setStyleSheet("font-size: 13px; font-weight: bold; color: #63b3ed;")
        main_layout.addWidget(sec_comp)

        self.cards_container = QWidget()
        self.cards_grid = QGridLayout(self.cards_container)
        self.cards_grid.setSpacing(8)
        self.cards_grid.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.cards_container)

        # 2. 17 位戰地後援陣列 (Legion Bench)
        sec_legion = QLabel("🏛️ 聯盟戰地後援陣列 (未出戰的其餘 17 個職業，永久提供全域被動屬性)：")
        sec_legion.setStyleSheet("font-size: 13px; font-weight: bold; color: #f6ad55; margin-top: 6px;")
        main_layout.addWidget(sec_legion)

        scroll_legion = QScrollArea()
        scroll_legion.setWidgetResizable(True)
        scroll_legion.setFixedHeight(180)
        scroll_legion.setStyleSheet("QScrollArea { border: 1px solid #2d3748; border-radius: 6px; background-color: #0f131a; }")

        self.legion_content = QWidget()
        self.legion_layout = QVBoxLayout(self.legion_content)
        self.legion_layout.setContentsMargins(10, 8, 10, 8)
        self.legion_layout.setSpacing(4)
        scroll_legion.setWidget(self.legion_content)
        main_layout.addWidget(scroll_legion)

        # 底部按鈕
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_close = QPushButton("完成編隊並儲存")
        btn_close.setStyleSheet("background-color: #319795; color: white; padding: 7px 24px; font-size: 13px;")
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        main_layout.addLayout(btn_box)

        self._refresh_companions()
        self._refresh_legion()

    def _refresh_companions(self):
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 6 位夥伴 (slot_idx 1 ~ 6)
        for idx in range(1, 7):
            if idx >= len(self.player.team):
                break
            member = self.player.team[idx]
            card = self._create_companion_card(idx, member)
            col = (idx - 1) % 3
            row = (idx - 1) // 3
            self.cards_grid.addWidget(card, row, col)

    def _create_companion_card(self, slot_idx, member):
        frame = QFrame()
        frame.setObjectName("card")
        wing_str = "左翼護衛" if slot_idx <= 3 else "右翼護衛"
        frame.setStyleSheet("QFrame#card { background-color: #1a2233; border: 1px solid #3182ce; border-radius: 6px; }")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # 標題與職業切換下拉選單
        header = QHBoxLayout()
        lbl_slot = QLabel(f"<b>[夥伴 {slot_idx}]</b> <span style='color: #a0aec0; font-size: 10px;'>({wing_str})</span>")
        lbl_slot.setStyleSheet("color: #63b3ed; font-size: 11px;")
        header.addWidget(lbl_slot)
        header.addStretch()

        combo = QComboBox()
        combo.setMinimumWidth(110)
        all_cids = list(ALL_CLASSES.keys())
        cur_idx = 0
        for i, cid in enumerate(all_cids):
            combo.addItem(ALL_CLASSES[cid]["name"], cid)
            if cid == member.class_id:
                cur_idx = i
        combo.setCurrentIndex(cur_idx)
        combo.currentIndexChanged.connect(lambda c_idx, s_idx=slot_idx, cb=combo: self._on_change_companion_class(s_idx, cb.currentData()))
        header.addWidget(combo)
        layout.addLayout(header)

        # 技能欄位 (每位夥伴最多 2 招)
        lbl_sk_title = QLabel("出戰招式 (上限 2 招，點擊切換)：")
        lbl_sk_title.setStyleSheet("color: #cbd5e0; font-size: 10px;")
        layout.addWidget(lbl_sk_title)

        active_skills = member.get_active_skills()
        sk_box = QHBoxLayout()
        for s_slot in range(2):
            if s_slot < len(active_skills):
                sk = active_skills[s_slot]
                icon = getattr(sk, "icon_symbol", "⚔️")
                btn_sk = QPushButton(f"{icon} {sk.name}")
                dmg_mult = getattr(sk, "dmg_mult", getattr(sk, "damage_multiplier", 1.0))
                btn_sk.setToolTip(f"{sk.name}\n冷卻: {sk.cooldown:.1f}s | 傷害: {int(dmg_mult*100)}%\n{getattr(sk, 'desc', '')}")
                btn_sk.clicked.connect(lambda _, m=member, cur_s=sk: self._toggle_companion_skill(m, cur_s))
                sk_box.addWidget(btn_sk)
            else:
                btn_empty = QPushButton("[+ 選招式]")
                btn_empty.setStyleSheet("border-style: dashed; color: #718096;")
                btn_empty.clicked.connect(lambda _, m=member: self._pick_new_companion_skill(m))
                sk_box.addWidget(btn_empty)
        layout.addLayout(sk_box)
        return frame

    def _on_change_companion_class(self, slot_idx, new_cid):
        # 核心主角職業不可被夥伴佔用
        if new_cid == self.player.team[0].class_id:
            QMessageBox.information(self, "提示", "該職業目前為【核心主角】出戰職業，不可重複指派為隨行夥伴。")
            self._refresh_companions()
            return
        self.player.set_slot_class(slot_idx, new_cid)
        self._refresh_companions()
        self._refresh_legion()

    def _toggle_companion_skill(self, member, current_skill):
        """點擊現有技能可切換為該職業的其他技能"""
        all_skills = member.class_info["skills"]
        cur_ids = [s.skill_id for s in member.get_active_skills()]
        # 尋找未裝備的下一招
        next_skill = None
        for s in all_skills:
            if s.skill_id not in cur_ids:
                next_skill = s
                break
        if next_skill:
            member.unequip_skill(current_skill.skill_id)
            member.equip_skill(next_skill)
            self._refresh_companions()

    def _pick_new_companion_skill(self, member):
        all_skills = member.class_info["skills"]
        cur_ids = [s.skill_id for s in member.get_active_skills()]
        for s in all_skills:
            if s.skill_id not in cur_ids:
                member.equip_skill(s)
                break
        self._refresh_companions()

    def _refresh_legion(self):
        while self.legion_layout.count():
            item = self.legion_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        bench = self.player.get_bench_classes()
        totals = calc_legion_bonuses(bench)

        # 戰地總成摘要標籤
        summary_lines = []
        if totals.get("damage_mult", 0) > 0: summary_lines.append(f"傷害 +{totals['damage_mult']*100:.1f}%")
        if totals.get("attack", 0) > 0: summary_lines.append(f"攻擊 +{totals['attack']}")
        if totals.get("crit_chance", 0) > 0: summary_lines.append(f"暴擊率 +{totals['crit_chance']*100:.1f}%")
        if totals.get("crit_dmg", 0) > 0: summary_lines.append(f"暴傷 +{totals['crit_dmg']*100:.1f}%")
        if totals.get("def_ignore", 0) > 0: summary_lines.append(f"無視防禦 +{totals['def_ignore']*100:.1f}%")
        if totals.get("final_dmg", 0) > 0: summary_lines.append(f"終傷 +{totals['final_dmg']*100:.1f}%")
        if totals.get("hp_pct", 0) > 0: summary_lines.append(f"生命 +{totals['hp_pct']*100:.1f}%")
        if totals.get("def_pct", 0) > 0: summary_lines.append(f"防禦 +{totals['def_pct']*100:.1f}%")
        if totals.get("gold_mult", 0) > 0: summary_lines.append(f"楓幣 +{totals['gold_mult']*100:.1f}%")
        if totals.get("exp_mult", 0) > 0: summary_lines.append(f"經驗 +{totals['exp_mult']*100:.1f}%")
        if totals.get("lifesteal", 0) > 0: summary_lines.append(f"吸血 +{totals['lifesteal']*100:.1f}%")

        sum_label = QLabel(f"🌟 <b>【17 職戰地聯盟加成總計】</b>：{' ｜ '.join(summary_lines)}")
        sum_label.setStyleSheet("color: #ecc94b; font-size: 11px; background-color: #242c3d; padding: 6px; border-radius: 4px;")
        sum_label.setWordWrap(True)
        self.legion_layout.addWidget(sum_label)

        # 列出 17 位後援清單
        b_grid = QGridLayout()
        b_grid.setSpacing(4)
        for i, cid in enumerate(bench):
            eff = LEGION_EFFECTS.get(cid, {})
            cname = eff.get("name", cid)
            desc = eff.get("desc", "")
            lbl = QLabel(f"<b>{cname}</b>: <span style='color: #cbd5e0;'>{desc}</span>")
            lbl.setStyleSheet("font-size: 10px; background-color: #171c28; padding: 3px 6px; border-radius: 3px;")
            r = i // 3
            c = i % 3
            b_grid.addWidget(lbl, r, c)

        self.legion_layout.addLayout(b_grid)
