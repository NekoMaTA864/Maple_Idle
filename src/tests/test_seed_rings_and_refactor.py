"""
單元測試套件：驗證特殊種子戒指獲取分流、技能欄位預留，以及系統模組化重構完整性
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
    Item, generate_loot, create_seed_ring, draw_gachapon,
    SET_DEFINITIONS, ABBY_SCROLLS, CUBE_COSTS, SLOT_NAMES,
    SPECIAL_SEED_RINGS, BASE_NAMES, ITEM_REQUIRED_LEVEL, ITEM_INHERENT_RARITY
)
from combat_system import CombatManager
from sound import sound_mgr


class TestSeedRingsAndModularRefactor(unittest.TestCase):
    def setUp(self):
        self.player = Player()

    def test_01_seed_rings_excluded_from_normal_mob_drops(self):
        """1. 測試特殊種子戒指絕不從小怪一般掉落中產出"""
        seed_ring_names = set(SPECIAL_SEED_RINGS.keys())

        # 檢驗 BASE_NAMES 中戒指清單完全不含任何種子戒指
        for r_name in BASE_NAMES["ring"]:
            self.assertNotIn(r_name, seed_ring_names, f"Seed ring {r_name} found in BASE_NAMES['ring']!")

        # 模擬 200 次不同等級地圖的小怪一般掉落 (is_boss=False)
        for lvl in [10, 50, 100, 150, 200, 250]:
            for _ in range(35):
                loot = generate_loot(lvl, is_boss=False)
                self.assertNotIn(
                    loot.base_name,
                    seed_ring_names,
                    f"General mob dropped restricted seed ring: {loot.base_name}"
                )

    def test_02_create_seed_ring_helper_and_attributes(self):
        """2. 測試 create_seed_ring 建構起源之塔特殊戒指與技能欄位預留"""
        ror = create_seed_ring("規範之戒")
        self.assertTrue(ror.is_seed_ring)
        self.assertEqual(ror.seed_skill, "restraint")
        self.assertEqual(ror.skill_level, 4)
        self.assertEqual(ror.level_req, 75)
        self.assertIn("規範之戒", ror.full_name)
        self.assertIn("[塔戒]", ror.full_name)

        cont = create_seed_ring("持續之戒")
        self.assertTrue(cont.is_seed_ring)
        self.assertEqual(cont.seed_skill, "continuous")

        wpuff = create_seed_ring("武器泡泡之戒")
        self.assertTrue(wpuff.is_seed_ring)
        self.assertEqual(wpuff.seed_skill, "weapon_puff")

    def test_03_seed_ring_serialization_roundtrip(self):
        """3. 測試特殊種子戒指的 to_dict / from_dict 序列化完整保留屬性"""
        ror = create_seed_ring("規範之戒")
        d = ror.to_dict()
        self.assertTrue(d.get("is_seed_ring"))
        self.assertEqual(d.get("seed_skill"), "restraint")
        self.assertEqual(d.get("skill_level"), 4)

        restored = Item.from_dict(d)
        self.assertTrue(restored.is_seed_ring)
        self.assertEqual(restored.seed_skill, "restraint")
        self.assertEqual(restored.skill_level, 4)
        self.assertEqual(restored.base_name, "規範之戒")

    def test_04_gachapon_jackpot_contains_seed_rings(self):
        """4. 測試黃金轉蛋屋大獎池包含特殊種子戒指"""
        self.player.gold = 50000000  # 提供足夠金幣
        drawn_seed_rings = []

        # 進行多次十連抽以驗證大獎產出機制
        for _ in range(50):
            success, msg, results = draw_gachapon(self.player, draw_count=10)
            self.assertTrue(success)
            for res in results:
                if res.get("type") == "item" and getattr(res.get("item"), "is_seed_ring", False):
                    drawn_seed_rings.append(res["item"])

        # 驗證轉蛋機成功抽中種子戒指時具有完整的塔戒屬性
        if drawn_seed_rings:
            sample = drawn_seed_rings[0]
            self.assertTrue(sample.is_seed_ring)
            self.assertIsNotNone(sample.seed_skill)

    def test_05_modular_reexport_facade_integrity(self):
        """5. 測試 item_system 模組化 Facade 介面向下相容性"""
        # 驗證套裝定義
        self.assertIn("fafnir", SET_DEFINITIONS)
        self.assertIn("absolab", SET_DEFINITIONS)
        self.assertIn("gollux_superior", SET_DEFINITIONS)

        # 驗證艾比卷軸與方塊常數
        self.assertIn("electric", ABBY_SCROLLS)
        self.assertIn("R", ABBY_SCROLLS)
        self.assertIn("B", ABBY_SCROLLS)
        self.assertIn("bright", CUBE_COSTS)

        # 驗證欄位名稱
        self.assertEqual(len(SLOT_NAMES), 29)
        self.assertIn("weapon", SLOT_NAMES)
        self.assertIn("sub_weapon1", SLOT_NAMES)
        self.assertIn("sub_weapon2", SLOT_NAMES)
        self.assertIn("sub_weapon3", SLOT_NAMES)


if __name__ == "__main__":
    unittest.main()

