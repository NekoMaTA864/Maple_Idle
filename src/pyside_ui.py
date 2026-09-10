"""
《新楓之谷：放置遠征隊》PySide6 現代化桌面 GUI 介面系統 (pyside_ui.py)
採用模組化面板架構，由 ui_panels 子套件組裝：
- top_bar.py: 頂部狀態列
- left_column.py: 5x5 裝備欄、套裝加成、背包與符號系統
- center_column.py: 冒險區域、戰鬥畫布、首領資訊與隊伍狀態
- right_column.py: 職業自選網格、技能配置與加點面板
"""

import os
import sys
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
)
from PySide6.QtCore import Qt, QTimer
from item_system import SLOT_NAMES
from player_symbols import ARC_SYMBOLS_DATA, AUT_SYMBOLS_DATA
from ui_styles import QSS_DARK_THEME
from ui_dialogs import (
    AutoCubeDialog, ItemCompareDialog, SetBonusDialog, TrainingDummyDialog,
    SkillDeckDialog, CompanionDialog
)
from ui_panels import (
    build_top_bar, update_top_bar,
    build_left_column, update_left_column, rebuild_inventory_ui,
    build_center_column, update_center_column, update_repeat_button_ui,
    build_right_column, update_right_column, refresh_right_panel
)


class MainWindow(QMainWindow):
    def __init__(self, player, combat_mgr, sound_mgr):
        super().__init__()
        self.player = player
        self.combat_mgr = combat_mgr
        self.sound_mgr = sound_mgr

        self.setWindowTitle("新楓之谷：放置遠征隊 (MapleStory Idle) - 現代桌面旗艦版")
        screen = self.screen() or QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else None
        if available:
            min_width = min(1100, available.width())
            min_height = min(760, available.height())
            self.setMinimumSize(min_width, min_height)
            initial_width = min(1480, max(min_width, int(available.width() * 0.97)))
            initial_height = min(1000, max(min_height, int(available.height() * 0.98)))
            self.resize(initial_width, initial_height)
        else:
            self.resize(1240, 830)
            self.setMinimumSize(1100, 700)
        self.setStyleSheet(QSS_DARK_THEME)

        self.selected_forge_slot = "weapon"
        self.current_tab_slot = 0
        self.right_mode = "team"
        self.last_gachapon_results = []

        # UI 狀態差異快取（消除無變化時重複刷新造成之 CPU 負擔）
        self._last_top_state = None
        self._last_left_state = None
        self._last_zone_state = None

        self._setup_ui()
        self._update_top_bar(force=True)
        self._update_left_column(force=True)
        self._update_center_column(force=True)
        self._update_right_column(force=True)
        self._refresh_right_panel()

        # 33ms 定時器驅動戰鬥循環 (約 30 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._game_loop_tick)
        self.timer.start(33)
        self.last_tick_time = time.time()
        self.last_save_time = time.time()

        combat_mgr.add_log("《新楓之谷：放置遠征隊》PySide6 現代桌面旗艦版啟動！五人冒險隊就緒！", (100, 220, 255))
        combat_mgr.add_log("支援 24 職業自選、192 招正統技能全開，5x5 新楓之谷神裝欄已就緒！", (255, 215, 60))

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(8)

        # 1. 頂部狀態列
        top_bar = build_top_bar(self)
        main_layout.addWidget(top_bar)

        # 2. 三欄核心佈局 (左欄 5x5裝備與背包 / 中欄戰場 / 右欄職業技能)
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(10)

        # --- A. 左欄：5x5 官方裝備欄位、行囊背包、符號系統 ---
        left_col = build_left_column(self)
        columns_layout.addWidget(left_col, stretch=26)

        # --- B. 中欄：冒險戰場、動態特效畫布、隊伍狀態 ---
        center_col = build_center_column(self)
        columns_layout.addWidget(center_col, stretch=40)

        # --- C. 右欄：四大子頁籤、職業網格、技能配置、屬性加點 ---
        right_col = build_right_column(self)
        columns_layout.addWidget(right_col, stretch=38)

        main_layout.addLayout(columns_layout)

    # -------------------------------------------------------------------------
    # 委派更新方法
    # -------------------------------------------------------------------------
    def _update_top_bar(self, force=False):
        update_top_bar(self, force)

    def _update_left_column(self, force=False):
        update_left_column(self, force)

    def _update_center_column(self, force=False):
        update_center_column(self, force)

    def _update_right_column(self, force=False):
        update_right_column(self, force)

    def _refresh_right_panel(self):
        refresh_right_panel(self)

    def _rebuild_inventory_ui(self):
        rebuild_inventory_ui(self)

    def _open_inventory_dialog(self):
        from ui_dialogs import InventoryGridDialog
        dlg = InventoryGridDialog(self.player, win=self, parent=self)
        dlg.exec()
        self._update_left_column(force=True)
        self._update_top_bar(force=True)

    def _open_set_bonus_dialog(self):
        dlg = SetBonusDialog(self.player, parent=self)
        dlg.exec()

    def _open_training_dummy_dialog(self):
        dlg = TrainingDummyDialog(self.player, self._apply_training_dummy, parent=self)
        dlg.exec()

    def _open_skill_deck_dialog(self):
        dlg = SkillDeckDialog(self.player, parent=self)
        if dlg.exec():
            self._update_center_column(force=True)
            self._update_right_column(force=True)

    def _open_companion_dialog(self):
        dlg = CompanionDialog(self.player, parent=self)
        if dlg.exec():
            self._update_center_column(force=True)
            self._update_right_column(force=True)

    def _apply_training_dummy(self, level, hp, attack, defense, count=1, is_boss=False):
        self.combat_mgr.configure_training_dummy(level, hp, attack, defense, count=count, is_boss=is_boss)
        self._update_center_column(force=True)
        self._update_left_column(force=True)

    def _update_repeat_button_ui(self):
        update_repeat_button_ui(self)

    # -------------------------------------------------------------------------
    # 戰鬥每幀循環更新 (~30 FPS)
    # -------------------------------------------------------------------------
    def _game_loop_tick(self):
        now = time.time()
        dt = min(0.1, now - self.last_tick_time)
        self.last_tick_time = now

        old_hp = self.combat_mgr.monster.hp if self.combat_mgr.monster else 0
        self.combat_mgr.update(dt, self.sound_mgr)
        new_hp = self.combat_mgr.monster.hp if self.combat_mgr.monster else 0

        # 受擊反饋檢測
        if new_hp < old_hp:
            self.arena_widget.trigger_flash(0.08)
            if (old_hp - new_hp) > 50:
                self.arena_widget.trigger_shake(3.0, 0.20)

        self.arena_widget.update_vfx_timer(dt)

        self._update_top_bar()
        self._update_left_column()
        self._update_center_column()
        self._update_right_column()
        self.arena_widget.update()

    # -------------------------------------------------------------------------
    # 操作回調處理
    # -------------------------------------------------------------------------
    def _switch_class(self, slot_idx, class_id):
        if self.player.set_slot_class(slot_idx, class_id):
            self.sound_mgr.play("levelup")
            c_info = self.player.team[slot_idx].class_info
            self.combat_mgr.add_log(f"遠征隊席位 [{slot_idx+1}] 已切換為【{c_info['name']}】！", (255, 215, 0))
            self._refresh_right_panel()

    def _toggle_skill(self, slot_idx, skill_idx):
        success, msg = self.player.team[slot_idx].toggle_skill(skill_idx)
        if success:
            self.sound_mgr.play("hit")
            sk_name = self.player.team[slot_idx].skills[skill_idx].name
            self.combat_mgr.add_log(f"席位 {slot_idx+1} 技能變更：【{sk_name}】{msg}！", (100, 220, 255))
        else:
            self.combat_mgr.add_log(f"提示：{msg}！", (255, 120, 120))
        self._refresh_right_panel()

    def _toggle_skill_by_id(self, slot_idx, skill_id):
        success, msg = self.player.team[slot_idx].toggle_skill_by_id(skill_id)
        if success:
            self.sound_mgr.play("hit")
            self.combat_mgr.add_log(f"席位 {slot_idx+1} 技能變更：{msg}！", (100, 220, 255))
        else:
            self.combat_mgr.add_log(f"提示：{msg}！", (255, 120, 120))
        self._refresh_right_panel()

    def _add_stat(self, stat_k):
        if self.player.allocate_point(stat_k):
            self.sound_mgr.play("hit")
            st_cn = {"atk": "攻擊", "def": "防禦", "hp": "生命", "crit": "技巧"}.get(stat_k, "")
            self.combat_mgr.add_log(f"遠征隊能力分配：【{st_cn}】+1！", (60, 240, 130))
            self._refresh_right_panel()

    def _add_stat_batch(self, stat_k, count):
        allocated = self.player.add_stat_points(stat_k, count)
        if allocated > 0:
            self.sound_mgr.play("levelup")
            st_cn = {"atk": "攻擊", "def": "防禦", "hp": "生命", "crit": "技巧"}.get(stat_k, "")
            self.combat_mgr.add_log(f"遠征隊能力批次加點：【{st_cn}】+{allocated} 點！", (60, 240, 130))
            self._refresh_right_panel()

    def _auto_alloc(self, mode):
        res = self.player.auto_allocate_points(mode)
        allocated = res[0] if isinstance(res, tuple) else res
        if allocated > 0:
            self.sound_mgr.play("levelup")
            mode_names = {"all_atk": "全點攻擊", "balanced": "均衡分配", "defensive": "生存防禦"}
            m_cn = mode_names.get(mode, mode)
            self.combat_mgr.add_log(f"遠征隊一鍵加點：【{m_cn}】已分配 {allocated} 點！", (255, 215, 60))
            self._refresh_right_panel()

    def _prev_zone(self):
        if hasattr(self, "btn_gold_dungeon") and self.btn_gold_dungeon.isChecked():
            self.btn_gold_dungeon.setChecked(False)
        if self.combat_mgr.current_zone_idx > 0:
            self.combat_mgr.set_zone(self.combat_mgr.current_zone_idx - 1)
            if self.combat_mgr.current_zone_idx < self.combat_mgr.unlocked_zones - 1:
                self.combat_mgr.set_repeat_current_zone(True)
            self._update_repeat_button_ui()

    def _next_zone(self):
        if hasattr(self, "btn_gold_dungeon") and self.btn_gold_dungeon.isChecked():
            self.btn_gold_dungeon.setChecked(False)
        if self.combat_mgr.current_zone_idx + 1 < self.combat_mgr.unlocked_zones:
            self.combat_mgr.set_zone(self.combat_mgr.current_zone_idx + 1)
            if self.combat_mgr.current_zone_idx == self.combat_mgr.unlocked_zones - 1:
                self.combat_mgr.set_repeat_current_zone(False)
            self._update_repeat_button_ui()

    def _on_combo_zone_changed(self, idx):
        if hasattr(self, "btn_gold_dungeon") and self.btn_gold_dungeon.isChecked():
            self.btn_gold_dungeon.setChecked(False)
        if 0 <= idx < self.combat_mgr.unlocked_zones and idx != self.combat_mgr.current_zone_idx:
            self.combat_mgr.set_zone(idx)
            if idx < self.combat_mgr.unlocked_zones - 1:
                self.combat_mgr.set_repeat_current_zone(True)
            else:
                self.combat_mgr.set_repeat_current_zone(False)
            self._update_repeat_button_ui()

    def _on_toggle_repeat_zone(self, checked):
        self.combat_mgr.set_repeat_current_zone(checked, announce=True)
        self._update_repeat_button_ui()

    def _on_toggle_gold_dungeon(self, checked):
        if checked:
            self.btn_gold_dungeon.setText("🚪 退出金庫")
            self.btn_gold_dungeon.setStyleSheet("background-color: #9b2c2c; color: #ffffff; border: 1px solid #fc8181; font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: bold;")
            self.combat_mgr.enter_gold_dungeon()
            self.lbl_zone.setText("【💰 黃金寶庫】 無限刷幣")
        else:
            self.btn_gold_dungeon.setText("💰 金庫")
            self.btn_gold_dungeon.setStyleSheet("background-color: #744210; color: #fbd38d; border: 1px solid #d69e2e; font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: bold;")
            self.combat_mgr.leave_gold_dungeon()
            zone = self.combat_mgr.get_current_zone()
            self.lbl_zone.setText(f"【{zone['name']}】 第 {self.combat_mgr.current_floor}/10 層")

    def _upgrade_symbol(self, sym_key):
        success, msg = self.player.upgrade_symbol(sym_key)
        if success:
            self.sound_mgr.play("levelup")
            self.combat_mgr.add_log(f"符號突破：{msg}", (100, 240, 200))
        else:
            self.combat_mgr.add_log(f"提示：{msg}", (255, 130, 130))
        self._update_left_column(force=True)
        self._update_right_column(force=True)
        self._update_top_bar(force=True)

    def _auto_upgrade_all_symbols(self):
        upgraded_count = 0
        all_keys = list(ARC_SYMBOLS_DATA.keys()) + list(AUT_SYMBOLS_DATA.keys())
        while True:
            upgraded_this_pass = False
            for sym_key in all_keys:
                cur_lvl = self.player.arc_symbols.get(sym_key, 0) if sym_key in ARC_SYMBOLS_DATA else self.player.aut_symbols.get(sym_key, 0)
                if cur_lvl == 0:
                    continue
                req_frags, req_gold, is_max = self.player.get_symbol_upgrade_req(sym_key)
                if not is_max and self.player.symbol_fragments.get(sym_key, 0) >= req_frags and self.player.gold >= req_gold:
                    ok, _ = self.player.upgrade_symbol(sym_key)
                    if ok:
                        upgraded_count += 1
                        upgraded_this_pass = True
            if not upgraded_this_pass:
                break

        if upgraded_count > 0:
            self.sound_mgr.play("levelup")
            self.combat_mgr.add_log(f"⚡ 一鍵符號強化：共提升了 {upgraded_count} 個符號等級！全隊戰力大幅提升！", (100, 240, 200))
        else:
            self.combat_mgr.add_log("提示：當前無滿足強化條件 (碎片或金幣不足) 的符號！", (255, 130, 130))
        self._update_left_column(force=True)
        self._update_right_column(force=True)
        self._update_top_bar(force=True)

    def _on_equip_slot_clicked(self, slot_id):
        self.selected_forge_slot = slot_id
        item = self.player.equipped.get(slot_id)
        dlg = ItemCompareDialog(
            item, self.player,
            on_unequip=self._on_item_unequip,
            on_enhance=self._on_item_enhance_from_dlg,
            slot_k=slot_id,
            parent=self
        )
        dlg.exec()
        self._update_left_column()
        self._rebuild_inventory_ui()

    def _auto_equip_all(self):
        changes = self.player.auto_equip_best_gear()
        if changes:
            self.sound_mgr.play("equip")
            self.combat_mgr.add_log(f"【⚡ 一鍵換裝】完成！已自動配戴最高戰力神裝 (共更換 {len(changes)} 個部位)！", (100, 240, 150))
            self._update_left_column()
            self._rebuild_inventory_ui()
        else:
            self.combat_mgr.add_log("【⚡ 一鍵換裝】目前各部位均已是最高戰力神裝配置，無需更換！", (160, 174, 192))

    def _sell_inferior_gear(self):
        from player_gear import sell_inferior_gear
        count, gold = sell_inferior_gear(self.player)
        if count > 0:
            self.sound_mgr.play("gold")
            self.combat_mgr.add_log(f"【💰 一鍵出售】完成！已自動出售 {count} 件淘汰劣裝，獲得 +{gold:,} 金幣！", (255, 215, 0))
            self._update_left_column()
            self._rebuild_inventory_ui()
        else:
            self.combat_mgr.add_log("【💰 一鍵出售】行囊中沒有劣於當前穿戴之淘汰裝備可供出售。", (160, 174, 192))

    def _enhance_selected_gear(self):
        slot_k = self.selected_forge_slot
        if self.player.can_enhance_slot(slot_k):
            success, msg = self.player.enhance_slot(slot_k)
            if success:
                self.sound_mgr.play("forge")
                self.combat_mgr.add_log(f"★ {msg}", (255, 215, 0))
            else:
                self.sound_mgr.play("hit")
                self.combat_mgr.add_log(f"★ {msg}", (255, 100, 100))
            self._update_left_column()
        else:
            cost = self.player.get_slot_enhance_cost(slot_k)
            self.combat_mgr.add_log(f"【星力強化】金幣不足或欄位已滿星！需要 ${cost:,} 金幣", (255, 120, 120))

    def _on_item_enhance_from_dlg(self, slot_k):
        self.selected_forge_slot = slot_k
        self._enhance_selected_gear()

    def _show_item_modal(self, item):
        dlg = ItemCompareDialog(
            item, self.player,
            on_equip=self._on_item_equip,
            on_sell=self._on_item_sell,
            parent=self
        )
        dlg.exec()
        self._update_left_column()
        self._rebuild_inventory_ui()

    def _on_item_equip(self, item):
        success, msg = self.player.equip_item(item)
        if success:
            self.sound_mgr.play("equip")
            self.combat_mgr.add_log(f"穿戴成功：{msg}！", (100, 240, 150))
            self._update_left_column()
            self._rebuild_inventory_ui()
        else:
            self.combat_mgr.add_log(f"提示：{msg}！", (255, 120, 120))

    def _on_item_unequip(self, slot_k):
        success, msg = self.player.unequip_item(slot_k)
        if success:
            self.sound_mgr.play("hit")
            self.combat_mgr.add_log(f"卸下成功：{msg}！", (200, 220, 255))
            self._update_left_column()
            self._rebuild_inventory_ui()
        else:
            self.combat_mgr.add_log(f"提示：{msg}！", (255, 120, 120))

    def _on_item_sell(self, item):
        gold = self.player.sell_item(item)
        if gold > 0:
            self.sound_mgr.play("gold")
            self.combat_mgr.add_log(f"出售裝備【{item.full_name}】，獲得 +{gold} 金幣！", (255, 215, 0))
            self._update_left_column()
            self._rebuild_inventory_ui()

    def _batch_sell(self, rarities):
        count, gold = self.player.sell_by_rarities(rarities)
        if count > 0:
            self.sound_mgr.play("gold")
            self.combat_mgr.add_log(f"批次出售 {count} 件裝備，獲得 +{gold} 金幣！", (255, 215, 0))
            self._update_left_column()
            self._rebuild_inventory_ui()
        else:
            self.combat_mgr.add_log("行囊中沒有符合該品質的裝備可供出售。", (160, 174, 192))

    def _open_game_guide_dialog(self):
        from ui_dialogs import GameGuideDialog
        dlg = GameGuideDialog(parent=self)
        dlg.exec()

    def _manual_save(self):
        self.player.save_to_file(combat_mgr=self.combat_mgr)
        self.combat_mgr.add_log("【系統】遠征隊戰況已手動安全存檔！", (100, 240, 150))

    def _on_volume_changed(self, value):
        vol = value / 100.0
        self.sound_mgr.set_volume(vol)
        if hasattr(self, 'lbl_vol_val'):
            self.lbl_vol_val.setText(f"{value}%")
        if hasattr(self, 'lbl_vol_icon'):
            if value == 0 or not self.sound_mgr.enabled:
                self.lbl_vol_icon.setText("🔇")
            elif value < 40:
                self.lbl_vol_icon.setText("🔉")
            else:
                self.lbl_vol_icon.setText("🔊")

    def _toggle_mute(self):
        self.sound_mgr.enabled = not self.sound_mgr.enabled
        is_muted = not self.sound_mgr.enabled
        self.btn_mute.setText("開音 [M]" if is_muted else "靜音 [M]")
        if hasattr(self, 'lbl_vol_icon'):
            if is_muted or self.sound_mgr.volume == 0:
                self.lbl_vol_icon.setText("🔇")
            elif self.sound_mgr.volume < 0.4:
                self.lbl_vol_icon.setText("🔉")
            else:
                self.lbl_vol_icon.setText("🔊")
        self.combat_mgr.add_log(f"音效已{'關閉' if is_muted else '開啟'}", (160, 174, 192))

    def _on_tab_changed(self, idx):
        self.current_tab_slot = idx
        self._refresh_right_panel()

    def _set_class_filter(self, fid):
        self.class_faction_filter = fid
        self._refresh_right_panel()

    def _switch_right_mode(self, mode):
        self.right_mode = mode
        self._refresh_right_panel()

    def _draw_gachapon(self, draw_count=1, show_dialog=True):
        from item_system import draw_gachapon
        success, msg, results = draw_gachapon(self.player, draw_count=draw_count)
        if success:
            self.sound_mgr.play("levelup")
            self.last_gachapon_results = results
            self.combat_mgr.add_log(f"🎰 黃金轉蛋機：{msg}", (255, 215, 0))
            for res in results:
                if res.get("type") in ["item", "scroll"]:
                    self.combat_mgr.add_log(f"  ★ {res['name']} - {res['desc']}", (255, 235, 120))
            self._rebuild_inventory_ui()
            self._update_top_bar(force=True)
            self._refresh_right_panel()

            # 彈出華麗開獎報告彈窗 (單元測試中避免阻塞)
            is_unittest = "unittest" in sys.modules and any("unittest" in str(arg) or "test_" in str(arg) for arg in sys.argv)
            if show_dialog and not is_unittest and os.environ.get("QT_QPA_PLATFORM") != "offscreen":
                from ui_dialogs import GachaponResultDialog
                dlg = GachaponResultDialog(
                    results,
                    draw_count=draw_count,
                    on_draw_again=lambda: self._draw_gachapon(draw_count=draw_count),
                    parent=self
                )
                dlg.exec()
                self._refresh_right_panel()
        else:
            self.sound_mgr.play("hit")
            self.combat_mgr.add_log(f"🎰 提示：{msg}", (255, 120, 120))
            is_unittest = "unittest" in sys.modules and any("unittest" in str(arg) or "test_" in str(arg) for arg in sys.argv)
            if show_dialog and not is_unittest and os.environ.get("QT_QPA_PLATFORM") != "offscreen":
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "轉蛋提示", msg)
            self._refresh_right_panel()

    def _show_last_gacha_dialog(self):
        if hasattr(self, "last_gachapon_results") and self.last_gachapon_results:
            from ui_dialogs import GachaponResultDialog
            dlg = GachaponResultDialog(
                self.last_gachapon_results,
                draw_count=len(self.last_gachapon_results),
                on_draw_again=lambda: self._draw_gachapon(draw_count=len(self.last_gachapon_results)),
                parent=self
            )
            dlg.exec()
            self._refresh_right_panel()

    def _buy_shop_scroll(self, scroll_type, count=1):
        from shop_service import buy_scroll
        result = buy_scroll(self.player, scroll_type, count)
        if result is None:
            return
        success, message = result
        self.sound_mgr.play("levelup" if success else "hit")
        self.combat_mgr.add_log(message, (100, 240, 160) if success else (255, 120, 120))
        self._update_top_bar(force=True)
        self._refresh_right_panel()

    def _sell_shop_scroll(self, scroll_type, count=1):
        from shop_service import sell_scroll
        result = sell_scroll(self.player, scroll_type, count)
        if result is None:
            return
        success, message = result
        self.sound_mgr.play("coin" if success else "hit")
        self.combat_mgr.add_log(message, (255, 215, 60) if success else (255, 120, 120))
        self._update_top_bar(force=True)
        self._refresh_right_panel()

    def _buy_shop_cube(self, cube_type, count=1):
        from shop_service import buy_cube
        success, message = buy_cube(self.player, cube_type, count)
        self.sound_mgr.play("levelup" if success else "hit")
        self.combat_mgr.add_log(message, (100, 240, 160) if success else (255, 120, 120))
        self._update_top_bar(force=True)
        self._refresh_right_panel()

    def _buy_shop_familiar_cube(self, count=1):
        from shop_service import buy_familiar_cube
        success, message = buy_familiar_cube(self.player, count)
        self.sound_mgr.play("levelup" if success else "hit")
        self.combat_mgr.add_log(message, (100, 240, 160) if success else (255, 120, 120))
        self._update_top_bar(force=True)
        self._refresh_right_panel()

    def _buy_shop_basic_pet(self, pet_key):
        from shop_service import buy_basic_pet
        result = buy_basic_pet(self.player, pet_key)
        if result is None:
            return
        success, message = result
        self.sound_mgr.play("levelup" if success else "hit")
        self.combat_mgr.add_log(message, (100, 240, 160) if success else (255, 120, 120))
        self._update_top_bar(force=True)
        self._refresh_right_panel()

    def _buy_shop_pet_equip(self, equip_key):
        from shop_service import buy_pet_equip
        result = buy_pet_equip(self.player, equip_key)
        if result is None:
            return
        success, message = result
        self.sound_mgr.play("levelup" if success else "hit")
        self.combat_mgr.add_log(message, (255, 215, 60) if success else (255, 120, 120))
        self._update_top_bar(force=True)
        self._refresh_right_panel()

    def _buy_shop_pet_scroll(self):
        from shop_service import buy_pet_scroll
        success, message = buy_pet_scroll(self.player)
        if success:
            self.sound_mgr.play("upgrade")
            self.combat_mgr.add_log(message, (100, 240, 160))
        else:
            if message.startswith("金幣不足"):
                self.sound_mgr.play("hit")
            self.combat_mgr.add_log(message, (255, 120, 120))
        self._update_top_bar(force=True)
        self._refresh_right_panel()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_S:
            self._manual_save()
        elif event.key() == Qt.Key_M:
            self._toggle_mute()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.player.save_to_file(combat_mgr=self.combat_mgr)
        event.accept()
