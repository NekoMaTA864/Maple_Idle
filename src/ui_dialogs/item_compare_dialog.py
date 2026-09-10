"""
《新楓之谷：放置遠征隊》裝備詳細對比與鍛造洗潛對話框 (item_compare_dialog.py)
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QMessageBox, QScrollArea, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from settings import (
    COLOR_COMMON, COLOR_UNCOMMON, COLOR_RARE, COLOR_EPIC, COLOR_LEGENDARY,
    COLOR_GREEN_STAT, COLOR_RED_STAT
)
from item_system import (
    compare_stats, SLOT_NAMES, CATEGORY_TO_SLOTS, SLOT_TO_CATEGORY, SET_DEFINITIONS,
    CUBE_COSTS, POTENTIAL_RANK_INFO, POTENTIAL_RANKS, ABBY_SCROLLS
)
from player_gear import ensure_player_slots
from ui_styles import QSS_DARK_THEME
from ui_dialogs.auto_cube_dialog import AutoCubeDialog


class ItemCompareDialog(QDialog):
    def __init__(self, item, player, on_equip=None, on_unequip=None, on_sell=None, on_enhance=None, slot_k=None, is_equipped=None, parent=None):
        super().__init__(parent)
        self.item = item
        self.player = player
        self.on_equip = on_equip
        self.on_unequip = on_unequip
        self.on_sell = on_sell
        self.on_enhance = on_enhance
        self.slot_k = slot_k
        if is_equipped is not None:
            self.is_equipped = is_equipped
        else:
            self.is_equipped = False
            if slot_k and player and hasattr(player, "equipped"):
                if player.equipped.get(slot_k) is item and item is not None:
                    self.is_equipped = True
            elif slot_k is not None and item is not None:
                if hasattr(player, "inventory") and item in player.inventory:
                    self.is_equipped = False
                else:
                    self.is_equipped = True

        ensure_player_slots(self.player)

        self.setWindowTitle("新楓之谷裝備與欄位鍛造面板")
        self.resize(580, 800)
        self.setMinimumSize(500, 620)
        self.setStyleSheet(QSS_DARK_THEME)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(8)

        self._build_ui()

    def _build_ui(self):
        # 清除現有元件
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_widget = QWidget()
        content_layout = QVBoxLayout(scroll_widget)
        content_layout.setContentsMargins(4, 4, 8, 4)
        content_layout.setSpacing(8)

        item = self.item
        slot_k = self.slot_k
        slot_star = self.player.slot_enhancements.get(slot_k, 0) if (slot_k and self.is_equipped) else 0
        s_pots = self.player.slot_potentials.get(slot_k) if (slot_k and self.is_equipped and hasattr(self.player, "slot_potentials")) else None
        s_scrolls = self.player.slot_scrolls.get(slot_k) if (slot_k and self.is_equipped and hasattr(self.player, "slot_scrolls")) else None

        # 1. 標題與基本部位
        s_name = SLOT_NAMES.get(slot_k or (item.slot if item else "weapon"), "裝備")
        if item:
            r, g, b = item.color[:3]
            title_str = item.full_name
            req_lvl = getattr(item, "level_req", item.item_level)
            lvl_ok = self.player.level >= req_lvl
            lvl_col = "#68d391" if lvl_ok else "#fc8181"
            lvl_tag = f"Lv.{req_lvl}" if lvl_ok else f"Lv.{req_lvl} (遠征隊等級不足，當前 Lv.{self.player.level})"
            req_lvl_str = f"<b style='color: {lvl_col};'>{lvl_tag}</b>"
        else:
            r, g, b = (160, 180, 200)
            title_str = f"【{s_name} 欄位】(未穿戴裝備)"
            req_lvl_str = "<span style='color: #68d391;'>無限制 (強化永久保留)</span>"

        title_lbl = QLabel(f"<b style='font-size: 15px;'>{title_str}</b>")
        title_lbl.setStyleSheet(f"color: rgb({r}, {g}, {b});")
        content_layout.addWidget(title_lbl)

        star_str = f" | 欄位星力: <b style='color: #ffd700;'>★{slot_star}</b>"
        sub_lbl = QLabel(f"部位: {s_name} | 等級需求: {req_lvl_str}{star_str}")
        sub_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        content_layout.addWidget(sub_lbl)

        # 1.5 若尚未穿戴裝備，提供快速穿戴候選框
        if not item and slot_k:
            quick_eq_box = QFrame()
            quick_eq_box.setStyleSheet("background-color: #151b28; border: 1px solid #3182ce; border-radius: 4px; padding: 6px;")
            q_lay = QVBoxLayout(quick_eq_box)
            q_lay.setContentsMargins(6, 4, 6, 4)
            q_lay.setSpacing(4)
            q_lay.addWidget(QLabel("<b style='color: #63b3ed; font-size: 11px;'>【從行囊快速穿戴此部位裝備】:</b>"))

            cat = SLOT_TO_CATEGORY.get(slot_k, slot_k)
            matching_items = [it for it in self.player.inventory if SLOT_TO_CATEGORY.get(it.slot, it.slot) == cat]
            if matching_items:
                for m_it in matching_items[:4]:
                    row = QHBoxLayout()
                    mr, mg, mb = m_it.color[:3]
                    can_wear = self.player.level >= getattr(m_it, "level_req", 1)
                    name_lbl = QLabel(f"• {m_it.full_name} (Lv.{m_it.level_req})")
                    name_lbl.setStyleSheet(f"color: rgb({mr},{mg},{mb}); font-size: 11px;")
                    row.addWidget(name_lbl)
                    row.addStretch()
                    btn_quick = QPushButton("穿戴" if can_wear else "等級不足")
                    btn_quick.setEnabled(can_wear)
                    btn_quick.setStyleSheet("background-color: #2b6cb0; color: #fff; padding: 2px 8px; font-size: 10px;" if can_wear else "background-color: #2d3748; color: #718096; padding: 2px 8px; font-size: 10px;")
                    def _do_quick_equip(it_to_eq=m_it):
                        self.player.equip_item(it_to_eq, target_slot=slot_k)
                        self.item = self.player.equipped.get(slot_k)
                        self.is_equipped = True
                        self._build_ui()
                    btn_quick.clicked.connect(_do_quick_equip)
                    row.addWidget(btn_quick)
                    q_lay.addLayout(row)
            else:
                q_lay.addWidget(QLabel("<span style='color: #718096; font-size: 10px;'>行囊中目前無符合此部位之裝備</span>"))
            content_layout.addWidget(quick_eq_box)

        # 2. 艾比卷軸強化展示框 (Abby Scrolls)
        if slot_k and s_scrolls:
            sc_cnt = s_scrolls.get("count", 0)
            sc_max = s_scrolls.get("max_count", 10)
            sc_frame = QFrame()
            sc_frame.setStyleSheet("background-color: #121826; border: 1.5px solid #ecc94b; border-radius: 6px; padding: 6px;")
            scf_layout = QVBoxLayout(sc_frame)
            scf_layout.setContentsMargins(6, 4, 6, 4)
            scf_layout.setSpacing(4)

            scf_layout.addWidget(QLabel(f"<b style='color: #ecc94b; font-size: 12px;'>【台服艾比卷軸強化】: {sc_cnt}/{sc_max} 次</b> <span style='color: #a0aec0; font-size: 10px;'>(優先扣除庫存)</span>"))
            sc_stats = s_scrolls.get("stats", {})
            if sc_stats:
                s_desc = ", ".join([f"{k}:+{v}" for k, v in sc_stats.items()])
                scf_layout.addWidget(QLabel(f"<span style='color: #e2e8f0; font-size: 11px;'>  • 卷軸加成累積：{s_desc}</span>"))
            else:
                scf_layout.addWidget(QLabel("<span style='color: #718096; font-size: 10px;'>  • 尚未施加艾比卷軸強化 (可注入極電/R/X/V/黑卷B)</span>"))

            # 卷軸注入按鈕列
            if sc_cnt < sc_max:
                sc_btn_row = QHBoxLayout()
                for s_key in ["electric", "R", "X", "V", "B"]:
                    s_info = ABBY_SCROLLS[s_key]
                    stock = getattr(self.player, "abby_scrolls", {}).get(s_key, 0)
                    tag = f"(存:{stock})" if stock > 0 else f"(${s_info['cost']//1000}K)"
                    b = QPushButton(f"{s_info['name'][:3]} {tag}")
                    if stock > 0:
                        b.setStyleSheet("background-color: #22543d; color: #9ae6b4; border: 1px solid #38a169; font-size: 10px; padding: 3px; font-weight: bold;")
                    else:
                        b.setStyleSheet("background-color: #1a202c; color: #feebc8; border: 1px solid #d69e2e; font-size: 10px; padding: 3px;")
                    b.clicked.connect(lambda _, k=s_key: self._apply_scroll(k))
                    sc_btn_row.addWidget(b)
                scf_layout.addLayout(sc_btn_row)

            # 回真卷軸按鈕 (當該欄位已有衝卷次數時可重置)
            if sc_cnt > 0:
                inno_stock = getattr(self.player, "abby_scrolls", {}).get("innocence", 0)
                inno_tag = f"(存:{inno_stock})" if inno_stock > 0 else "($100K)"
                btn_inno = QPushButton(f"🔄 回真卷軸 {inno_tag} (重置次數)")
                btn_inno.setToolTip("重置此欄位的艾比卷軸次數與加成屬性，回歸 0/10 次 (星力與潛能不受影響)")
                if inno_stock > 0:
                    btn_inno.setStyleSheet("background-color: #2c1a24; color: #fed7d7; border: 1.5px solid #e53e3e; font-size: 10px; padding: 4px; font-weight: bold; border-radius: 4px;")
                else:
                    btn_inno.setStyleSheet("background-color: #1a1622; color: #feebc8; border: 1px solid #d69e2e; font-size: 10px; padding: 4px; border-radius: 4px;")
                btn_inno.clicked.connect(self._confirm_innocence_scroll)
                scf_layout.addWidget(btn_inno)

            content_layout.addWidget(sc_frame)

        # 3. 正統新楓之谷【主潛能】展示框 (Main Potential)
        main_pot = s_pots.get("main", {}) if s_pots else {"rank": getattr(item, 'potential_rank', 'rare'), "lines": getattr(item, 'potential_lines', [])}
        main_rank = main_pot.get("rank", "rare")
        main_info = POTENTIAL_RANK_INFO.get(main_rank, POTENTIAL_RANK_INFO['rare'])
        main_qcol = main_info.get("qcolor", "#4299e1")
        main_name = main_info.get("name", "特殊")

        pot_frame = QFrame()
        pot_frame.setStyleSheet(f"background-color: #121622; border: 1.5px solid {main_qcol}; border-radius: 6px; padding: 6px;")
        pf_layout = QVBoxLayout(pot_frame)
        pf_layout.setContentsMargins(8, 6, 8, 6)
        pf_layout.setSpacing(4)

        p_head = QHBoxLayout()
        p_head.addWidget(QLabel(f"<b style='color: {main_qcol}; font-size: 13px;'>【主潛能：{main_name}】</b> <span style='color: #a0aec0; font-size: 10px;'>(欄位永久綁定)</span>"))
        p_head.addStretch()
        pf_layout.addLayout(p_head)

        for l in main_pot.get("lines", []):
            pf_layout.addWidget(QLabel(f"  <b style='color: #e2e8f0; font-size: 11px;'>• {l.get('name', '')}</b>"))

        # 洗主潛能按鈕
        c_row = QHBoxLayout()
        m_st = getattr(self.player, "cube_inventory", {}).get("mystic", 0)
        btn_mystic = QPushButton(f"🎲 楓方塊 (存:{m_st})" if m_st > 0 else "🎲 楓方塊 ($6K)")
        btn_mystic.setStyleSheet("background-color: #2b6cb0; color: #ebf8ff; border: 1px solid #4299e1; padding: 4px; font-weight: bold; font-size: 10px;")
        btn_mystic.clicked.connect(lambda: self._cube_roll("mystic", is_bonus=False))
        c_row.addWidget(btn_mystic)

        br_st = getattr(self.player, "cube_inventory", {}).get("bright", 0)
        btn_bright = QPushButton(f"✨ 閃耀方塊 (存:{br_st})" if br_st > 0 else "✨ 閃耀方塊 ($30K)")
        btn_bright.setStyleSheet("background-color: #553c9a; color: #faf5ff; border: 1px solid #9f7aea; padding: 4px; font-weight: bold; font-size: 10px;")
        btn_bright.clicked.connect(lambda: self._cube_roll("bright", is_bonus=False))
        c_row.addWidget(btn_bright)

        btn_auto_c = QPushButton("🔮 一鍵洗主潛")
        btn_auto_c.setStyleSheet("background-color: #285e61; color: #e6fffa; border: 1px solid #38b2ac; padding: 4px; font-weight: bold; font-size: 10px;")
        btn_auto_c.clicked.connect(lambda: self._open_auto_cube(is_bonus=False))
        c_row.addWidget(btn_auto_c)
        pf_layout.addLayout(c_row)
        content_layout.addWidget(pot_frame)

        # 4. 正統新楓之谷【附加潛能】展示框 (Bonus Potential)
        if s_pots:
            bonus_pot = s_pots.get("bonus", {})
            b_rank = bonus_pot.get("rank", "rare")
            b_info = POTENTIAL_RANK_INFO.get(b_rank, POTENTIAL_RANK_INFO['rare'])
            b_qcol = b_info.get("qcolor", "#48bb78")
            b_name = b_info.get("name", "特殊")

            b_frame = QFrame()
            b_frame.setStyleSheet(f"background-color: #121820; border: 1.5px solid {b_qcol}; border-radius: 6px; padding: 6px;")
            bf_layout = QVBoxLayout(b_frame)
            bf_layout.setContentsMargins(8, 6, 8, 6)
            bf_layout.setSpacing(4)

            bp_head = QHBoxLayout()
            bp_head.addWidget(QLabel(f"<b style='color: {b_qcol}; font-size: 13px;'>【附加潛能：{b_name}】</b> <span style='color: #a0aec0; font-size: 10px;'>(微型屬性加成)</span>"))
            bp_head.addStretch()
            bf_layout.addLayout(bp_head)

            for l in bonus_pot.get("lines", []):
                bf_layout.addWidget(QLabel(f"  <b style='color: #cbd5e1; font-size: 11px;'>• {l.get('name', '')}</b>"))

            bc_row = QHBoxLayout()
            bo_st = getattr(self.player, "cube_inventory", {}).get("bonus_occult", 0)
            btn_b_mystic = QPushButton(f"📦 可疑附加 (存:{bo_st})" if bo_st > 0 else "📦 可疑附加 ($15K)")
            btn_b_mystic.setStyleSheet("background-color: #2c5282; color: #e2e8f0; border: 1px solid #63b3ed; padding: 4px; font-weight: bold; font-size: 10px;")
            btn_b_mystic.clicked.connect(lambda: self._cube_roll("bonus_occult", is_bonus=True))
            bc_row.addWidget(btn_b_mystic)

            bb_st = getattr(self.player, "cube_inventory", {}).get("bonus_bright", 0)
            btn_b_bright = QPushButton(f"🌟 閃耀附加 (存:{bb_st})" if bb_st > 0 else "🌟 閃耀附加 ($50K)")
            btn_b_bright.setStyleSheet("background-color: #6b46c1; color: #faf5ff; border: 1px solid #b794f4; padding: 4px; font-weight: bold; font-size: 10px;")
            btn_b_bright.clicked.connect(lambda: self._cube_roll("bonus_bright", is_bonus=True))
            bc_row.addWidget(btn_b_bright)

            btn_b_auto = QPushButton("🔮 一鍵洗附加")
            btn_b_auto.setStyleSheet("background-color: #234e52; color: #b2f5ea; border: 1px solid #4fd1c5; padding: 4px; font-weight: bold; font-size: 10px;")
            btn_b_auto.clicked.connect(lambda: self._open_auto_cube(is_bonus=True))
            bc_row.addWidget(btn_b_auto)
            bf_layout.addLayout(bc_row)
            content_layout.addWidget(b_frame)

        # 5. 套裝資訊展示
        if item and item.set_id and item.set_id in SET_DEFINITIONS:
            s_def = SET_DEFINITIONS[item.set_id]
            cnt = sum(1 for it in self.player.equipped.values() if it and getattr(it, 'set_id', None) == item.set_id)
            sr, sg, sb = s_def["color"]
            set_box = QFrame()
            set_box.setStyleSheet(f"background-color: #121826; border: 1px solid rgba({sr},{sg},{sb},0.5); border-radius: 4px; padding: 4px;")
            sb_layout = QVBoxLayout(set_box)
            sb_layout.setContentsMargins(6, 4, 6, 4)
            sb_layout.setSpacing(2)
            sb_layout.addWidget(QLabel(f"<b style='color: rgb({sr},{sg},{sb}); font-size: 11px;'>【{s_def['name']}】</b> <span style='color: #ecc94b;'>(目前穿戴 {cnt} 件)</span>"))
            for req, data in sorted(s_def["tiers"].items()):
                tier_act = "color: #68d391; font-weight: bold;" if cnt >= req else "color: #718096;"
                act_tag = "[已啟動]" if cnt >= req else "[未達成]"
                sb_layout.addWidget(QLabel(f"<span style='{tier_act} font-size: 10px;'>• {req}件套 {act_tag}: {data['desc']}</span>"))
            content_layout.addWidget(set_box)

        # 6. 數值對比區 (含星力、卷軸與潛能計算)
        if item:
            diff_frame = QFrame()
            diff_frame.setStyleSheet("background-color: #141824; border: 1px solid #2a3447; border-radius: 6px; padding: 6px;")
            df_layout = QVBoxLayout(diff_frame)
            df_layout.setSpacing(3)
            df_layout.addWidget(QLabel("<b style='color: #ecc94b; font-size: 11px;'>裝備實際生效總數值 (含星力/卷軸/潛能):</b>"))

            curr_eff = item.get_effective_stats(star_level=slot_star, slot_potentials=s_pots, slot_scrolls=s_scrolls)
            for k, v in curr_eff.items():
                if isinstance(v, float):
                    stat_str = f"{k}: {v:.2f}"
                else:
                    stat_str = f"{k}: {v}"
                row = QHBoxLayout()
                row.addWidget(QLabel(stat_str))
                df_layout.addLayout(row)
            content_layout.addWidget(diff_frame)

        # 7. 星力強化列 (支援欄位星力強化，限已穿戴欄位)
        if slot_k and self.is_equipped and slot_star < 25:
            cost = self.player.get_slot_enhance_cost(self.slot_k)
            rate = int(self.player.get_slot_enhance_success_rate(self.slot_k) * 100)
            star_row = QHBoxLayout()
            btn_enh = QPushButton(f"★ 升星 (★{slot_star+1}, 機率:{rate}%, ${cost:,})")
            btn_enh.setStyleSheet("background-color: #744210; color: #feebc8; border: 1px solid #d69e2e; padding: 5px;")
            btn_enh.setEnabled(self.player.can_enhance_slot(self.slot_k))
            btn_enh.clicked.connect(self._enhance_clicked)
            star_row.addWidget(btn_enh)

            btn_auto_15 = QPushButton("⚡ 一鍵★15")
            btn_auto_15.setStyleSheet("background-color: #744210; color: #ffffff; border: 1px solid #d69e2e; padding: 5px; font-weight: bold;")
            btn_auto_15.clicked.connect(lambda: self._auto_enhance_to(15))
            star_row.addWidget(btn_auto_15)

            btn_auto_20 = QPushButton("⚡ 一鍵★20")
            btn_auto_20.setStyleSheet("background-color: #975a16; color: #ffffff; border: 1px solid #ecc94b; padding: 5px; font-weight: bold;")
            btn_auto_20.clicked.connect(lambda: self._auto_enhance_to(20))
            star_row.addWidget(btn_auto_20)

            btn_auto_25 = QPushButton("⚡ 一鍵★25")
            btn_auto_25.setStyleSheet("background-color: #b7791f; color: #ffffff; border: 1px solid #f6e05e; padding: 5px; font-weight: bold;")
            btn_auto_25.clicked.connect(lambda: self._auto_enhance_to(25))
            star_row.addWidget(btn_auto_25)
            content_layout.addLayout(star_row)

        content_layout.addStretch()
        scroll.setWidget(scroll_widget)
        self.main_layout.addWidget(scroll, 1)

        # 8. 操作按鈕列 (綠鎖/卸下/穿戴/出售/關閉)
        btn_layout = QHBoxLayout()
        if self.is_equipped:
            btn_uneq = QPushButton("卸下裝備")
            btn_uneq.setStyleSheet("background-color: #2d3748; color: #cbd5e1; border: 1px solid #4a5568; padding: 6px;")
            btn_uneq.clicked.connect(self._unequip_clicked)
            btn_layout.addWidget(btn_uneq)
        elif item:
            # 綠鎖切換按鈕
            is_locked = getattr(item, "locked", False)
            lock_text = "🔓 解除綠鎖" if is_locked else "🔒 綠鎖鎖定"
            lock_style = "background-color: #276749; color: #c6f6d5; border: 1px solid #48bb78; padding: 6px;" if is_locked else "background-color: #2d3748; color: #e2e8f0; border: 1px solid #4a5568; padding: 6px;"
            btn_lock = QPushButton(lock_text)
            btn_lock.setStyleSheet(lock_style)
            btn_lock.clicked.connect(self._toggle_lock_clicked)
            btn_layout.addWidget(btn_lock)

            btn_eq = QPushButton("穿戴裝備")
            btn_eq.setStyleSheet("background-color: #1c4532; color: #c6f6d5; border: 1px solid #38a169; padding: 6px;")
            btn_eq.clicked.connect(self._equip_clicked)
            btn_layout.addWidget(btn_eq)

            btn_sell = QPushButton(f"出售 (${item.sell_price})")
            btn_sell.setEnabled(not is_locked)
            if is_locked:
                btn_sell.setStyleSheet("background-color: #1a202c; color: #718096; border: 1px solid #2d3748; padding: 6px;")
                btn_sell.setToolTip("裝備已上鎖，無法出售")
            else:
                btn_sell.setStyleSheet("background-color: #744210; color: #feebc8; border: 1px solid #d69e2e; padding: 6px;")
            btn_sell.clicked.connect(self._sell_clicked)
            btn_layout.addWidget(btn_sell)

        btn_close = QPushButton("關閉")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        self.main_layout.addLayout(btn_layout)

    def _toggle_lock_clicked(self):
        if self.item:
            from player_gear import toggle_item_lock
            toggle_item_lock(self.item)
            self._build_ui()

    def _confirm_innocence_scroll(self):
        s_name = SLOT_NAMES.get(self.slot_k, self.slot_k)
        ret = QMessageBox.question(
            self,
            "確認使用回真卷軸",
            f"確定要對【{s_name}】使用回真卷軸嗎？\n\n此操作將清空該欄位目前的艾比卷軸次數與所有加成數值！\n(欄位星力與主/附加潛能不受影響，將完整保留)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if ret == QMessageBox.Yes:
            self._apply_scroll("innocence")

    def _apply_scroll(self, scroll_type):
        if self.is_equipped and self.slot_k:
            from player_gear import apply_scroll_to_slot
            success, msg = apply_scroll_to_slot(self.player, self.slot_k, scroll_type)
            title = "回真卷軸重置成功" if scroll_type == "innocence" else "艾比卷軸強化成功"
            err_title = "回真失敗" if scroll_type == "innocence" else "強化失敗"
            if success:
                QMessageBox.information(self, title, msg)
            else:
                QMessageBox.warning(self, err_title, msg)
        elif self.item:
            QMessageBox.information(self, "提示", "艾比卷軸為【欄位永久強化】，請先將此裝備穿戴至對應欄位後即可注入強化！")
        self._build_ui()

    def _cube_roll(self, cube_type, is_bonus=False):
        if self.is_equipped and self.slot_k:
            from player_gear import cube_slot
            success, msg = cube_slot(self.player, self.slot_k, cube_type, is_bonus=is_bonus)
        elif self.item:
            success, msg = self.player.cube_item(self.item, cube_type)
        else:
            success, msg = False, "無目標可洗潛能"
        if success:
            QMessageBox.information(self, "洗潛能結果", msg)
        else:
            QMessageBox.warning(self, "洗潛能失敗", msg)
        self._build_ui()

    def _open_auto_cube(self, is_bonus=False):
        slot_target = self.slot_k if self.is_equipped else None
        dlg = AutoCubeDialog(self.item, self.player, slot_k=slot_target, is_bonus=is_bonus, on_cube_done=self._build_ui, parent=self)
        dlg.exec()
        self._build_ui()

    def _equip_clicked(self):
        if self.on_equip and self.item:
            self.on_equip(self.item)
        self.accept()

    def _unequip_clicked(self):
        if self.on_unequip and self.slot_k:
            self.on_unequip(self.slot_k)
            self.item = None
            self.is_equipped = False
            self._build_ui()

    def _sell_clicked(self):
        if self.on_sell and self.item:
            self.on_sell(self.item)
        self.accept()

    def _enhance_clicked(self):
        if self.slot_k:
            if self.on_enhance:
                self.on_enhance(self.slot_k)
            else:
                success, msg = self.player.enhance_slot(self.slot_k)
                if not success:
                    QMessageBox.warning(self, "升星失敗", msg)
            self._build_ui()

    def _auto_enhance_to(self, target_star: int):
        if self.slot_k:
            curr = self.player.slot_enhancements.get(self.slot_k, 0)
            if curr >= target_star:
                QMessageBox.information(self, "提示", f"該欄位星力已達 ★{curr}，無需升至 ★{target_star}！")
                return
            success, msg = self.player.auto_enhance_slot(self.slot_k, target_star=target_star)
            QMessageBox.information(self, f"一鍵升至 ★{target_star} 結果", msg)
            self._build_ui()

    def _auto_enhance_clicked(self):
        if self.slot_k:
            curr = self.player.slot_enhancements.get(self.slot_k, 0)
            if curr < 15:
                target = 15
            elif curr < 20:
                target = 20
            else:
                target = 25
            self._auto_enhance_to(target)


