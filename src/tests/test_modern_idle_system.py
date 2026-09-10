"""
單元與整合測試：新楓之谷放置冒險記 (MapleStory: Idle RPG) 核心系統全面檢驗
包含：
1. 7 人編隊體系 (1 核心主角 + 6 隨行護衛夥伴)
2. 主角母職業群跨職技能庫自由配置 (6~12 欄位擴展)
3. 夥伴 2 招王牌技能配置
4. 單一核心生存機制 (僅計算主角血防，首領 AOE 不多倍受創)
5. 17 職聯盟戰地後援 (Legion Bench) 被動加成
6. 戰鬥冷卻遞減與技能施法循環
7. 技能構築彈窗與夥伴編隊彈窗
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from classes import (
    ALL_CLASSES, MOTHER_CLASS_GROUPS,
    get_mother_group_for_class, get_mother_group_skills
)
from player_data import Player, TeamMember
from combat_system import CombatManager
from legion_system import LEGION_EFFECTS, calc_legion_bonuses
from sound import sound_mgr


class TestModernIdleSystem(unittest.TestCase):
    def setUp(self):
        self.player = Player()
        self.combat_mgr = CombatManager(self.player)

    def test_01_team_size_and_roles(self):
        """1. 驗證 7 人編隊：席位 0 為主角，席位 1~6 為隨行夥伴"""
        self.assertEqual(len(self.player.team), 7)
        self.assertTrue(self.player.team[0].is_protagonist)
        for i in range(1, 7):
            self.assertFalse(self.player.team[i].is_protagonist, f"席位 {i} 應為隨行夥伴而非主角")

    def test_02_protagonist_skill_slot_growth(self):
        """2. 驗證主角技能槽位：100等前 6 槽，100等以上擴展為 12 槽；夥伴固定 2 槽"""
        hero = self.player.team[0]
        companion = self.player.team[1]

        # 等級 1
        self.player.level = 1
        self.assertEqual(hero.max_skill_slots, 6)
        self.assertEqual(companion.max_skill_slots, 2)

        # 等級 99
        self.player.level = 99
        self.assertEqual(hero.max_skill_slots, 6)

        # 等級 100+
        self.player.level = 100
        self.assertEqual(hero.max_skill_slots, 12)
        self.player.level = 260
        self.assertEqual(hero.max_skill_slots, 12)
        self.assertEqual(companion.max_skill_slots, 2)

    def test_03_mother_class_group_skills(self):
        """3. 驗證 5 大母職業群跨職技能庫"""
        self.assertEqual(len(MOTHER_CLASS_GROUPS), 5)
        for g_id, g_info in MOTHER_CLASS_GROUPS.items():
            self.assertIn(g_id, ["warrior", "magician", "bowman", "thief", "pirate"])
            self.assertGreaterEqual(len(g_info["classes"]), 4)

        # 主角為英雄 (Warrior)，可用技能庫應包含劍士系全部 5 個職業的技能 (40 招)
        self.player.team[0].set_class("hero", self.player)
        avail = self.player.team[0].get_available_skills()
        self.assertEqual(len(avail), 40)

        # 主角切換為火毒魔導士 (Magician)，可用技能庫應變更為法師系 5 個職業 (40 招)
        self.player.team[0].set_class("fire_poison_mage", self.player)
        avail_mage = self.player.team[0].get_available_skills()
        self.assertEqual(len(avail_mage), 40)

    def test_04_single_health_pool_and_aoe_safety(self):
        """4. 驗證單一核心生存機制：隨行夥伴共享主角血防，首領 AOE 單次傷害結算"""
        hero = self.player.team[0]
        companion = self.player.team[1]
        initial_hp = hero.current_hp

        # 夥伴受到傷害應委派扣減主角血量
        lost, abs_sh = companion.take_damage(50)
        self.assertEqual(lost, 50)
        self.assertEqual(hero.current_hp, initial_hp - 50)
        self.assertEqual(companion.current_hp, hero.current_hp)

        # 測試首領 AOE 技能結算 (不應乘以 7 倍傷害)
        from monster import Monster
        from monster_ai import execute_monster_skill
        from skills import Skill

        boss = Monster({"name": "露希妲", "lvl": 200, "hp": 500000, "atk": 100, "def": 50, "spd": 2.5}, is_boss=True)
        aoe_skill = Skill(
            "dragon_breath", "龍息噴吐", 15.0, 1.2, 1, 1,
            skill_type="aoe_all", desc="全體全屏攻擊", is_aoe=True
        )
        before_hp = hero.current_hp
        execute_monster_skill(self.combat_mgr, aoe_skill, self.player.team, sound_mgr, boss_monster=boss)
        damage_taken = before_hp - hero.current_hp

        # 單次傷害計算：m_atk(100) * dmg_mult(1.2) = 約 120 點傷害 (浮動 0.92~1.08)
        # 若發生 7 倍傷害暴擊則會超過 700 點，驗證單次結算
        self.assertLess(damage_taken, 200, f"AOE 受創不應乘以 7 倍，當前扣血: {damage_taken}")

    def test_05_cross_class_skill_cooldown_updates(self):
        """5. 驗證跨職自選技能在戰鬥循環中冷卻能正常倒數更新"""
        hero = self.player.team[0]
        hero.set_class("hero", self.player)

        # 主角自選配置劍士母群技能：挑選 1 招英雄本職技能與 1 招聖魂劍士技能
        avail = hero.get_available_skills()
        hero_skill = next(s for s in avail if s.origin_class_id == "hero" and s.cooldown > 0)
        dw_skill = next(s for s in avail if s.origin_class_id == "dawn_warrior" and s.cooldown > 0)

        hero.set_equipped_skills([hero_skill, dw_skill])
        self.assertEqual(len(hero.get_active_skills()), 2)

        # 取得裝備中的出戰技能實例並觸發冷卻
        active_dw = next(s for s in hero.get_active_skills() if s.skill_id == dw_skill.skill_id)
        active_dw.trigger()
        self.assertFalse(active_dw.is_ready)
        self.assertGreater(active_dw.timer, 0.0)

        # 確保有怪物在場避免提前 return
        if not any(m.is_alive for m in self.combat_mgr.monsters):
            self.combat_mgr.spawn_next_monster()

        # 執行戰鬥 tick 更新 (0.5 秒)
        old_timer = active_dw.timer
        self.combat_mgr.update(0.5, sound_mgr)
        self.assertLess(active_dw.timer, old_timer, "跨職技能冷卻應正常隨戰鬥循環遞減！")

    def test_06_legion_bench_system(self):
        """6. 驗證 17 職戰地後援 (Legion Bench) 被動屬性累加"""
        bench = self.player.get_bench_classes()
        # 總共 24 職，出戰 7 職，後援應為 17 職
        self.assertEqual(len(bench), 17)

        # 驗證戰地加成計算
        bonuses = calc_legion_bonuses(bench)
        self.assertIn("attack", bonuses)
        self.assertIn("damage_mult", bonuses)
        self.assertGreater(bonuses["damage_mult"], 0.0)

        # 透過 player.get_legion_stat 獲取
        dmg_mult = self.player.get_legion_stat("damage_mult")
        self.assertEqual(dmg_mult, bonuses["damage_mult"])

    def test_07_class_switching_auto_swap(self):
        """7. 驗證席位換職防重複與自動互換 (Auto-Swap) 機制"""
        # 初始席位 1 為 dawn_warrior，席位 2 為 battle_mage
        cid_1 = self.player.team[1].class_id
        cid_2 = self.player.team[2].class_id

        # 將席位 1 換成席位 2 的職業 (battle_mage)
        success = self.player.set_slot_class(1, cid_2)
        self.assertTrue(success)

        # 席位 1 應變成 battle_mage，席位 2 自動換成 dawn_warrior，兩者不重複
        self.assertEqual(self.player.team[1].class_id, cid_2)
        self.assertEqual(self.player.team[2].class_id, cid_1)
        active_cids = {m.class_id for m in self.player.team}
        self.assertEqual(len(active_cids), 7, "7 個席位職業應始終保持各自唯一")

    def test_08_skill_toggle_by_id(self):
        """8. 驗證 toggle_skill_by_id 能精準裝備與卸下指定技能"""
        hero = self.player.team[0]
        hero.set_class("hero", self.player)
        avail = hero.get_available_skills()
        target = avail[3]

        # 卸下後再重新裝備
        hero.unequip_skill(target.skill_id)
        active_ids = {s.skill_id for s in hero.get_active_skills()}
        self.assertNotIn(target.skill_id, active_ids)

        # 依 ID 重新 toggle 裝備
        ok, msg = hero.toggle_skill_by_id(target.skill_id)
        self.assertTrue(ok)
        active_ids_after = {s.skill_id for s in hero.get_active_skills()}
        self.assertIn(target.skill_id, active_ids_after)


if __name__ == "__main__":
    unittest.main()
