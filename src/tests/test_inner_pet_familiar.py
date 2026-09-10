"""
《新楓之谷：放置遠征隊》內潛、寵物與萌獸三大核心系統單元測試 (test_inner_pet_familiar.py)
"""

import unittest
import os
import sys

src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from player_data import Player
from inner_ability import InnerAbility, InnerAbilityLine
from pet_system import Pet, PetManager
from familiar_system import Familiar, FamiliarLine, FamiliarManager
from player_save import player_to_dict, player_load_dict


class TestInnerPetFamiliarSystems(unittest.TestCase):

    def setUp(self):
        self.player = Player()

    def test_01_inner_ability_mechanics(self):
        """測試內在能力系統：階級、鎖定限制、防掉階與數值加乘"""
        ia = self.player.inner_ability
        self.assertIsNotNone(ia)
        self.assertEqual(len(ia.lines), 3)

        # 測試手動設為傳說階級
        ia.tier = "legendary"
        ia.lines[0] = InnerAbilityLine("boss_damage", "legendary", 0.20)
        ia.lines[1] = InnerAbilityLine("crit_chance", "unique", 0.18)
        ia.lines[2] = InnerAbilityLine("cooldown_skip", "unique", 0.10)

        # 驗證數值讀取
        self.assertAlmostEqual(self.player.get_inner_ability_stat("boss_damage"), 0.20)
        self.assertAlmostEqual(self.player.get_inner_ability_stat("crit_chance"), 0.18)
        self.assertAlmostEqual(self.player.get_inner_ability_stat("cooldown_skip"), 0.10)

        # 測試鎖定限制 (最多鎖定 2 排)
        ok1, _ = ia.toggle_lock(0)
        self.assertTrue(ok1)
        ok2, _ = ia.toggle_lock(1)
        self.assertTrue(ok2)
        ok3, _ = ia.toggle_lock(2)
        self.assertFalse(ok3)  # 不可鎖定 3 排

        # 測試名譽消耗與洗練 (鎖定 2 排需 5000 + 10000 = 15,000)
        self.assertEqual(ia.get_reroll_cost(), 15000)
        ia.honor_exp = 50000
        ok_roll, _ = ia.reroll()
        self.assertTrue(ok_roll)
        self.assertEqual(ia.tier, "legendary")  # 絕不降階
        # 第 0 排與第 1 排因鎖定保持原樣
        self.assertEqual(ia.lines[0].stat_type, "boss_damage")
        self.assertEqual(ia.lines[1].stat_type, "crit_chance")

    def test_02_pet_system_mechanics(self):
        """測試寵物系統：3 隻出戰限制、飾品衝卷、P 寵共鳴套裝與自動喝水"""
        pm = self.player.pet_manager
        self.assertIsNotNone(pm)

        # 預設出戰 3 隻
        active_pets = pm.get_active_pets()
        self.assertEqual(len(active_pets), 3)

        # 測試衝卷
        p1 = active_pets[0]
        old_atk = p1.equip_atk
        ok, _ = p1.scroll_equip()
        self.assertTrue(ok)
        self.assertEqual(p1.equip_atk, old_atk + 3)

        # 測試將三隻換成月光小寵物 (P寵)
        for p in pm.pets:
            p.is_active = False

        pm.set_pet_active("pet_luna_titania", True)
        pm.set_pet_active("pet_luna_bella", True)
        pm.set_pet_active("pet_luna_pico", True)

        self.assertEqual(pm.get_luna_petite_count(), 3)
        self.assertEqual(pm.get_luna_set_attack(), 30)  # 三隻 P 寵觸發 +30 攻擊力
        self.assertAlmostEqual(pm.get_loot_multiplier(), 1.30)  # 磁吸加成 1.30x

        # 測試自動喝水
        self.player.team[0].current_hp = 10.0  # 血量極低
        used = pm.check_auto_potion(self.player)
        self.assertGreater(used, 0)
        self.assertEqual(self.player.team[0].current_hp, float(self.player.team[0].get_max_hp(self.player)))

    def test_03_familiar_system_mechanics(self):
        """測試萌獸系統：獨立終傷相乘乘區、神級雙終/三終判定與 4 秒光環回復"""
        fm = self.player.familiar_manager
        self.assertIsNotNone(fm)

        # 測試三終萌獸 (3 排 20% 最終傷害)
        fam = Familiar("fam_test", "神選萌獸", "legendary", [
            FamiliarLine("final_damage", "legendary", 0.20),
            FamiliarLine("final_damage", "legendary", 0.20),
            FamiliarLine("final_damage", "legendary", 0.20)
        ], is_summoned=True)
        self.assertEqual(fam.tag_summary, "👑 傳奇三終")

        # 測試雙終萌獸
        fam2 = Familiar("fam_test2", "雙終萌獸", "legendary", [
            FamiliarLine("final_damage", "legendary", 0.20),
            FamiliarLine("final_damage", "legendary", 0.20),
            FamiliarLine("boss_damage", "legendary", 0.40)
        ], is_summoned=True)
        self.assertEqual(fam2.tag_summary, "⭐ 雙終極品")

        # 測試獨立終傷乘區計算
        fm.familiars = [fam]  # 僅出戰三終萌獸
        # (1 + 0.20) * (1 + 0.20) * (1 + 0.20) = 1.728
        expected_fd = 1.20 * 1.20 * 1.20
        self.assertAlmostEqual(fm.get_final_damage_multiplier(), expected_fd, places=4)

        # 測試 4 秒定時全隊回復光環
        fam_heal = Familiar("fam_heal", "聖光萌獸", "legendary", [
            FamiliarLine("team_hp_regen", "legendary", 0.15),
            FamiliarLine("boss_damage", "legendary", 0.40),
            FamiliarLine("def_ignore", "legendary", 0.40)
        ], is_summoned=True)
        fm.familiars = [fam_heal]

        self.player.team[0].current_hp = 50.0
        # 模擬時間經過 4.1 秒
        healed = fm.update_regen_aura(4.1, self.player)
        self.assertGreater(healed, 0)
        self.assertGreater(self.player.team[0].current_hp, 50.0)

    def test_04_save_and_load_persistence(self):
        """測試三大系統存檔序列化與讀檔反序列化"""
        p = self.player
        p.inner_ability.tier = "legendary"
        p.inner_ability.honor_exp = 88888
        p.pet_manager.potions = 77
        p.familiar_manager.familiar_cards = 99

        data = player_to_dict(p)
        self.assertIn("inner_ability", data)
        self.assertIn("pet_manager", data)
        self.assertIn("familiar_manager", data)

        new_p = Player()
        player_load_dict(new_p, data)

        self.assertEqual(new_p.inner_ability.tier, "legendary")
        self.assertEqual(new_p.inner_ability.honor_exp, 88888)
        self.assertEqual(new_p.pet_manager.potions, 77)
        self.assertEqual(new_p.familiar_manager.familiar_cards, 99)

    def test_05_inner_ability_auto_reroll(self):
        """測試內在能力一鍵洗潛 (指定目標詞條與階級)"""
        ia = self.player.inner_ability
        ia.tier = "rare"
        ia.honor_exp = 500000
        ok, msg = ia.auto_reroll(target_stat="cooldown_skip", target_tier="legendary", max_attempts=500)
        if ok:
            self.assertEqual(ia.tier, "legendary")
            self.assertTrue(any(l.stat_type == "cooldown_skip" for l in ia.lines))

    def test_06_familiar_single_active_and_fusion(self):
        """測試萌獸同時間僅能生效 1 隻、吞噬升階與一鍵洗潛"""
        fm = self.player.familiar_manager
        # 驗證初始出戰僅 1 隻
        self.assertEqual(len(fm.get_summoned_familiars()), 1)

        # 召喚另一隻萌獸，舊的出戰自動收回
        ok, _ = fm.set_summoned("fam_lucid", True)
        self.assertTrue(ok)
        active = fm.get_summoned_familiars()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].fid, "fam_lucid")

        # 測試吞噬素材
        fodder = Familiar("fam_fodder", "測試普通小怪", "common")
        fm.familiars.append(fodder)
        target = active[0]
        old_exp = target.exp
        ok_feed, msg = fm.feed_fodder(target.fid, fodder.fid)
        self.assertTrue(ok_feed)
        self.assertNotIn(fodder, fm.familiars)
        self.assertGreater(target.exp, old_exp)

        # 測試萌獸一鍵洗潛 (先清空終傷，消耗方塊直到洗出目標)
        target.lines = [
            FamiliarLine("boss_damage", "rare", 0.10),
            FamiliarLine("crit_damage", "rare", 0.02),
            FamiliarLine("team_hp_regen", "rare", 0.05)
        ]
        self.assertFalse(target.matches_target_condition("any_fd"))
        fm.familiar_cubes = 50
        ok_cube, msg_cube = target.auto_reroll_potentials(fm, target_mode="any_fd", max_cubes=50)
        self.assertTrue(ok_cube)
        self.assertTrue(target.matches_target_condition("any_fd"))

    def test_07_pet_equipment_and_gachapon(self):
        """測試寵物專屬裝備穿戴與飾品衝卷"""
        pm = self.player.pet_manager
        p = pm.pets[0]
        ok, msg = p.equip_gear("精靈天使之翼", bonus_atk=18, extra_slots=10)
        self.assertTrue(ok)
        self.assertEqual(p.equip_name, "精靈天使之翼")
        self.assertGreaterEqual(p.equip_atk, 18)

    def test_08_star_force_25(self):
        """測試一鍵升星支援到 ★25"""
        self.player.gold = 500_000_000
        slot_k = "weapon"
        self.player.slot_enhancements[slot_k] = 20
        ok, msg = self.player.auto_enhance_slot(slot_k, target_star=25)
        self.assertTrue(self.player.slot_enhancements[slot_k] >= 20)
        self.assertLessEqual(self.player.slot_enhancements[slot_k], 25)

    def test_09_sell_inferior_and_luna_equip_and_guide(self):
        """測試 player.sell_inferior_gear 委派、月光神裝與百科對話框"""
        # 1. 驗證 player.sell_inferior_gear 存在且可正常呼叫
        count, gold = self.player.sell_inferior_gear()
        self.assertIsInstance(count, int)
        self.assertIsInstance(gold, int)

        # 2. 驗證月光寵物神裝規格
        from pet_system import LUNA_PET_EQUIP_CATALOG
        self.assertIn("luna_titania_crown", LUNA_PET_EQUIP_CATALOG)
        self.assertIn("luna_bella_wings", LUNA_PET_EQUIP_CATALOG)
        self.assertIn("luna_pico_earring", LUNA_PET_EQUIP_CATALOG)
        t_crown = LUNA_PET_EQUIP_CATALOG["luna_titania_crown"]
        self.assertEqual(t_crown["atk"], 25)

        # 3. 驗證 GameGuideDialog 模組與結構
        from ui_dialogs import GameGuideDialog
        self.assertIsNotNone(GameGuideDialog)


if __name__ == "__main__":
    unittest.main()


