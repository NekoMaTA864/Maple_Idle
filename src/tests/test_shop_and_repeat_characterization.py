"""Characterization coverage for the existing shop UI and repeat-zone mutations."""

import os
import sys
import unittest


SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from combat_system import CombatManager
from player_data import Player
from pyside_ui import MainWindow
from sound import sound_mgr


class TestShopAndRepeatCharacterization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.player = Player()
        self.combat = CombatManager(self.player)
        self.window = MainWindow(self.player, self.combat, sound_mgr)

    def tearDown(self):
        self.window.close()

    def test_scroll_purchase_and_sale_keep_existing_cost_and_stock_rules(self):
        self.player.gold = 500_000

        self.window._buy_shop_scroll("R", 2)
        self.assertEqual(self.player.gold, 400_000)
        self.assertEqual(self.player.abby_scrolls["R"], 2)

        self.window._sell_shop_scroll("R", 1)
        self.assertEqual(self.player.gold, 480_000)
        self.assertEqual(self.player.abby_scrolls["R"], 1)

        before = (self.player.gold, dict(self.player.abby_scrolls))
        self.window._buy_shop_scroll("V", 1)
        self.assertEqual((self.player.gold, self.player.abby_scrolls), before)

    def test_shop_insufficient_gold_preserves_scroll_cube_and_familiar_cube_state(self):
        self.player.gold = 0
        before = (
            dict(self.player.abby_scrolls),
            dict(self.player.cube_inventory),
            self.player.familiar_manager.familiar_cubes,
        )

        self.window._buy_shop_scroll("electric", 1)
        self.window._buy_shop_cube("bright", 1)
        self.window._buy_shop_familiar_cube(1)

        self.assertEqual(self.player.gold, 0)
        self.assertEqual(
            (self.player.abby_scrolls, self.player.cube_inventory, self.player.familiar_manager.familiar_cubes),
            before,
        )

    def test_pet_purchases_preserve_existing_charge_before_duplicate_or_equipment_mutation(self):
        self.player.gold = 1_000_000
        existing = next(pet for pet in self.player.pet_manager.pets if pet.pet_id == "pet_puppy")
        atk_before = existing.equip_atk

        self.window._buy_shop_basic_pet("pet_husky")
        self.assertEqual(self.player.gold, 800_000)
        husky = next(pet for pet in self.player.pet_manager.pets if pet.pet_id == "pet_husky")
        self.assertEqual(husky.equip_atk, 6)

        self.window._buy_shop_basic_pet("pet_husky")
        self.assertEqual(self.player.gold, 600_000)
        self.assertEqual(husky.equip_atk, 11)
        self.assertEqual(existing.equip_atk, atk_before)

        self.window._buy_shop_pet_equip("golden_bell")
        self.assertEqual(self.player.gold, 450_000)

    def test_pet_scroll_without_any_slot_preserves_gold(self):
        self.player.gold = 50_000
        for pet in self.player.pet_manager.pets:
            pet.scroll_slots_left = 0

        self.window._buy_shop_pet_scroll()

        self.assertEqual(self.player.gold, 50_000)

    def test_repeat_zone_toggle_keeps_state_and_existing_log_text(self):
        self.combat.current_zone_idx = 0
        self.combat.unlocked_zones = 2

        self.window._on_toggle_repeat_zone(True)
        self.assertTrue(self.combat.repeat_current_zone)
        self.assertIn("已鎖定", self.combat.combat_logs[-1]["text"])

        self.window._on_toggle_repeat_zone(False)
        self.assertFalse(self.combat.repeat_current_zone)
        self.assertIn("已恢復一般進度模式", self.combat.combat_logs[-1]["text"])


if __name__ == "__main__":
    unittest.main()
