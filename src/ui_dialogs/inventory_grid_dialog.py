"""
《新楓之谷：放置遠征隊》60 格網格式冒險行囊背包彈窗 (inventory_grid_dialog.py)
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QMessageBox, QScrollArea, QWidget
)
from PySide6.QtCore import Qt
from item_system import SLOT_NAMES, POTENTIAL_RANK_INFO
from ui_styles import QSS_DARK_THEME
from ui_dialogs.item_compare_dialog import ItemCompareDialog


class InventoryGridDialog(QDialog):
    """60 格網格式冒險行囊背包彈窗 (類似 5x5 裝備格排列，支援點擊檢視/穿戴/強化/鎖定)"""
    def __init__(self, player, win=None, parent=None):
        super().__init__(parent or win)
        self.player = player
        self.win = win
        self.current_filter = "all"

        self.setWindowTitle(f"【冒險行囊背包】 (60格全覽)")
        self.resize(960, 680)
        self.setMinimumSize(880, 580)
        self.setStyleSheet(QSS_DARK_THEME)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 14, 16, 14)
        self.main_layout.setSpacing(10)

        self._build_ui()

    def _build_ui(self):
        # 清空現有子佈局
        while self.main_layout.count() > 0:
            child = self.main_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                while child.layout().count() > 0:
                    c2 = child.layout().takeAt(0)
                    if c2.widget():
                        c2.widget().deleteLater()

        # 1. 頂部狀態與操作列
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        total_cnt = len(self.player.inventory)
        title_lbl = QLabel(f"<b style='font-size: 16px; color: #ffd700;'>🎒 冒險行囊全覽</b> "
                           f"<span style='color: #68d391; font-size: 13px;'>已用容量: <b>{total_cnt}/60</b> 格</span> "
                           f"<span style='color: #ecc94b; font-size: 13px;'>| 行囊金幣: <b>${self.player.gold:,}</b></span>")
        top_bar.addWidget(title_lbl)
        top_bar.addStretch()

        btn_auto_eq = QPushButton("⚡ 一鍵換裝")
        btn_auto_eq.setToolTip("自動搜尋背包與身上裝備，穿戴最高戰力神裝！")
        btn_auto_eq.setStyleSheet("background-color: #2b6cb0; color: #ffffff; border: 1px solid #4299e1; padding: 5px 12px; font-weight: bold; border-radius: 4px;")
        btn_auto_eq.clicked.connect(self._on_auto_equip)
        top_bar.addWidget(btn_auto_eq)

        btn_sell_inf = QPushButton("💰 一鍵售劣")
        btn_sell_inf.setToolTip("自動檢索背包，出售數值低於目前身上穿戴的淘汰裝備 (自動保護綠鎖裝備)")
        btn_sell_inf.setStyleSheet("background-color: #744210; color: #feebc8; border: 1px solid #d69e2e; padding: 5px 12px; font-weight: bold; border-radius: 4px;")
        btn_sell_inf.clicked.connect(self._on_sell_inferior)
        top_bar.addWidget(btn_sell_inf)

        if self.win is not None:
            btn_set_bonus = QPushButton("🛡 套裝效果")
            btn_set_bonus.setToolTip("開啟彈窗查看目前穿戴套裝與下一階效果")
            btn_set_bonus.setStyleSheet("background-color: #4a3b1a; color: #ecc94b; border: 1px solid #b7791f; padding: 5px 12px; font-weight: bold; border-radius: 4px;")
            btn_set_bonus.clicked.connect(self.win._open_set_bonus_dialog)
            top_bar.addWidget(btn_set_bonus)

        btn_close = QPushButton("關閉")
        btn_close.setStyleSheet("background-color: #2d3748; color: #cbd5e0; border: 1px solid #4a5568; padding: 5px 14px; border-radius: 4px;")
        btn_close.clicked.connect(self.accept)
        top_bar.addWidget(btn_close)

        self.main_layout.addLayout(top_bar)

        # 2. 分類篩選列
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(6)
        filters = [
            ("all", f"全部 ({total_cnt})"),
            ("weapon", "武器類"),
            ("armor", "防具類"),
            ("accessory", "飾品類"),
            ("locked", "已鎖定 🔒")
        ]
        for f_key, f_name in filters:
            fb = QPushButton(f_name)
            is_active = (self.current_filter == f_key)
            if is_active:
                fb.setStyleSheet("background-color: #3182ce; color: #ffffff; border: 1px solid #63b3ed; font-weight: bold; padding: 4px 10px; border-radius: 4px; font-size: 11px;")
            else:
                fb.setStyleSheet("background-color: #1e2535; color: #a0aec0; border: 1px solid #2d3748; padding: 4px 10px; border-radius: 4px; font-size: 11px;")
            fb.clicked.connect(lambda _, k=f_key: self._set_filter(k))
            filter_bar.addWidget(fb)
        filter_bar.addStretch()
        self.main_layout.addLayout(filter_bar)

        # 3. 60 格網格滾動區 (5 列 x 12 欄 或 6 列 x 10 欄)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #0f121d; border: 1px solid #242c3d; border-radius: 6px;")

        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setContentsMargins(10, 10, 10, 10)
        grid_layout.setSpacing(6)

        # 根據篩選取得合格裝備
        filtered_items = []
        for it in self.player.inventory:
            if self.current_filter == "all":
                filtered_items.append(it)
            elif self.current_filter == "weapon" and it.slot in ["weapon", "sub_weapon", "sub_weapon1", "sub_weapon2", "sub_weapon3", "emblem"]:
                filtered_items.append(it)
            elif self.current_filter == "armor" and it.slot in ["hat", "top", "bottom", "shoes", "gloves", "cape", "shoulder"]:
                filtered_items.append(it)
            elif self.current_filter == "accessory" and it.slot in ["ring", "pendant", "face", "eye", "earrings", "belt", "pocket", "badge", "badge_chest"]:
                filtered_items.append(it)
            elif self.current_filter == "locked" and getattr(it, "locked", False):
                filtered_items.append(it)

        COLS = 6
        TOTAL_SLOTS = 60

        for slot_idx in range(TOTAL_SLOTS):
            r = slot_idx // COLS
            c = slot_idx % COLS

            if slot_idx < len(filtered_items):
                item = filtered_items[slot_idx]
                r_color = getattr(item, "color", (160, 174, 192))
                q_color = f"rgb({r_color[0]}, {r_color[1]}, {r_color[2]})"
                star_txt = f"★{item.enhance_level} " if item.enhance_level > 0 else ""
                lock_txt = "🔒 " if getattr(item, "locked", False) else ""
                pot_rank = getattr(item, "potential_rank", "rare")
                pot_info = POTENTIAL_RANK_INFO.get(pot_rank, {})
                pot_cn = pot_info.get("name", "特殊")
                pot_qcol = pot_info.get("qcolor", "#4299e1")

                btn = QPushButton()
                btn.setFixedHeight(58)
                btn_txt = (f"<div align='center'>"
                           f"<b style='color: {q_color}; font-size: 11px;'>{lock_txt}{star_txt}{item.base_name[:6]}</b><br/>"
                           f"<span style='color: #718096; font-size: 10px;'>Lv.{item.level_req}</span> "
                           f"<span style='color: {pot_qcol}; font-size: 10px;'>[{pot_cn}]</span>"
                           f"</div>")
                btn.setText("")
                # 使用內部 Label 格式化排版
                btn_lbl = QLabel(btn_txt, btn)
                btn_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
                btn_lbl.setAlignment(Qt.AlignCenter)
                btn_lbl.setGeometry(0, 0, 138, 58)

                btn_style = (f"QPushButton {{ background-color: #161b28; border: 1.5px solid {q_color}; border-radius: 5px; }} "
                             f"QPushButton:hover {{ background-color: #1f273b; border: 2px solid #ffd700; }}")
                btn.setStyleSheet(btn_style)

                # Tooltip 詳細屬性
                eff_stats = item.get_effective_stats()
                stats_str = " | ".join(f"{k}: {v}" for k, v in eff_stats.items() if v)
                tip = f"【{item.full_name}】\n部位: {SLOT_NAMES.get(item.slot, item.slot)}\n需求等級: Lv.{item.level_req}\n數值: {stats_str}\n賣價: ${item.sell_price:,}\n(點擊開啟強化/穿戴/鎖定視窗)"
                btn.setToolTip(tip)

                btn.clicked.connect(lambda _, it_target=item: self._open_item_dialog(it_target))
                grid_layout.addWidget(btn, r, c)
            else:
                empty_btn = QPushButton(f"#{slot_idx+1}")
                empty_btn.setFixedHeight(58)
                empty_btn.setEnabled(False)
                empty_btn.setStyleSheet("background-color: #11141e; border: 1px dashed #242c3d; color: #4a5568; font-size: 11px; border-radius: 5px;")
                grid_layout.addWidget(empty_btn, r, c)

        scroll.setWidget(grid_container)
        self.main_layout.addWidget(scroll, stretch=1)

    def _set_filter(self, f_key):
        self.current_filter = f_key
        self._build_ui()

    def _open_item_dialog(self, item):
        dlg = ItemCompareDialog(
            item,
            self.player,
            slot_k=item.slot if item else None,
            is_equipped=False,
            on_equip=self._on_item_equip,
            on_sell=self._on_item_sell,
            parent=self
        )
        dlg.exec()
        self._build_ui()
        if self.win:
            if hasattr(self.win, "_update_left_column"):
                self.win._update_left_column(force=True)
            if hasattr(self.win, "_rebuild_inventory_ui"):
                self.win._rebuild_inventory_ui()

    def _on_item_equip(self, item):
        from player_gear import equip_item
        success, msg = equip_item(self.player, item)
        if success:
            if self.win and hasattr(self.win, "combat_mgr"):
                self.win.combat_mgr.add_log(f"成功穿戴：{item.full_name}！", (60, 240, 130))
                self.win.sound_mgr.play("levelup")
        else:
            QMessageBox.warning(self, "穿戴失敗", msg)
        self._build_ui()
        if self.win:
            if hasattr(self.win, "_update_left_column"):
                self.win._update_left_column(force=True)

    def _on_item_sell(self, item):
        from player_gear import sell_item
        success, msg = sell_item(self.player, item)
        if success:
            if self.win and hasattr(self.win, "combat_mgr"):
                self.win.combat_mgr.add_log(msg, (255, 215, 60))
                self.win.sound_mgr.play("coin")
        self._build_ui()
        if self.win:
            if hasattr(self.win, "_update_left_column"):
                self.win._update_left_column(force=True)

    def _on_auto_equip(self):
        if self.win and hasattr(self.win, "_auto_equip_all"):
            self.win._auto_equip_all()
        else:
            self.player.auto_equip_best_gear()
        self._build_ui()
        if self.win:
            if hasattr(self.win, "_update_left_column"):
                self.win._update_left_column(force=True)

    def _on_sell_inferior(self):
        if self.win and hasattr(self.win, "_sell_inferior_gear"):
            self.win._sell_inferior_gear()
        else:
            from player_gear import sell_inferior_gear
            sell_inferior_gear(self.player)
        self._build_ui()
        if self.win:
            if hasattr(self.win, "_update_left_column"):
                self.win._update_left_column(force=True)


# =========================================================================
