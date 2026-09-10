"""
新楓之谷：放置遠征隊 - 轉蛋機、商店、職業平衡、綠鎖與 25 欄位完整性整合測試
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from player_data import Player
from item_system import draw_gachapon, ABBY_SCROLLS, CUBE_COSTS, Item
from player_gear import ensure_player_slots, apply_scroll_to_slot, cube_slot, sell_by_rarities, toggle_item_lock
from player_save import player_to_dict, player_load_dict
from classes import ALL_CLASSES


class TestGachaponShopAndBalance(unittest.TestCase):
    def test_01_class_balance(self):
        # 1. 冰雷大魔導士
        ilm = ALL_CLASSES["ice_lightning_mage"]
        self.assertEqual(ilm["atk_mult"], 1.35)
        cl_sk = next(s for s in ilm["skills"] if s.skill_id == "chain_lightning")
        self.assertEqual(cl_sk.cooldown, 3.2)
        self.assertEqual(cl_sk.dmg_mult, 3.95)
        bl_sk = next(s for s in ilm["skills"] if s.skill_id == "blizzard")
        self.assertEqual(bl_sk.buff_duration, 3.0)
        fb_sk = next(s for s in ilm["skills"] if s.skill_id == "freezing_breath")
        self.assertEqual(fb_sk.buff_duration, 3.0)

        # 2. 主教
        bsp = ALL_CLASSES["bishop"]
        hs_sk = next(s for s in bsp["skills"] if s.skill_id == "holy_symbol")
        self.assertEqual(hs_sk.buff_val, 0.20)
        gen_sk = next(s for s in bsp["skills"] if s.skill_id == "genesis")
        self.assertEqual(gen_sk.dmg_mult, 2.8)
        sh_sk = next(s for s in bsp["skills"] if s.skill_id == "holy_magic_shell")
        self.assertEqual(sh_sk.shield_bonus, 90)
        dj_sk = next(s for s in bsp["skills"] if s.skill_id == "divine_judgment")
        self.assertEqual(dj_sk.dmg_mult, 2.0)

        # 3. 箭神 (Bowmaster)
        bm = ALL_CLASSES["bowmaster"]
        self.assertEqual(bm["name"], "箭神")
        hur_sk = next(s for s in bm["skills"] if s.skill_id == "hurricane")
        self.assertEqual(hur_sk.hit_count, 6)
        self.assertEqual(hur_sk.dmg_mult, 4.32)
        se_sk = next(s for s in bm["skills"] if s.skill_id == "sharp_eyes")
        self.assertEqual(se_sk.buff_val, 0.25)

        # 4. 狂豹獵人
        wh = ALL_CLASSES["wild_hunter"]
        wab_sk = next(s for s in wh["skills"] if s.skill_id == "wild_arrow_blast")
        self.assertEqual(wab_sk.hit_count, 5)
        self.assertEqual(wab_sk.dmg_mult, 0.90)
        howl_sk = next(s for s in wh["skills"] if s.skill_id == "howling")
        self.assertEqual(howl_sk.buff_val, 0.20)
        jr_sk = next(s for s in wh["skills"] if s.skill_id == "jaguar_rider")
        self.assertEqual(jr_sk.buff_val, 0.25)
        ea_sk = next(s for s in wh["skills"] if s.skill_id == "extreme_archery")
        self.assertEqual(ea_sk.dmg_mult, 4.2)

    def test_02_gachapon_draws(self):
        player = Player()
        player.gold = 5000000
        ok, msg, res = draw_gachapon(player, draw_count=10)
        self.assertTrue(ok)
        self.assertEqual(len(res), 10)
        self.assertEqual(player.gold, 4100000)

    def test_03_scroll_consumption(self):
        player = Player()
        ensure_player_slots(player)
        player.abby_scrolls = {"V": 2}
        player.gold = 0
        ok, msg = apply_scroll_to_slot(player, "weapon", "V")
        self.assertTrue(ok)
        self.assertEqual(player.abby_scrolls["V"], 1)
        self.assertEqual(player.gold, 0)

    def test_04_cube_consumption(self):
        player = Player()
        ensure_player_slots(player)
        player.cube_inventory = {"bright": 3}
        player.gold = 0
        ok, msg = cube_slot(player, "weapon", "bright", is_bonus=False)
        self.assertTrue(ok)
        self.assertEqual(player.cube_inventory["bright"], 2)
        self.assertEqual(player.gold, 0)

    def test_05_green_lock(self):
        player = Player()
        it1 = Item("ring", "legendary", 200, "規範之戒", {"attack": 30})
        it2 = Item("ring", "epic", 200, "持續之戒", {"attack": 30})
        it3 = Item("weapon", "common", 10, "木劍", {"attack": 5})
        toggle_item_lock(it1)
        self.assertTrue(it1.locked)
        self.assertFalse(it2.locked)
        player.inventory = [it1, it2, it3]
        sell_by_rarities(player, ["legendary", "epic", "common"])
        self.assertIn(it1, player.inventory)
        self.assertNotIn(it2, player.inventory)
        self.assertNotIn(it3, player.inventory)
        self.assertIn(it1, player.inventory)
        self.assertNotIn(it2, player.inventory)
        self.assertNotIn(it3, player.inventory)

    def test_06_persistence(self):
        player = Player()
        ensure_player_slots(player)
        player.abby_scrolls = {"X": 5, "B": 2}
        player.cube_inventory = {"bright": 10, "bonus_bright": 4}
        it1 = Item("ring", "legendary", 200, "規範之戒", {"attack": 30})
        toggle_item_lock(it1)
        player.inventory = [it1]

        d = player_to_dict(player)
        p2 = Player()
        player_load_dict(p2, d)
        self.assertEqual(p2.abby_scrolls, {"X": 5, "B": 2})
        self.assertEqual(p2.cube_inventory, {"bright": 10, "bonus_bright": 4})
        self.assertTrue(p2.inventory[0].locked)

    def test_07_ui_mode_switching_and_shop_actions(self):
        from PySide6.QtWidgets import QApplication
        from pyside_ui import MainWindow
        from combat_system import CombatManager
        from sound import sound_mgr

        app = QApplication.instance() or QApplication(sys.argv)
        player = Player()
        combat_mgr = CombatManager(player)
        win = MainWindow(player, combat_mgr, sound_mgr)

        # 初始隊伍模式
        self.assertEqual(win.right_mode, "team")
        self.assertFalse(win.tab_widget.isHidden())
        self.assertTrue(win.shop_container.isHidden())

        # 切換至商店轉蛋模式
        win.btn_mode_shop.click()
        self.assertEqual(win.right_mode, "shop")
        self.assertTrue(win.tab_widget.isHidden())
        self.assertFalse(win.shop_container.isHidden())

        # 購買艾比卷軸與方塊 (商店僅開放至R卷)
        win.player.gold = 3000000
        win._buy_shop_scroll("R", 2)
        self.assertEqual(win.player.abby_scrolls.get("R", 0), 2)
        win._buy_shop_cube("bright", 2)
        self.assertEqual(win.player.cube_inventory.get("bright", 0), 2)

        # 轉蛋十連抽
        win._draw_gachapon(10)
        self.assertEqual(len(win.last_gachapon_results), 10)

        # 切換至符號模式
        win.btn_mode_symbol.click()
        self.assertEqual(win.right_mode, "symbol")
        self.assertTrue(win.tab_widget.isHidden())
        self.assertTrue(win.shop_container.isHidden())
        self.assertFalse(win.symbol_container.isHidden())

        # 切回隊伍模式
        win.btn_mode_team.click()
        self.assertEqual(win.right_mode, "team")
        self.assertFalse(win.tab_widget.isHidden())
        self.assertTrue(win.shop_container.isHidden())
        self.assertTrue(win.symbol_container.isHidden())

    def test_08_innocence_scroll_and_split_slot_colors(self):
        player = Player()
        ensure_player_slots(player)

        # 1. 測試回真卷軸衝卷重置
        # 先衝 3 張 V 卷
        player.abby_scrolls = {"V": 3, "innocence": 1}
        player.gold = 1000000
        for _ in range(3):
            ok, msg = apply_scroll_to_slot(player, "weapon", "V")
            self.assertTrue(ok)
        self.assertEqual(player.slot_scrolls["weapon"]["count"], 3)
        self.assertTrue(player.slot_scrolls["weapon"]["stats"]["attack"] > 0)

        # 使用回真卷軸 (扣除庫存)
        ok, msg = apply_scroll_to_slot(player, "weapon", "innocence")
        self.assertTrue(ok)
        self.assertEqual(player.slot_scrolls["weapon"]["count"], 0)
        self.assertEqual(player.slot_scrolls["weapon"]["stats"], {})
        self.assertEqual(player.slot_scrolls["weapon"]["history"], [])
        self.assertEqual(player.abby_scrolls["innocence"], 0)

        # 再次對 count=0 的欄位使用回真卷軸應被拒絕
        player.abby_scrolls["innocence"] = 1
        ok, msg = apply_scroll_to_slot(player, "weapon", "innocence")
        self.assertFalse(ok)
        self.assertIn("無須", msg)

        # 2. 測試商店購買回真卷軸
        from PySide6.QtWidgets import QApplication
        from pyside_ui import MainWindow
        from combat_system import CombatManager
        from sound import sound_mgr
        app = QApplication.instance() or QApplication(sys.argv)
        cm = CombatManager(player)
        win = MainWindow(player, cm, sound_mgr)
        player.gold = 500000
        win._buy_shop_scroll("innocence", 1)
        self.assertEqual(player.abby_scrolls.get("innocence", 0), 2)  # 原本剩 1 + 買 1 = 2
        self.assertEqual(player.gold, 400000)

        # 3. 測試 25 格裝備欄位雙層漸層品階與名稱保持
        # 卸下武器測試空欄位名稱為 "主武器"，品階為 rare/rare (特殊: #1a365d, #3182ce)
        player.equipped["weapon"] = None
        win._update_left_column(force=True)
        w_btn = win.equip_slot_buttons["weapon"]
        self.assertEqual(w_btn.text(), "主武器")
        self.assertIn("#0e2442", w_btn.styleSheet())
        self.assertIn("#3182ce", w_btn.styleSheet())

        # 穿上裝備、洗主潛能至傳奇 (legendary, #48bb78)、附加至罕見 (unique, #ed8936)、星力 15
        from item_system import Item
        player.equipped["weapon"] = Item("weapon", "legendary", 200, "創世短刀", {"attack": 250})
        player.slot_potentials["weapon"]["main"]["rank"] = "legendary"
        player.slot_potentials["weapon"]["bonus"]["rank"] = "unique"
        player.slot_enhancements["weapon"] = 15
        win._update_left_column(force=True)

        # 保持顯示裝備名稱與星數，不用額外文字標註稀有度
        self.assertEqual(w_btn.text(), "★15 創世短刀")
        # 樣式表應包含主潛傳奇綠色 (#48bb78) 與附加罕見橘色 (#ed8936)
        self.assertIn("#48bb78", w_btn.styleSheet())
        self.assertIn("#ed8936", w_btn.styleSheet())

        # 4. 測試木樁設定群怪環境 (1~5 隻)
        cm.configure_training_dummy(100, 500000, 0, 0, count=4)
        self.assertTrue(cm.is_training_dummy)
        self.assertEqual(len(cm.monsters), 4)
        for m in cm.monsters:
            self.assertTrue(m.name.startswith("自定義木樁"))
            self.assertEqual(m.max_hp, 500000)

        # 5. 測試 AUT 地區與符文完整度 (包含 275 奧迪溫、280~285 阿爾特利亞、290~300 塔拉哈特)
        from player_symbols import AUT_SYMBOLS_DATA
        from combat_system import ZONES
        expected_aut = ["cernium", "arcus", "odium", "shangrila", "arteria", "carcion", "talahart"]
        for sym_k in expected_aut:
            self.assertIn(sym_k, AUT_SYMBOLS_DATA)
            self.assertIn(sym_k, player.aut_symbols)
        zone_map = {z["id"]: z for z in ZONES}
        for zone_k in ["odium", "arteria", "talahart"]:
            self.assertIn(zone_k, zone_map)
            self.assertIn("aut_req", zone_map[zone_k])



if __name__ == "__main__":
    unittest.main()
