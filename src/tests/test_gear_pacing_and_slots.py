"""
單元測試套件：驗證裝備等級限制、掉落節奏、商店卷軸限制、正統套裝效果與欄位彈窗
"""
import unittest
import os
import sys

test_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(test_dir, ".."))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)

from player_data import Player
from item_system import (
    Item, generate_loot, SET_DEFINITIONS, ABBY_SCROLLS,
    ITEM_REQUIRED_LEVEL, ITEM_INHERENT_RARITY, SLOT_NAMES
)
from player_gear import equip_item, auto_equip_best_gear, ensure_player_slots
from combat_system import CombatManager
from sound import sound_mgr
from ui_dialogs import ItemCompareDialog


class TestGearPacingAndSlots(unittest.TestCase):
    def setUp(self):
        self.player = Player()
        ensure_player_slots(self.player)

    def test_player_init_slots(self):
        """1. 測試 Player 初始化即具備完整 25 格欄位星力、潛能與卷軸結構"""
        p = Player()
        self.assertIsNotNone(p.slot_scrolls)
        self.assertIsNotNone(p.slot_potentials)
        self.assertIsNotNone(p.slot_enhancements)
        self.assertIn("weapon", p.slot_scrolls)
        self.assertIn("sub_weapon1", p.slot_potentials)
        self.assertGreaterEqual(len(p.slot_enhancements), 25)

    def test_level_requirement_enforcement(self):
        """2. 測試裝備等級限制：等級不足不可手動穿戴，一鍵換裝自動略過超標裝備"""
        self.player.level = 10
        self.player.equipped["weapon"] = None
        # 建立 150 等深淵武器與 10 等木劍
        fafnir_sword = Item("weapon", "rare", 150, "法夫納斬首巨劍", {"attack": 80})
        wood_sword = Item("weapon", "common", 10, "木製短劍", {"attack": 15})

        self.player.inventory.append(fafnir_sword)
        self.player.inventory.append(wood_sword)

        # Lv.10 嘗試穿戴 150 等法夫納
        success, msg = equip_item(self.player, fafnir_sword)
        self.assertFalse(success)
        self.assertIn("等級不足", msg)
        self.assertNotEqual(self.player.equipped.get("weapon"), fafnir_sword)

        # Lv.10 穿戴 10 等木劍
        success, msg = equip_item(self.player, wood_sword)
        self.assertTrue(success)
        self.assertEqual(self.player.equipped.get("weapon"), wood_sword)

        # 測試一鍵換裝：當前 Lv.10，背包有 150 等神裝，一鍵換裝不應配戴超標裝
        self.player.auto_equip_best_gear()
        self.assertEqual(self.player.equipped.get("weapon"), wood_sword)

        # 玩家升級至 Lv.150，再次換裝即可配戴
        self.player.level = 150
        success, msg = equip_item(self.player, fafnir_sword)
        self.assertTrue(success)
        self.assertEqual(self.player.equipped.get("weapon"), fafnir_sword)

    def test_drop_pacing_and_level_matching(self):
        """3. 測試掉落機制：低等區域絕不掉落超越區域等階太多的神裝"""
        # Henesys (等級 15 怪物)
        for _ in range(50):
            loot = generate_loot(15, is_boss=False)
            req = ITEM_REQUIRED_LEVEL.get(loot.base_name, 10)
            self.assertLessEqual(req, 30, f"Zone 15 mob dropped over-leveled item {loot.base_name} (req: {req})")
            self.assertNotEqual(loot.rarity, "legendary")

        # 深層 BOSS (等級 200 怪物)
        loot_boss = generate_loot(200, is_boss=True)
        self.assertIsNotNone(loot_boss)

    def test_authentic_set_effects(self):
        """4. 測試正統新楓之谷套裝屬性 (深淵、航海師、頂培、神秘冥界、永恆)"""
        # 深淵法夫納
        faf = SET_DEFINITIONS["fafnir"]["tiers"]
        self.assertEqual(faf[4]["boss_dmg"], 0.30)
        self.assertEqual(faf[4]["damage_mult"], 0.10)

        # 航海師
        abso = SET_DEFINITIONS["absolab"]["tiers"]
        self.assertEqual(abso[5]["boss_dmg"], 0.30)
        self.assertEqual(abso[4]["damage_mult"], 0.10)

        # 頂級培羅德
        gol = SET_DEFINITIONS["gollux_superior"]["tiers"]
        self.assertEqual(gol[4]["boss_dmg"], 0.30)
        self.assertEqual(gol[4]["def_ignore"], 0.30)

        # 永恆神恩
        ete = SET_DEFINITIONS["eternal"]["tiers"]
        self.assertEqual(ete[2]["boss_dmg"], 0.10)
        self.assertEqual(ete[3]["def_ignore"], 0.10)
        self.assertEqual(ete[5]["crit_dmg"], 0.05)

    def test_shop_scroll_sales_limit(self):
        """5. 測試商店艾比卷軸限制：僅能直購極電與R卷，X/V/B不可直購"""
        from pyside_ui import MainWindow
        combat = CombatManager(self.player)
        win = MainWindow(self.player, combat, sound_mgr)

        self.player.gold = 1000000
        # 購買 R 卷
        old_r = self.player.abby_scrolls.get("R", 0)
        win._buy_shop_scroll("R", 1)
        self.assertEqual(self.player.abby_scrolls.get("R", 0), old_r + 1)

        # 嘗試購買 V 卷 (不可直購)
        old_v = self.player.abby_scrolls.get("V", 0)
        win._buy_shop_scroll("V", 1)
        self.assertEqual(self.player.abby_scrolls.get("V", 0), old_v)

    def test_dialog_opening_for_empty_and_equipped_slots(self):
        """6. 測試裝備彈窗：無論部位是否穿戴，均可直接開啟並查看/強化欄位潛能與卷軸"""
        # 1. 穿戴部位 (weapon)
        weapon_item = self.player.equipped.get("weapon")
        self.assertIsNotNone(weapon_item)
        dlg_equipped = ItemCompareDialog(weapon_item, self.player, slot_k="weapon")
        self.assertTrue(dlg_equipped.is_equipped)
        self.assertIsNotNone(dlg_equipped.slot_k)

        # 2. 空白部位 (ring1 預設未穿戴)
        self.player.equipped["ring1"] = None
        dlg_empty = ItemCompareDialog(None, self.player, slot_k="ring1")
        self.assertFalse(dlg_empty.is_equipped)
        self.assertEqual(dlg_empty.slot_k, "ring1")


if __name__ == "__main__":
    unittest.main()
