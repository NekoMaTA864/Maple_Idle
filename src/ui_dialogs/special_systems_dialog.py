"""
《新楓之谷：放置遠征隊》內潛、寵物與萌獸三大核心系統專屬控制台 (special_systems_dialog.py)
整合原版 TMS 內在能力洗練、寵物出戰與自動喝水、萌獸獨立終傷與潛能洗練
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QTabWidget, QCheckBox, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from ui_styles import QSS_DARK_THEME
from inner_ability import TIER_NAMES, TIER_COLORS
from familiar_system import FAMILIAR_TIER_NAMES, FAMILIAR_TIER_COLORS, TIER_UP_EXP


class SpecialSystemsDialog(QDialog):
    """三大核心系統管理彈窗"""
    def __init__(self, player, sound_mgr=None, parent=None):
        super().__init__(parent)
        self.player = player
        self.sound_mgr = sound_mgr
        self.setWindowTitle("新楓之谷特權系統：內潛 · 寵物 · 萌獸")
        self.resize(700, 750)
        self.setStyleSheet(QSS_DARK_THEME)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # 頂部標題
        title_lbl = QLabel(
            "<b style='font-size: 16px; color: #ecc94b;'>"
            "🍁 新楓之谷巔峰戰力加持 (Inner Ability · Pets · Familiars)</b>"
        )
        main_layout.addWidget(title_lbl)

        # 三大分頁
        self.tabs = QTabWidget()
        self.tab_inner = QWidget()
        self.tab_pet = QWidget()
        self.tab_fam = QWidget()

        self.tabs.addTab(self.tab_inner, "✨ 內在能力 (內潛)")
        self.tabs.addTab(self.tab_pet, "🐾 寵物與月光P寵")
        self.tabs.addTab(self.tab_fam, "🐲 萌獸與獨立終傷")

        main_layout.addWidget(self.tabs)

        self._setup_inner_tab()
        self._setup_pet_tab()
        self._setup_fam_tab()

    # ==================== 1. 內在能力分頁 ====================
    def _setup_inner_tab(self):
        lay = QVBoxLayout(self.tab_inner)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        # 頂部資訊
        self.lbl_ia_info = QLabel()
        lay.addWidget(self.lbl_ia_info)

        # 三排能力卡片容器
        self.frame_lines = QFrame()
        self.frame_lines.setStyleSheet("background-color: #1a2234; border: 1px solid #2d3748; border-radius: 6px; padding: 8px;")
        self.lay_lines = QVBoxLayout(self.frame_lines)
        lay.addWidget(self.frame_lines)

        # 一鍵洗潛目標配置區
        auto_box = QFrame()
        auto_box.setStyleSheet("background-color: #161c28; border: 1px solid #2b4c7e; border-radius: 6px; padding: 8px;")
        ab_lay = QVBoxLayout(auto_box)
        ab_lay.setSpacing(6)
        ab_lay.addWidget(QLabel("<b style='color: #63b3ed; font-size: 12px;'>⚡ 內潛一鍵洗潛配置 (自動洗到出目標為止)</b>"))

        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("目標階級:"))
        self.combo_ia_rank = QComboBox()
        self.combo_ia_rank.addItem("傳說階級 (Legendary)", "legendary")
        self.combo_ia_rank.addItem("罕見階級 (Unique)", "unique")
        self.combo_ia_rank.addItem("任意階級 (不限階級)", "any")
        self.combo_ia_rank.setStyleSheet("background-color: #1a202c; color: #cbd5e1; border: 1px solid #4a5568; padding: 3px;")
        sel_row.addWidget(self.combo_ia_rank)

        sel_row.addWidget(QLabel("目標詞條:"))
        self.combo_ia_stat = QComboBox()
        self.combo_ia_stat.addItem("任意詞條 (只求達標階級)", "any")
        self.combo_ia_stat.addItem("略過技能冷卻時間 (無冷 10%~20%)", "cooldown_skip")
        self.combo_ia_stat.addItem("BOSS 怪物傷害增加 (B傷 10%~20%)", "boss_damage")
        self.combo_ia_stat.addItem("增益效果持續時間增加 (加持 35%~50%)", "buff_duration")
        self.combo_ia_stat.addItem("攻擊速度增加 (攻速提升)", "attack_speed")
        self.combo_ia_stat.addItem("被動技能等級提升 +1 (全隊增傷)", "passive_level")
        self.combo_ia_stat.addItem("爆擊機率增加 (+18%~30%)", "crit_chance")
        self.combo_ia_stat.addItem("物理/魔法攻擊力增加 (+20~30)", "attack")
        self.combo_ia_stat.addItem("無視目標怪物防禦力 (+10%~20%)", "def_ignore")
        self.combo_ia_stat.addItem("道具掉落率增加 (+12%~20%)", "drop_rate")
        self.combo_ia_stat.addItem("楓幣獲得量增加 (+12%~20%)", "meso_rate")
        self.combo_ia_stat.setStyleSheet("background-color: #1a202c; color: #cbd5e1; border: 1px solid #4a5568; padding: 3px;")
        sel_row.addWidget(self.combo_ia_stat)

        ab_lay.addLayout(sel_row)

        btn_bar = QHBoxLayout()
        self.btn_auto_ia = QPushButton("⚡ 開始一鍵洗潛 (洗到出目標為止)")
        self.btn_auto_ia.setStyleSheet("background-color: #b7791f; color: white; font-weight: bold; padding: 8px; border-radius: 4px; border: 1px solid #ecc94b;")
        self.btn_auto_ia.clicked.connect(self._on_auto_reroll_ia)
        btn_bar.addWidget(self.btn_auto_ia)

        self.btn_reroll_ia = QPushButton("🎲 單次洗練")
        self.btn_reroll_ia.setStyleSheet("background-color: #2b6cb0; color: white; font-weight: bold; padding: 8px; border-radius: 4px;")
        self.btn_reroll_ia.clicked.connect(self._on_reroll_ia)
        btn_bar.addWidget(self.btn_reroll_ia)

        ab_lay.addLayout(btn_bar)
        lay.addWidget(auto_box)

        tip_lbl = QLabel(
            "<span style='color: #a0aec0; font-size: 11px;'>"
            "💡 原版 TMS 規則：升級至傳說階級永不掉階！首排保底傳說，二三排最高罕見；可鎖定最多 2 排。"
            "</span>"
        )
        tip_lbl.setWordWrap(True)
        lay.addWidget(tip_lbl)
        lay.addStretch()

        self._refresh_inner_ui()

    def _refresh_inner_ui(self):
        ia = self.player.inner_ability
        t_name = TIER_NAMES.get(ia.tier, ia.tier)
        r, g, b = TIER_COLORS.get(ia.tier, (255, 255, 255))
        cost = ia.get_reroll_cost()

        self.lbl_ia_info.setText(
            f"當前階級：<b style='color: rgb({r},{g},{b}); font-size: 15px;'>【{t_name}】</b>　"
            f"名譽點數：<b style='color: #ecc94b; font-size: 14px;'>{ia.honor_exp:,}</b> 點　"
            f"(單次消耗: <b style='color: #fc8181;'>{cost:,}</b> 點)"
        )

        # 清空舊排數
        while self.lay_lines.count():
            item = self.lay_lines.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for idx, line in enumerate(ia.lines):
            row = QHBoxLayout()
            lr, lg, lb = TIER_COLORS.get(line.tier, (200, 200, 200))
            line_lbl = QLabel(
                f"<b style='color: rgb({lr},{lg},{lb}); font-size: 13px;'>第 {idx + 1} 排：</b> "
                f"<span style='color: #e2e8f0; font-size: 13px;'>{line.display_text}</span>"
            )
            row.addWidget(line_lbl, 1)

            cb = QCheckBox("鎖定")
            cb.setChecked(line.locked)
            cb.setStyleSheet("color: #ecc94b; font-weight: bold;")
            cb.toggled.connect(lambda checked, i=idx: self._on_toggle_ia_lock(i))
            row.addWidget(cb)

            self.lay_lines.addLayout(row)

    def _on_toggle_ia_lock(self, idx):
        ia = self.player.inner_ability
        ok, msg = ia.toggle_lock(idx)
        if not ok:
            QMessageBox.warning(self, "提示", msg)
        self._refresh_inner_ui()

    def _on_reroll_ia(self):
        ia = self.player.inner_ability
        ok, msg = ia.reroll()
        if not ok:
            QMessageBox.warning(self, "洗練失敗", msg)
            return
        if self.sound_mgr:
            self.sound_mgr.play("levelup" if "突破" in msg else "loot")
        self._refresh_inner_ui()

    def _on_auto_reroll_ia(self):
        ia = self.player.inner_ability
        tgt_tier = self.combo_ia_rank.currentData()
        tgt_stat = self.combo_ia_stat.currentData()
        success, msg = ia.auto_reroll(target_stat=tgt_stat, target_tier=tgt_tier)
        if success:
            if self.sound_mgr:
                self.sound_mgr.play("levelup")
            QMessageBox.information(self, "一鍵洗內潛結果", msg)
        else:
            if self.sound_mgr:
                self.sound_mgr.play("hit")
            QMessageBox.warning(self, "一鍵洗內潛中斷/提示", msg)
        self._refresh_inner_ui()

    # ==================== 2. 寵物系統分頁 ====================
    def _setup_pet_tab(self):
        lay = QVBoxLayout(self.tab_pet)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        self.lbl_pet_info = QLabel()
        lay.addWidget(self.lbl_pet_info)

        # 寵物列表滾動區
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.lay_pet_list = QVBoxLayout(content)
        scroll.setWidget(content)
        lay.addWidget(scroll, 1)

        tip_lbl = QLabel(
            "<span style='color: #a0aec0; font-size: 11px;'>"
            "💡 原版 TMS 規則：最多 3 隻寵物同時出戰！3 隻月光小寵物 (P寵) 同場可觸發【月光祝福】全隊攻擊力+30、全圖磁吸吸寶+30% 金幣！"
            "</span>"
        )
        tip_lbl.setWordWrap(True)
        lay.addWidget(tip_lbl)

        self._refresh_pet_ui()

    def _refresh_pet_ui(self):
        pm = self.player.pet_manager
        p_count = pm.get_luna_petite_count()
        set_atk = pm.get_luna_set_attack()
        loot_mult = pm.get_loot_multiplier()

        self.lbl_pet_info.setText(
            f"出戰中寵物：<b style='color: #68d391;'>{len(pm.get_active_pets())}/3</b> 隻　"
            f"超級藥水庫存：<b style='color: #63b3ed;'>{pm.potions:,}</b> 瓶　"
            f"P寵磁吸收益：<b style='color: #ecc94b;'>{loot_mult:.2f}×</b><br>"
            f"月光祝福套裝加成：<b style='color: #b794f4;'>全隊攻擊力 +{set_atk}</b>"
        )

        while self.lay_pet_list.count():
            item = self.lay_pet_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for pet in pm.pets:
            f = QFrame()
            border_col = "#b794f4" if pet.is_luna else "#4a5568"
            f.setStyleSheet(f"background-color: #1a2234; border: 1px solid {border_col}; border-radius: 6px; padding: 6px;")
            f_lay = QHBoxLayout(f)

            type_tag = "<b style='color: #b794f4;'>[月光P寵]</b>" if pet.is_luna else "<span style='color: #a0aec0;'>[一般寵物]</span>"
            status_tag = "<b style='color: #68d391;'>【出戰中】</b>" if pet.is_active else "<span style='color: #718096;'>【休息】</span>"
            eq_color = "#b794f4" if pet.is_luna or any(k in pet.equip_name for k in ["魔精", "迷蝶", "星辰"]) else "#f6ad55"
            luna_gear_tag = " <span style='color: #ecc94b; font-weight: bold;'>[✨ 月光專屬神裝]</span>" if eq_color == "#b794f4" else ""
            p_desc = (
                f"{type_tag} <b>{pet.name}</b> {status_tag}<br>"
                f"<span style='color: #cbd5e0; font-size: 11px;'>"
                f"自動補水閾值: 低於 {int(pet.auto_potion_hp*100)}% HP 自動喝水 | 裝備: <b style='color:{eq_color};'>{pet.equip_name}</b>{luna_gear_tag} (飾品攻: +{pet.equip_atk}，剩餘衝卷: {pet.scroll_slots_left})</span>"
            )
            lbl = QLabel(p_desc)
            f_lay.addWidget(lbl, 1)

            # 衝卷按鈕
            btn_scroll = QPushButton("📜 飾品衝卷")
            btn_scroll.setEnabled(pet.scroll_slots_left > 0)
            btn_scroll.clicked.connect(lambda _, p=pet: self._on_scroll_pet(p))
            f_lay.addWidget(btn_scroll)

            # 出戰/收回按鈕
            btn_toggle = QPushButton("收回" if pet.is_active else "出戰")
            btn_toggle.setStyleSheet(
                "background-color: #e53e3e; color: white;" if pet.is_active
                else "background-color: #38a169; color: white;"
            )
            btn_toggle.clicked.connect(lambda _, p=pet: self._on_toggle_pet(p))
            f_lay.addWidget(btn_toggle)

            self.lay_pet_list.addWidget(f)

        self.lay_pet_list.addStretch()

    def _on_toggle_pet(self, pet):
        pm = self.player.pet_manager
        ok, msg = pm.set_pet_active(pet.pet_id, not pet.is_active)
        if not ok:
            QMessageBox.warning(self, "提示", msg)
        self._refresh_pet_ui()

    def _on_scroll_pet(self, pet):
        ok, msg = pet.scroll_equip()
        if not ok:
            QMessageBox.warning(self, "強化失敗", msg)
        else:
            if self.sound_mgr:
                self.sound_mgr.play("upgrade")
        self._refresh_pet_ui()

    # ==================== 3. 萌獸系統分頁 ====================
    def _setup_fam_tab(self):
        lay = QVBoxLayout(self.tab_fam)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        self.lbl_fam_info = QLabel()
        lay.addWidget(self.lbl_fam_info)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.lay_fam_list = QVBoxLayout(content)
        scroll.setWidget(content)
        lay.addWidget(scroll, 1)

        tip_lbl = QLabel(
            "<span style='color: #a0aec0; font-size: 11px;'>"
            "💡 原版 TMS 獨佔超核心：最終傷害 (終傷 %) 採<b>獨立相乘</b>計算！"
            "神級【雙終】與【👑 傳奇三終】可帶來翻倍的極致輸出爆發！每 4 秒定時回復全隊生命值。"
            "</span>"
        )
        tip_lbl.setWordWrap(True)
        lay.addWidget(tip_lbl)

        self._refresh_fam_ui()

    def _refresh_fam_ui(self):
        fm = self.player.familiar_manager
        fd_mult = fm.get_final_damage_multiplier()
        fd_gain_pct = int(round((fd_mult - 1.0) * 100))
        regen = fm.get_stat_sum("team_hp_regen")

        self.lbl_fam_info.setText(
            f"已召喚萌獸：<b style='color: #68d391;'>{len(fm.get_summoned_familiars())}/1</b> 隻 (同時間僅限 1 隻主戰萌獸生效)　"
            f"神奇萌獸方塊：<b style='color: #f687b3;'>{fm.familiar_cubes:,}</b> 顆<br>"
            f"🔥 <b>獨立終傷乘區：+{fd_gain_pct}% (×{fd_mult:.3f})</b>　"
            f"💚 <b>全隊定時光環回復：每 4 秒 +{int(round(regen*100))}% HP</b>"
        )

        while self.lay_fam_list.count():
            item = self.lay_fam_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for fam in fm.familiars:
            f = QFrame()
            r, g, b = FAMILIAR_TIER_COLORS.get(fam.tier, (160, 160, 160))
            f.setStyleSheet(f"background-color: #1a2234; border: 1px solid rgb({r},{g},{b}); border-radius: 6px; padding: 8px;")
            f_lay = QVBoxLayout(f)

            top_h = QHBoxLayout()
            t_name = FAMILIAR_TIER_NAMES.get(fam.tier, fam.tier)
            status_str = "<b style='color: #68d391;'>【主戰中】</b>" if fam.is_summoned else "<span style='color: #718096;'>【卡冊休眠】</span>"
            tag_str = f" <span style='color: #ffd700; font-weight: bold;'>{fam.tag_summary}</span>" if fam.tag_summary else ""
            t_exp_need = TIER_UP_EXP.get(fam.tier, 999999)
            exp_str = f" <span style='color: #a0aec0; font-size: 11px;'>[升階: {fam.exp}/{t_exp_need} EXP]</span>" if fam.tier != "legendary" else " <span style='color: #68d391; font-size: 11px;'>[最高傳說]</span>"

            name_lbl = QLabel(
                f"<b style='color: rgb({r},{g},{b}); font-size: 14px;'>[{t_name}] {fam.name}</b> "
                f"{status_str}{tag_str}{exp_str}"
            )
            top_h.addWidget(name_lbl, 1)

            btn_auto_c = QPushButton("⚡ 一鍵洗潛")
            btn_auto_c.setStyleSheet("background-color: #b7791f; color: white; font-weight: bold; border: 1px solid #ecc94b; padding: 4px 8px; border-radius: 3px;")
            btn_auto_c.clicked.connect(lambda _, fm_obj=fam: self._on_auto_cube_fam(fm_obj))
            top_h.addWidget(btn_auto_c)

            if fam.tier != "legendary":
                btn_feed = QPushButton("🍖 吞噬升階")
                btn_feed.setStyleSheet("background-color: #276749; color: #c6f6d5; border: 1px solid #48bb78; padding: 4px 8px; border-radius: 3px; font-weight: bold;")
                btn_feed.setToolTip("吞噬卡冊中所有未出戰的低階萌獸 (普通/特殊) 獲得經驗！")
                btn_feed.clicked.connect(lambda _, fm_obj=fam: self._on_feed_fam(fm_obj))
                top_h.addWidget(btn_feed)

            btn_reroll = QPushButton("🎴 單次洗潛")
            btn_reroll.setStyleSheet("background-color: #2b6cb0; color: white; padding: 4px 8px; border-radius: 3px;")
            btn_reroll.clicked.connect(lambda _, fm_obj=fam: self._on_reroll_fam(fm_obj))
            top_h.addWidget(btn_reroll)

            btn_summon = QPushButton("收回" if fam.is_summoned else "召喚出戰")
            btn_summon.setStyleSheet(
                "background-color: #e53e3e; color: white; padding: 4px 8px; border-radius: 3px; font-weight: bold;" if fam.is_summoned
                else "background-color: #38a169; color: white; padding: 4px 8px; border-radius: 3px; font-weight: bold;"
            )
            btn_summon.clicked.connect(lambda _, fm_obj=fam: self._on_toggle_summon(fm_obj))
            top_h.addWidget(btn_summon)

            f_lay.addLayout(top_h)

            # 顯示三排潛能
            for p_idx, line in enumerate(fam.lines):
                pot_lbl = QLabel(
                    f"<span style='color: #cbd5e0; font-size: 12px;'>"
                    f"• {line.display_text}</span>"
                )
                f_lay.addWidget(pot_lbl)

            self.lay_fam_list.addWidget(f)

        self.lay_fam_list.addStretch()

    def _on_toggle_summon(self, fam):
        fm = self.player.familiar_manager
        ok, msg = fm.set_summoned(fam.fid, not fam.is_summoned)
        if not ok:
            QMessageBox.warning(self, "提示", msg)
        self._refresh_fam_ui()

    def _on_reroll_fam(self, fam):
        fm = self.player.familiar_manager
        if fm.familiar_cubes <= 0:
            QMessageBox.warning(self, "道具不足", "神奇萌獸方塊已用盡！可在轉蛋屋商城購買補充！")
            return

        fm.familiar_cubes -= 1
        ok, msg = fam.reroll_potentials()
        if self.sound_mgr:
            self.sound_mgr.play("levelup" if "突破" in msg or "終" in msg else "loot")
        self._refresh_fam_ui()

    def _on_auto_cube_fam(self, fam):
        from PySide6.QtWidgets import QInputDialog
        options = [
            "✨ 洗出最終傷害 (至少 1 排終傷)",
            "⭐ 雙終極品 (洗出雙排終傷)",
            "👑 傳奇三終 (洗出三排終傷)",
            "⚔️ BOSS 怪物傷害 (+10%~40%)",
            "🌟 突破至傳說階級"
        ]
        modes = ["any_fd", "double_final", "triple_final", "boss_damage", "legendary"]
        item, ok = QInputDialog.getItem(self, "萌獸一鍵洗潛", f"請為【{fam.name}】選擇目標潛能條件：", options, 0, False)
        if not ok or not item:
            return
        idx = options.index(item)
        mode = modes[idx]
        fm = self.player.familiar_manager
        success, msg = fam.auto_reroll_potentials(fm, target_mode=mode)
        if success:
            if self.sound_mgr:
                self.sound_mgr.play("levelup")
            QMessageBox.information(self, "萌獸一鍵洗潛結果", msg)
        else:
            if self.sound_mgr:
                self.sound_mgr.play("hit")
            QMessageBox.warning(self, "萌獸一鍵洗潛中斷", msg)
        self._refresh_fam_ui()

    def _on_feed_fam(self, fam):
        fm = self.player.familiar_manager
        ok, msg = fm.batch_feed_low_tier(fam.fid)
        if ok:
            if self.sound_mgr:
                self.sound_mgr.play("levelup")
            QMessageBox.information(self, "吞噬升階成功", msg)
        else:
            QMessageBox.warning(self, "吞噬升階提示", msg)
        self._refresh_fam_ui()

