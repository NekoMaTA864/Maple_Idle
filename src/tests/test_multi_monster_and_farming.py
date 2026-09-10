"""
多怪物波次群戰、AOE技能橫掃、菁英怪物機制與地圖循環農怪測試套件
(tests/test_multi_monster_and_farming.py)
"""
import sys
import os
import unittest

src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
if os.path.abspath('.') not in sys.path:
    sys.path.insert(0, os.path.abspath('.'))

from player_data import Player
from combat_system import CombatManager, Monster, ZONES
from skills import Skill, is_skill_aoe
from sound import sound_mgr


class TestMultiMonsterAndFarming(unittest.TestCase):
    def setUp(self):
        self.player = Player()
        self.sound_mgr = sound_mgr
        self.combat_mgr = CombatManager(self.player)

    def test_monster_backward_compatibility(self):
        """測試 combat_mgr.monster 的前向與向後相容性"""
        self.assertIsNotNone(self.combat_mgr.monster)
        self.assertTrue(self.combat_mgr.monster.is_alive)

        # 測試 setter 單一怪物
        m_single = Monster({"name": "測試菇菇", "lvl": 5, "hp": 100, "atk": 10, "def": 5, "spd": 2.0})
        self.combat_mgr.monster = m_single
        self.assertEqual(len(self.combat_mgr.monsters), 1)
        self.assertEqual(self.combat_mgr.monster.name, "測試菇菇")

        # 測試 setter 怪物陣列
        m1 = Monster({"name": "小怪A", "lvl": 5, "hp": 100, "atk": 10, "def": 5, "spd": 2.0})
        m2 = Monster({"name": "小怪B", "lvl": 5, "hp": 100, "atk": 10, "def": 5, "spd": 2.0})
        self.combat_mgr.monster = [m1, m2]
        self.assertEqual(len(self.combat_mgr.monsters), 2)
        self.assertEqual(self.combat_mgr.monster.name, "小怪A")

        # 當第一隻陣亡時，動態返回第二隻
        m1.hp = 0
        self.assertEqual(self.combat_mgr.monster.name, "小怪B")

    def test_wave_generation_and_elite_affixes(self):
        """測試非 BOSS 關卡生成 1~5 隻怪物波次，包含菁英怪物與詞綴"""
        self.combat_mgr.current_floor = 1

        wave_sizes = set()
        found_elite = False

        for _ in range(50):
            self.combat_mgr.spawn_next_monster()
            wave_sizes.add(len(self.combat_mgr.monsters))
            for m in self.combat_mgr.monsters:
                if getattr(m, "is_elite", False):
                    found_elite = True
                    self.assertIn(m.elite_affix, ["【強大】", "【堅壁】", "【迅捷】"])
                    self.assertGreater(m.exp_reward, int(m.lvl * 20))
                    self.assertGreater(m.gold_reward, int(m.lvl * 14))

        self.assertGreater(len(wave_sizes), 1)
        self.assertTrue(found_elite, "50 次生成應至少出現過一次菁英怪")

    def test_aoe_skill_detection(self):
        """測試 is_skill_aoe 判定邏輯"""
        sk_single = Skill("magnum", "巨型衝擊", 3.0, dmg_mult=2.0)
        self.assertFalse(is_skill_aoe(sk_single))

        sk_aoe_type = Skill("laser", "巨型雷射砲", 5.0, skill_type="aoe_beam")
        self.assertTrue(is_skill_aoe(sk_aoe_type))

        sk_genesis = Skill("genesis", "天怒", 8.0, tag_name="[全屏神罰]")
        self.assertTrue(is_skill_aoe(sk_genesis))

        sk_dark_genesis = Skill("dark_gen", "暗黑世紀", 6.0)
        self.assertTrue(is_skill_aoe(sk_dark_genesis))

        sk_explicit = Skill("custom", "自訂大招", 5.0, is_aoe=True)
        self.assertTrue(is_skill_aoe(sk_explicit))

    def test_aoe_vs_single_target_damage(self):
        """測試 AOE 技能全體打擊 vs 單體技能集火打擊"""
        m1 = Monster({"name": "小怪1", "lvl": 1, "hp": 500, "atk": 5, "def": 0, "spd": 2.0})
        m2 = Monster({"name": "小怪2", "lvl": 1, "hp": 500, "atk": 5, "def": 0, "spd": 2.0})
        m3 = Monster({"name": "小怪3", "lvl": 1, "hp": 500, "atk": 5, "def": 0, "spd": 2.0})
        self.combat_mgr.monsters = [m1, m2, m3]

        attacker = self.player.team[0]

        # 1. 單體技能打擊：僅第一隻怪扣血
        sk_single = Skill("test_single", "單體斬擊", 1.0, dmg_mult=1.0)
        self.combat_mgr._member_attack(attacker, self.sound_mgr, specific_skill=sk_single)
        self.assertLess(m1.hp, 500)
        self.assertEqual(m2.hp, 500)
        self.assertEqual(m3.hp, 500)

        # 2. AOE 技能打擊：全部存活怪物皆扣血
        hp1_before = m1.hp
        sk_aoe = Skill("test_aoe", "天怒", 1.0, dmg_mult=1.0, is_aoe=True)
        self.combat_mgr._member_attack(attacker, self.sound_mgr, specific_skill=sk_aoe)
        self.assertLess(m1.hp, hp1_before)
        self.assertLess(m2.hp, 500)
        self.assertLess(m3.hp, 500)

    def test_repeat_zone_farming_mode(self):
        """測試循環刷怪 (停留本區) 模式"""
        self.combat_mgr.current_zone_idx = 0
        self.combat_mgr.unlocked_zones = 3
        self.combat_mgr.current_floor = 10
        self.combat_mgr.spawn_next_monster()
        self.assertTrue(self.combat_mgr.is_boss_active)

        # 開啟循環農怪模式
        self.combat_mgr.repeat_current_zone = True

        # 擊破首領
        boss = self.combat_mgr.monster
        boss.hp = 0
        self.combat_mgr._on_monster_killed(self.sound_mgr)

        # 驗證：依然停留在第 0 區，但重置回第 1 層
        self.assertEqual(self.combat_mgr.current_zone_idx, 0)
        self.assertEqual(self.combat_mgr.current_floor, 1)
        self.assertFalse(self.combat_mgr.is_boss_active)

    def test_normal_progression_mode(self):
        """測試一般進度模式（關閉循環農怪時通關晉級）"""
        self.combat_mgr.current_zone_idx = 0
        self.combat_mgr.unlocked_zones = 1
        self.combat_mgr.current_floor = 10
        self.combat_mgr.spawn_next_monster()

        # 推進模式
        self.combat_mgr.repeat_current_zone = False

        boss = self.combat_mgr.monster
        boss.hp = 0
        self.combat_mgr._on_monster_killed(self.sound_mgr)

        # 驗證：晉級第 1 區第 1 層
        self.assertEqual(self.combat_mgr.current_zone_idx, 1)
        self.assertEqual(self.combat_mgr.current_floor, 1)
        self.assertEqual(self.combat_mgr.unlocked_zones, 2)


if __name__ == '__main__':
    unittest.main()
