"""Characterization tests for the current Golden Gachapon reward contract."""

import os
import sys
import unittest
from unittest.mock import patch


SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from item_system import draw_gachapon


class GachaponPlayerStub:
    def __init__(self, gold, inventory_limit=None):
        self.gold = gold
        self.inventory = []
        self.inventory_limit = inventory_limit
        self.arc_symbols = {"vanishing": {}}

    def add_to_inventory(self, item):
        if self.inventory_limit is not None and len(self.inventory) >= self.inventory_limit:
            return False
        self.inventory.append(item)
        return True


class TestItemGachaponCharacterization(unittest.TestCase):
    def test_insufficient_gold_returns_before_mutating_player(self):
        player = GachaponPlayerStub(gold=99_999)

        ok, message, results = draw_gachapon(player, draw_count=1)

        self.assertFalse(ok)
        self.assertEqual(message, "金幣不足！轉蛋需要 $100,000 金幣")
        self.assertEqual(results, [])
        self.assertEqual(player.gold, 99_999)
        self.assertEqual(player.inventory, [])

    def test_seed_ring_jackpot_preserves_seed_ring_payload_and_cost(self):
        player = GachaponPlayerStub(gold=100_000)

        with patch("item_gachapon.random.random", return_value=0.039), \
             patch("item_gachapon.random.choice", return_value=("規範之戒", "ring")):
            ok, message, results = draw_gachapon(player, draw_count=1)

        self.assertTrue(ok)
        self.assertEqual(message, "🎉 恭喜完成 1 連抽！消耗 $100,000 金幣。")
        self.assertEqual(player.gold, 0)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["type"], "item")
        self.assertEqual(results[0]["name"], "【特殊種子戒指】規範之戒")
        item = results[0]["item"]
        self.assertTrue(item.is_seed_ring)
        self.assertEqual(item.seed_skill, "restraint")
        self.assertEqual(item.skill_level, 4)
        self.assertEqual(player.inventory, [item])

    def test_non_seed_jackpot_uses_legendary_item_payload(self):
        player = GachaponPlayerStub(gold=100_000)

        with patch("item_gachapon.random.random", return_value=0.0), \
             patch("item_gachapon.random.choice", return_value=("巨大恐懼", "ring")):
            ok, _, results = draw_gachapon(player, draw_count=1)

        self.assertTrue(ok)
        item = results[0]["item"]
        self.assertEqual(results[0]["name"], "【傳奇大獎】巨大恐懼")
        self.assertFalse(item.is_seed_ring)
        self.assertEqual(item.base_name, "巨大恐懼")
        self.assertEqual(item.stats, {"attack": 45, "defense": 25, "hp": 300, "crit_chance": 0.08})
        self.assertEqual(item.potential_rank, "legendary")

    def test_threshold_branches_keep_resource_payloads_and_mutations(self):
        player = GachaponPlayerStub(gold=900_000)

        with patch("item_gachapon.random.random", side_effect=[0.14, 0.50, 0.75]), \
             patch("item_gachapon.random.choice", side_effect=["V", ("bright", "閃耀方塊", 2), "vanishing"]), \
             patch("item_gachapon.random.randint", return_value=6):
            ok, _, results = draw_gachapon(player, draw_count=3)

        self.assertTrue(ok)
        self.assertEqual(player.gold, 0)
        self.assertEqual([result["type"] for result in results], ["scroll", "resource", "symbol"])
        self.assertEqual(player.abby_scrolls, {"V": 1})
        self.assertEqual(player.cube_inventory, {"bright": 2})
        self.assertEqual(player.symbol_fragments, {"vanishing": 6})

    def test_full_inventory_reports_lost_item_without_changing_reward_roll(self):
        player = GachaponPlayerStub(gold=100_000, inventory_limit=0)

        with patch("item_gachapon.random.random", return_value=0.039), \
             patch("item_gachapon.random.choice", return_value=("規範之戒", "ring")):
            ok, _, results = draw_gachapon(player, draw_count=1)

        self.assertTrue(ok)
        self.assertEqual(player.gold, 0)
        self.assertEqual(player.inventory, [])
        self.assertEqual(results[0]["type"], "item_lost")
        self.assertIn("背包已滿", results[0]["name"])
        self.assertIn("背包已滿", results[0]["desc"])


if __name__ == "__main__":
    unittest.main()
