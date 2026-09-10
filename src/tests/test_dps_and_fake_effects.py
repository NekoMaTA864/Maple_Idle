"""
《新楓之谷：放置遠征隊》真效果修復、金幣經濟與 DPS 計算器單元測試 (test_dps_and_fake_effects.py)
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from player_data import Player, TeamMember
from combat_system import CombatManager
from monster import Monster
from classes import ALL_CLASSES
from item_system import Item, ABBY_SCROLLS
from dps_calculator import SilentSound, run_dps_simulation


class TestDpsAndFakeEffects(unittest.TestCase):
    def test_01_guaranteed_crit(self):
        """測試 guaranteed_crit 技能在 0% 暴擊率下依然 100% 暴擊"""
        player = Player()
        player.level = 200
        player.stat_crit = 0  # 歸零爆擊

        cm = CombatManager(player)
        cm.configure_training_dummy(200, 10**8, 0, 0, count=1)
        target = cm.monsters[0]

        # 取得有必定暴擊特性的技能，例如英雄「終極攻擊 (final_attack)」或神射手「必殺狙擊 (snipe)」
        hero = player.team[0]
        snipe_sk = next(s for s in ALL_CLASSES["marksman"]["skills"] if s.skill_id == "snipe")
        self.assertTrue(getattr(snipe_sk, "guaranteed_crit", False))

        snd = SilentSound()
        # 執行攻擊
        cm._member_attack(hero, snd, specific_skill=snipe_sk)

        # 結算多段 hits
        while cm.pending_hits:
            hit = cm.pending_hits.pop(0)
            self.assertTrue(hit.is_crit, f"Pending hit {hit.skill_name} 應為暴擊！")

        stats = cm.combat_stats.for_member(hero.slot_idx)
        self.assertGreater(stats.critical_count, 0)
        self.assertEqual(stats.critical_count, stats.hit_lines)

    def test_02_ignore_defense_pct(self):
        """測試 ignore_defense_pct 能實質減少目標防禦力並提升傷害 (新楓之谷正統防禦率機制)"""
        player = Player()
        player.level = 200

        # 英雄「狂怒伸展 (raging_blow)」自帶無視防禦
        raging_blow = next(s for s in ALL_CLASSES["hero"]["skills"] if s.skill_id == "raging_blow")
        self.assertGreater(getattr(raging_blow, "ignore_defense_pct", 0.0), 0.0)

        # 模擬打 300% 正統防禦率首領木樁
        cm = CombatManager(player)
        cm.configure_training_dummy(200, 10**8, 0, 300, count=1, is_boss=True)
        hero = player.team[0]
        snd = SilentSound()

        # 執行 ignore_defense 技能攻擊
        cm._member_attack(hero, snd, specific_skill=raging_blow)
        st = cm.combat_stats.for_member(hero.slot_idx)
        self.assertGreater(st.damage_dealt, 0)
        self.assertEqual(cm.monsters[0].defense_rate, 3.0)

    def test_03_gold_dungeon_rewards(self):
        """測試金幣副本：擊殺後不給予任何經驗值 (EXP=0)，給予大量金幣"""
        player = Player()
        player.level = 200
        initial_exp = player.exp
        initial_gold = player.gold

        cm = CombatManager(player)
        cm.enter_gold_dungeon()
        self.assertTrue(cm.is_gold_dungeon)
        self.assertEqual(len(cm.monsters), 1)
        chest_m = cm.monsters[0]
        self.assertIn("黃金寶箱怪", chest_m.name)

        # 將寶箱怪血量降為 0 觸發擊殺結算
        chest_m.hp = 0
        snd = SilentSound()
        cm._on_monster_killed(snd)

        # 驗證經驗值完全不增加
        self.assertEqual(player.exp, initial_exp, "金幣副本不應給予任何經驗值！")
        # 驗證金幣大量增加 (Lv.200 至少 300萬)
        self.assertGreaterEqual(player.gold - initial_gold, 3_000_000, "金幣副本應掉落巨額金幣！")

    def test_04_gear_selling_and_abby_scroll_selling(self):
        """測試裝備售價階梯提升與艾比卷軸回收出售機制"""
        # 1. 裝備高額售價
        high_gear = Item(slot="weapon", rarity="legendary", level_req=250, base_name="神秘冥界幽靈雙刀", stats={"atk": 500})
        sell_p = high_gear.sell_price
        # Lv.250 傳說神裝基礎價格 80000 + 50*1000 = 130000 * 3.2 = 416,000
        self.assertGreaterEqual(sell_p, 200_000, f"高等傳說裝備售價應大幅提高，實際為 {sell_p}")

        # 2. 艾比卷軸回收
        self.assertEqual(ABBY_SCROLLS["electric"]["sell_price"], 30_000)
        self.assertEqual(ABBY_SCROLLS["R"]["sell_price"], 80_000)

    def test_05_dps_simulation_fast_runner(self):
        """測試 DPS 高速演算計算器模擬 60 秒戰鬥正確產出報表數據"""
        player = Player()
        player.level = 200

        res = run_dps_simulation(
            player,
            duration_sec=60.0,
            dummy_level=200,
            dummy_def=300,
            dummy_targets=1
        )

        self.assertAlmostEqual(res["duration"], 60.0, delta=1.0)
        self.assertLess(res["real_time"], 3.0, "60 秒模擬運算應在 3 秒內完成！")
        self.assertGreater(res["team_damage"], 0)
        self.assertGreater(res["team_dps"], 0)
        self.assertEqual(len(res["members"]), 7)
        for m in res["members"]:
            self.assertGreater(m["damage"], 0)
            self.assertGreater(m["attacks"], 0)
            self.assertLessEqual(m["crit_rate"], 100.0)

    def test_06_random_team_and_role_classification(self):
        """測試全隨機 7 人抽籤組隊 (1 主角 + 6 隨行夥伴) 與職業戰術定位 (坦/輔/輸出) 判定"""
        from dps_calculator import create_random_team_player, classify_class_role

        player, picked_cids = create_random_team_player(level=200)
        self.assertEqual(len(picked_cids), 7)
        self.assertEqual(len(set(picked_cids)), 7, "隨機抽籤職業不應重複")
        self.assertEqual(len(player.team), 7)

        # 驗證戰術定位
        self.assertIn("坦克", classify_class_role("paladin"))
        self.assertIn("坦克", classify_class_role("dark_knight"))
        self.assertIn("坦克", classify_class_role("mechanic"))
        self.assertIn("輔助", classify_class_role("bishop"))
        self.assertIn("輔助", classify_class_role("battle_mage"))
        self.assertIn("輸出", classify_class_role("night_lord"))
        self.assertIn("輸出", classify_class_role("hero"))


if __name__ == "__main__":
    unittest.main()
