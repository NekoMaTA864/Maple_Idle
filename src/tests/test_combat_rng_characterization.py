"""Deterministic safety net for the current combat RNG call sites."""

import os
import random
import sys
import unittest
from unittest.mock import patch


SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from combat_system import CombatManager
from dps_calculator import SilentSound, run_dps_simulation
from monster import Monster
from player_data import Player


class QueueRng:
    """Small deterministic stub; it deliberately exposes only current combat RNG methods."""

    def __init__(self, random_values=(), uniform_values=(), choices=(), randint_values=()):
        self.random_values = list(random_values)
        self.uniform_values = list(uniform_values)
        self.choices = list(choices)
        self.randint_values = list(randint_values)
        self.calls = []

    def random(self):
        self.calls.append("random")
        return self.random_values.pop(0) if self.random_values else 0.99

    def uniform(self, low, high):
        self.calls.append(("uniform", low, high))
        return self.uniform_values.pop(0) if self.uniform_values else (low + high) / 2

    def choice(self, values):
        self.calls.append(("choice", tuple(values)))
        return self.choices.pop(0) if self.choices else values[0]

    def randint(self, low, high):
        self.calls.append(("randint", low, high))
        return self.randint_values.pop(0) if self.randint_values else low


class TestCombatRngCharacterization(unittest.TestCase):
    def make_player(self):
        # Player construction currently creates starter equipment with module-level RNG.
        # This fixes the fixture only; production gameplay still uses its existing RNG.
        random.seed(7001)
        player = Player()
        player.level = 200
        return player

    def test_default_combat_rng_is_the_existing_module_random(self):
        import combat_system

        combat = CombatManager(self.make_player())

        self.assertIs(combat.rng, combat_system.random)

    def test_single_hit_damage_and_critical_flag_follow_injected_rng(self):
        combat = CombatManager(self.make_player())
        combat.rng = QueueRng(uniform_values=[1.0, 0.0], random_values=[0.0])
        combat.configure_training_dummy(200, 10**9, 0, 0)
        member = combat.player.team[0]

        combat._member_attack(member, SilentSound(), force_normal=True)

        stats = combat.combat_stats.for_member(0)
        self.assertEqual(stats.damage_dealt, 538)
        self.assertEqual(stats.hit_lines, 1)
        self.assertEqual(stats.critical_count, 1)
        self.assertEqual(combat.monsters[0].hp, 10**9 - 538)
        self.assertEqual(combat.rng.calls, [
            ("uniform", 0.92, 1.08), "random", ("uniform", -10, 10), ("uniform", -10, 10)
        ])

    def test_multi_hit_damage_and_scheduling_keep_existing_seeded_payload(self):
        combat = CombatManager(self.make_player(), rng=random.Random(4096))
        combat.player.set_slot_class(0, "bowmaster")
        combat.configure_training_dummy(200, 10**9, 0, 0)
        skill = next(skill for skill in combat.player.team[0].skills if skill.skill_id == "hurricane")

        combat._member_attack(combat.player.team[0], SilentSound(), specific_skill=skill)

        self.assertEqual(combat.combat_stats.for_member(0).damage_dealt, 224)
        self.assertEqual([(hit.delay, hit.damage, hit.is_crit) for hit in combat.pending_hits], [
            (0.08, 221, False), (0.16, 221, False), (0.24, 221, False),
            (0.32, 221, False), (0.4, 221, False),
        ])

    def test_monster_normal_attack_uses_injected_damage_roll(self):
        player = self.make_player()
        rng = QueueRng(uniform_values=[0.9])
        combat = CombatManager(player)
        combat.rng = rng
        monster = Monster({"name": "RNG 怪", "lvl": 200, "hp": 1000, "atk": 100, "def": 0, "spd": 2.0})
        combat.monsters = [monster]
        hp_before = player.team[0].current_hp

        combat._monster_attack_unit(monster, SilentSound())

        self.assertEqual(hp_before - player.team[0].current_hp, 1.0)
        self.assertEqual(rng.calls, [("uniform", 0.9, 1.1), ("uniform", -10, 10)])

    def test_ready_boss_skill_keeps_priority_over_normal_attack(self):
        class ReadyShieldSkill:
            name = "固定護盾"
            is_ready = True
            target_type = "self_shield"
            shield_val = 321
            vfx_kind = "support_gate"
            vfx_color = (1, 2, 3)
            cast_desc = ""

            def trigger(self):
                self.is_ready = False

        combat = CombatManager(self.make_player(), rng=QueueRng())
        boss = Monster({"name": "RNG Boss", "lvl": 200, "hp": 1000, "atk": 999, "def": 0, "spd": 2.0}, is_boss=True)
        boss.skills = [ReadyShieldSkill()]
        combat.monsters = [boss]
        hp_before = combat.player.team[0].current_hp

        combat._monster_attack_unit(boss, SilentSound())

        self.assertEqual(boss.shield, 321)
        self.assertFalse(boss.skills[0].is_ready)
        self.assertEqual(combat.player.team[0].current_hp, hp_before)

    def test_boss_loot_rolls_and_progression_follow_injected_rng(self):
        player = self.make_player()
        rng = QueueRng(
            random_values=[0.99, 0.0, 0.99, 0.99, 0.99, 0.99],
            choices=["V"],
        )
        combat = CombatManager(player)
        combat.rng = rng
        combat.current_floor = combat.max_floors
        combat.monsters = [Monster({"name": "RNG Boss", "lvl": 160, "hp": 0, "atk": 1, "def": 0, "spd": 2.0}, is_boss=True)]

        with patch("combat_loot.generate_loot") as generate_loot:
            combat._on_monster_killed(SilentSound())

        generate_loot.assert_not_called()
        self.assertEqual(player.abby_scrolls.get("V"), 1)
        self.assertEqual(combat.current_zone_idx, 1)
        self.assertEqual(combat.current_floor, 1)
        self.assertFalse(combat.is_boss_active)

    def test_seeded_wave_generation_reproduces_monster_order_and_elite_decision(self):
        first = CombatManager(self.make_player(), rng=random.Random(1))
        second = CombatManager(self.make_player(), rng=random.Random(1))

        def snapshot(combat):
            return [(m.name, m.max_hp, m.atk, m.is_elite) for m in combat.monsters]

        self.assertEqual(snapshot(first), snapshot(second))
        self.assertEqual(len(first.monsters), 3)
        self.assertTrue(first.monsters[1].is_elite)

    def test_complete_seeded_training_combat_case_has_stable_stats_and_pending_hits(self):
        combat = CombatManager(self.make_player(), rng=random.Random(20260910))
        combat.configure_training_dummy(200, 10**12, 0, 300, is_boss=True)
        sound = SilentSound()

        for _ in range(20):
            combat.update(0.05, sound)

        stats = combat.combat_stats
        member_stats = stats.for_member(0)
        self.assertEqual((stats.total_damage, member_stats.attack_count, member_stats.hit_lines), (1393, 3, 3))
        self.assertEqual(
            [(member.damage_dealt, member.attack_count, member.hit_lines, member.critical_count)
             for member in stats.members.values()],
            [(305, 3, 3, 1), (201, 2, 2, 0), (178, 2, 5, 1), (69, 2, 2, 0),
             (148, 2, 5, 4), (115, 2, 3, 2), (377, 2, 7, 7)],
        )
        self.assertEqual(
            [(hit.delay, hit.damage, hit.is_crit, hit.skill_name) for hit in combat.pending_hits],
            [(0.009999999999999995, 41, True, "暴風神射"),
             (0.09000000000000001, 41, True, "暴風神射"),
             (0.17000000000000004, 41, True, "暴風神射"),
             (0.25000000000000006, 41, True, "暴風神射")],
        )

    def test_dps_runner_repeats_for_equivalent_player_and_rng_seed(self):
        random.seed(7001)
        first_player = self.make_player()
        random.seed(7001)
        second_player = self.make_player()

        first = run_dps_simulation(first_player, duration_sec=3.0, sim_dt=0.05, rng=random.Random(88))
        second = run_dps_simulation(second_player, duration_sec=3.0, sim_dt=0.05, rng=random.Random(88))

        self.assertEqual(first["team_damage"], second["team_damage"])
        self.assertEqual(first["team_dps"], second["team_dps"])
        self.assertEqual(first["team_damage"], 1671)
        self.assertAlmostEqual(first["team_dps"], 557.0)
        self.assertEqual(
            [(member["damage"], member["attacks"], member["crit_count"]) for member in first["members"]],
            [(member["damage"], member["attacks"], member["crit_count"]) for member in second["members"]],
        )


if __name__ == "__main__":
    unittest.main()
