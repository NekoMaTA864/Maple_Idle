"""
新楓之谷：放置冒險記 - 主角技能配置構築彈窗 (skill_deck_dialog.py)
支援主角母職業群龐大技能庫 (24~40招任選)、6~12槽位擴展與一鍵預設套裝配置。
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from classes import get_mother_group_for_class, get_mother_group_skills, ALL_CLASSES


class SkillDeckDialog(QDialog):
    """主角技能構築配置彈窗"""
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.hero = player.team[0]  # 席位 0 核心主角
        self.setWindowTitle("🎯 核心主角技能構築 (Skill Deck)")
        self.resize(880, 680)
        self.setStyleSheet("""
            QDialog { background-color: #121620; color: #e2e8f0; font-family: 'Microsoft YaHei UI', sans-serif; }
            QFrame#card { background-color: #1a202c; border: 1px solid #2d3748; border-radius: 6px; }
            QPushButton { background-color: #2b3548; color: #edf2f7; border: 1px solid #4a5568; border-radius: 4px; padding: 5px 10px; font-weight: bold; }
            QPushButton:hover { background-color: #3b4760; border-color: #63b3ed; }
            QPushButton#btn_preset { background-color: #2c5282; color: #bee3f8; border: 1px solid #4299e1; }
            QPushButton#btn_preset:hover { background-color: #2b6cb0; }
        """)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 頂部資訊列
        top_bar = QHBoxLayout()
        group_info = get_mother_group_for_class(self.hero.class_id)
        max_slots = self.hero.max_skill_slots
        p_lvl = self.player.level

        lbl_title = QLabel(f"👑 核心主角：<b>{self.hero.name}</b> ｜ 母職業群：<b style='color: #f6ad55;'>{group_info['name']}</b>")
        lbl_title.setStyleSheet("font-size: 14px; color: #edf2f7;")
        top_bar.addWidget(lbl_title)
        top_bar.addStretch()

        slot_hint = f"技能槽位：<b>{len(self.hero.get_active_skills())}/{max_slots}</b>"
        if p_lvl < 100:
            slot_hint += f" <span style='color: #a0aec0;'>(Lv.100 解鎖額外 6 槽)</span>"
        else:
            slot_hint += f" <span style='color: #68d391;'>★ 全 12 槽已完全解鎖！</span>"

        lbl_slots = QLabel(slot_hint)
        lbl_slots.setStyleSheet("font-size: 13px; color: #cbd5e0;")
        top_bar.addWidget(lbl_slots)
        main_layout.addLayout(top_bar)

        # 快捷預設按鈕列
        preset_bar = QHBoxLayout()
        lbl_p_title = QLabel("⚡ 一鍵構築：")
        lbl_p_title.setStyleSheet("color: #a0aec0; font-size: 12px;")
        preset_bar.addWidget(lbl_p_title)

        btn_mob = QPushButton("🌾 割草農怪組")
        btn_mob.setObjectName("btn_preset")
        btn_mob.clicked.connect(self._preset_mob)
        preset_bar.addWidget(btn_mob)

        btn_boss = QPushButton("👑 首領攻堅組")
        btn_boss.setObjectName("btn_preset")
        btn_boss.clicked.connect(self._preset_boss)
        preset_bar.addWidget(btn_boss)

        btn_survival = QPushButton("🛡️ 護盾吸血組")
        btn_survival.setObjectName("btn_preset")
        btn_survival.clicked.connect(self._preset_survival)
        preset_bar.addWidget(btn_survival)

        btn_origin = QPushButton("✨ 本職經典組")
        btn_origin.setObjectName("btn_preset")
        btn_origin.clicked.connect(self._preset_origin)
        preset_bar.addWidget(btn_origin)

        preset_bar.addStretch()
        main_layout.addLayout(preset_bar)

        # 1. 裝備中的技能槽位區域 (6 格 或 12 格)
        sec_equipped = QLabel(f"🎯 已裝備出戰技能 (點擊卡片可卸下，至多 {max_slots} 招)：")
        sec_equipped.setStyleSheet("font-size: 13px; font-weight: bold; color: #63b3ed;")
        main_layout.addWidget(sec_equipped)

        self.equipped_container = QWidget()
        self.equipped_grid = QGridLayout(self.equipped_container)
        self.equipped_grid.setSpacing(8)
        self.equipped_grid.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.equipped_container)

        # 2. 母職業群可用技能庫 (捲動清單)
        sec_pool = QLabel(f"📚 {group_info['name']}技能庫 (共 {len(self.hero.get_available_skills())} 招，點擊未裝備卡片即可裝配)：")
        sec_pool.setStyleSheet("font-size: 13px; font-weight: bold; color: #f6ad55; margin-top: 6px;")
        main_layout.addWidget(sec_pool)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #2d3748; border-radius: 6px; background-color: #0f131a; }")

        self.pool_container = QWidget()
        self.pool_grid = QGridLayout(self.pool_container)
        self.pool_grid.setSpacing(8)
        self.pool_grid.setContentsMargins(10, 10, 10, 10)
        scroll.setWidget(self.pool_container)
        main_layout.addWidget(scroll, 1)

        # 底部關閉確認按鈕
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_close = QPushButton("完成配置並儲存")
        btn_close.setStyleSheet("background-color: #319795; color: white; padding: 7px 24px; font-size: 13px;")
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        main_layout.addLayout(btn_box)

        self._refresh_views()

    def _refresh_views(self):
        # 1. 刷新裝備槽位
        while self.equipped_grid.count():
            item = self.equipped_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        active_skills = self.hero.get_active_skills()
        max_slots = self.hero.max_skill_slots

        cols = 6
        for slot_i in range(12):
            r = slot_i // cols
            c = slot_i % cols

            if slot_i < len(active_skills):
                sk = active_skills[slot_i]
                card = self._create_equipped_card(slot_i + 1, sk)
                self.equipped_grid.addWidget(card, r, c)
            elif slot_i < max_slots:
                card = self._create_empty_slot_card(slot_i + 1)
                self.equipped_grid.addWidget(card, r, c)
            else:
                card = self._create_locked_slot_card(slot_i + 1)
                self.equipped_grid.addWidget(card, r, c)

        # 2. 刷新技能庫
        while self.pool_grid.count():
            item = self.pool_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        active_ids = {s.skill_id for s in active_skills}
        all_avail = self.hero.get_available_skills()

        pool_cols = 4
        for idx, sk in enumerate(all_avail):
            r = idx // pool_cols
            c = idx % pool_cols
            is_equipped = sk.skill_id in active_ids
            card = self._create_pool_card(sk, is_equipped)
            self.pool_grid.addWidget(card, r, c)

    def _create_equipped_card(self, slot_num, sk):
        frame = QFrame()
        frame.setObjectName("card")
        frame.setStyleSheet("QFrame#card { background-color: #1e2638; border: 1px solid #4299e1; border-radius: 6px; }")
        frame.setFixedHeight(88)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        header = QHBoxLayout()
        lbl_num = QLabel(f"#{slot_num}")
        lbl_num.setStyleSheet("color: #63b3ed; font-size: 10px; font-weight: bold;")
        header.addWidget(lbl_num)

        origin_name = getattr(sk, "origin_class_name", self.hero.name)
        lbl_orig = QLabel(f"[{origin_name}]")
        lbl_orig.setStyleSheet("color: #a0aec0; font-size: 9px;")
        header.addWidget(lbl_orig)
        header.addStretch()

        btn_rem = QPushButton("✕")
        btn_rem.setFixedSize(18, 18)
        btn_rem.setStyleSheet("padding: 0; font-size: 10px; background-color: #4a5568; color: #fc8181;")
        btn_rem.clicked.connect(lambda: self._unequip(sk.skill_id))
        header.addWidget(btn_rem)
        layout.addLayout(header)

        icon = getattr(sk, "icon_symbol", "⚔️")
        lbl_name = QLabel(f"{icon} {sk.name}")
        lbl_name.setStyleSheet("font-weight: bold; font-size: 11px; color: #f7fafc;")
        layout.addWidget(lbl_name)

        dmg_mult = getattr(sk, "dmg_mult", getattr(sk, "damage_multiplier", 1.0))
        stat_str = f"CD:{sk.cooldown:.1f}s | 傷:{int(dmg_mult*100)}%"
        if getattr(sk, "hit_count", 1) > 1:
            stat_str += f"x{sk.hit_count}"
        lbl_stat = QLabel(stat_str)
        lbl_stat.setStyleSheet("color: #cbd5e0; font-size: 9px;")
        layout.addWidget(lbl_stat)

        tag = getattr(sk, "tag_name", getattr(sk, "tag", ""))
        if tag:
            lbl_tag = QLabel(tag)
            lbl_tag.setStyleSheet("color: #ecc94b; font-size: 9px; font-weight: bold;")
            layout.addWidget(lbl_tag)

        return frame

    def _create_empty_slot_card(self, slot_num):
        frame = QFrame()
        frame.setObjectName("card")
        frame.setStyleSheet("QFrame#card { background-color: #151923; border: 1px dashed #4a5568; border-radius: 6px; }")
        frame.setFixedHeight(88)

        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel(f"槽位 #{slot_num}\n[空置中]")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #718096; font-size: 10px;")
        layout.addWidget(lbl)
        return frame

    def _create_locked_slot_card(self, slot_num):
        frame = QFrame()
        frame.setObjectName("card")
        frame.setStyleSheet("QFrame#card { background-color: #0f121a; border: 1px dashed #2d3748; border-radius: 6px; }")
        frame.setFixedHeight(88)

        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel(f"🔒 槽位 #{slot_num}\nLv.100 解鎖")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #4a5568; font-size: 10px;")
        layout.addWidget(lbl)
        return frame

    def _create_pool_card(self, sk, is_equipped):
        frame = QFrame()
        frame.setObjectName("card")
        border_col = "#3182ce" if is_equipped else "#2d3748"
        bg_col = "#1a2333" if is_equipped else "#171c28"
        frame.setStyleSheet(f"QFrame#card {{ background-color: {bg_col}; border: 1px solid {border_col}; border-radius: 6px; }}")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(3)

        top = QHBoxLayout()
        origin = getattr(sk, "origin_class_name", self.hero.name)
        lbl_orig = QLabel(f"[{origin}]")
        lbl_orig.setStyleSheet("color: #f6ad55; font-size: 10px; font-weight: bold;")
        top.addWidget(lbl_orig)
        top.addStretch()

        if is_equipped:
            lbl_eq = QLabel("★ 已出戰")
            lbl_eq.setStyleSheet("color: #68d391; font-size: 10px; font-weight: bold;")
            top.addWidget(lbl_eq)
        else:
            btn_add = QPushButton("+ 裝備")
            btn_add.setFixedHeight(20)
            btn_add.setStyleSheet("padding: 1px 6px; font-size: 10px;")
            btn_add.clicked.connect(lambda: self._equip(sk))
            top.addWidget(btn_add)
        layout.addLayout(top)

        icon = getattr(sk, "icon_symbol", "⚔️")
        lbl_name = QLabel(f"{icon} {sk.name}")
        lbl_name.setStyleSheet("color: #ffffff; font-size: 11px; font-weight: bold;")
        layout.addWidget(lbl_name)

        dmg_mult = getattr(sk, "dmg_mult", getattr(sk, "damage_multiplier", 1.0))
        stat_str = f"冷卻: {sk.cooldown:.1f}s ｜ 傷害: {int(dmg_mult*100)}%"
        if getattr(sk, "hit_count", 1) > 1:
            stat_str += f" ({sk.hit_count}連段)"
        if getattr(sk, "def_ignore", getattr(sk, "ignore_defense_pct", 0)) > 0:
            def_ign = getattr(sk, "def_ignore", getattr(sk, "ignore_defense_pct", 0))
            stat_str += f" 破防+{int(def_ign*100)}%"
        lbl_stat = QLabel(stat_str)
        lbl_stat.setStyleSheet("color: #cbd5e0; font-size: 9px;")
        layout.addWidget(lbl_stat)

        desc = getattr(sk, "desc", "")
        if desc:
            lbl_desc = QLabel(desc)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet("color: #a0aec0; font-size: 9px;")
            layout.addWidget(lbl_desc)

        return frame

    def _equip(self, sk):
        ok, msg = self.hero.equip_skill(sk)
        if not ok:
            QMessageBox.warning(self, "裝備失敗", msg)
        else:
            self._refresh_views()

    def _unequip(self, skill_id):
        ok, msg = self.hero.unequip_skill(skill_id)
        if not ok:
            QMessageBox.warning(self, "卸下失敗", msg)
        else:
            self._refresh_views()

    def _preset_mob(self):
        """一鍵割草農怪組：優先挑選 AOE 與多段技能"""
        avail = self.hero.get_available_skills()
        scored = []
        for s in avail:
            score = 0
            if getattr(s, "is_aoe", False) or getattr(s, "skill_type", "") == "aoe_beam":
                score += 10
            if getattr(s, "hit_count", 1) > 1:
                score += getattr(s, "hit_count", 1) * 2
            if s.cooldown <= 4.5:
                score += 3
            scored.append((score, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        picked = [item[1] for item in scored[:self.hero.max_skill_slots]]
        self.hero.set_equipped_skills(picked)
        self._refresh_views()

    def _preset_boss(self):
        """一鍵首領攻堅組：優先挑選單體高破防、高倍率與增傷"""
        avail = self.hero.get_available_skills()
        scored = []
        for s in avail:
            dmg_mult = getattr(s, "dmg_mult", getattr(s, "damage_multiplier", 1.0))
            score = dmg_mult * getattr(s, "hit_count", 1)
            def_ign = getattr(s, "def_ignore", getattr(s, "ignore_defense_pct", 0))
            score += def_ign * 10
            if getattr(s, "skill_type", "") == "team_buff" or getattr(s, "buff_val", 0) > 0:
                score += 8
            scored.append((score, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        picked = [item[1] for item in scored[:self.hero.max_skill_slots]]
        self.hero.set_equipped_skills(picked)
        self._refresh_views()

    def _preset_survival(self):
        """一鍵護盾吸血組：優先挑選護盾、吸血與減傷技能"""
        avail = self.hero.get_available_skills()
        scored = []
        for s in avail:
            score = 0
            if getattr(s, "skill_type", "") == "shield" or getattr(s, "shield_bonus", 0) > 0:
                score += 15
            if getattr(s, "life_steal", 0) > 0 or getattr(s, "lifesteal_bonus", 0) > 0:
                score += 12
            if getattr(s, "skill_type", "") == "freeze":
                score += 10
            scored.append((score, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        picked = [item[1] for item in scored[:self.hero.max_skill_slots]]
        self.hero.set_equipped_skills(picked)
        self._refresh_views()

    def _preset_origin(self):
        """一鍵本職經典組"""
        cinfo = ALL_CLASSES.get(self.hero.class_id, {})
        my_skills = [s.clone() for s in cinfo.get("skills", [])]
        self.hero.set_equipped_skills(my_skills[:self.hero.max_skill_slots])
        self._refresh_views()
