"""Characterization tests for the existing multi-hit pending-hit queue semantics."""

import os
import sys
import unittest

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from classes import ALL_CLASSES
from combat_events import PendingHit
from combat_system import CombatManager
from player_data import Player


class SilentSound:
    def __init__(self):
        self.played = []

    def play(self, sound_name):
        self.played.append(sound_name)


class FixedCombatRng:
    def __init__(self, uniform_value, random_value):
        self.uniform_value = uniform_value
        self.random_value = random_value

    def uniform(self, _low, _high):
        return self.uniform_value

    def random(self):
        return self.random_value


class TestPendingHitQueueCharacterization(unittest.TestCase):
    def setUp(self):
        self.player = Player()
        self.player.level = 200
        self.player.set_slot_class(0, "bowmaster")
        self.member = self.player.team[0]
        self.skill = next(skill for skill in ALL_CLASSES["bowmaster"]["skills"] if skill.skill_id == "hurricane")
        self.combat = CombatManager(self.player)
        self.combat.configure_training_dummy(200, 10**12, 0, 0, count=1)
        self.sound = SilentSound()

    def _queue_hurricane(self, random_roll=0.99):
        """Queue a known six-hit skill with deterministic damage and crit rolls."""
        target = self.combat.monsters[0]
        hp_before = target.hp
        self.combat.rng = FixedCombatRng(uniform_value=1.0, random_value=random_roll)
        self.combat._member_attack(self.member, self.sound, specific_skill=self.skill)
        return hp_before - target.hp

    def _freeze_actions_after_queue_processing(self):
        # Queue processing happens before the resting early return in update().
        self.combat.is_resting = True
        self.combat.respawn_timer = 999.0

    def test_hurricane_queues_five_follow_ups_after_immediate_first_hit(self):
        immediate_damage = self._queue_hurricane()

        self.assertGreater(immediate_damage, 0)
        self.assertEqual(self.combat.combat_stats.for_member(0).hit_lines, 1)
        self.assertEqual(len(self.combat.pending_hits), 5)
        self.assertEqual([hit.delay for hit in self.combat.pending_hits], [0.08, 0.16, 0.24, 0.32, 0.4])
        self.assertTrue(all(hit.member is self.member for hit in self.combat.pending_hits))
        self.assertEqual([hit.target_name for hit in self.combat.pending_hits], ["monster_0"] * 5)
        self.assertEqual([hit.target_monster_idx for hit in self.combat.pending_hits], [0] * 5)
        self.assertEqual([hit.skill_name for hit in self.combat.pending_hits], [self.skill.name] * 5)
        self.assertTrue(all(hit.damage == self.combat.pending_hits[0].damage for hit in self.combat.pending_hits))
        self.assertTrue(all(hit.is_crit is False for hit in self.combat.pending_hits))
        self.assertFalse(hasattr(self.combat.pending_hits[0], "miss"))

    def test_pending_hit_waits_for_its_delay_then_executes_and_is_removed(self):
        self._queue_hurricane()
        self._freeze_actions_after_queue_processing()
        target = self.combat.monsters[0]
        hp_after_first_hit = target.hp

        self.combat.update(0.079, self.sound)
        self.assertEqual(len(self.combat.pending_hits), 5)
        self.assertEqual(self.combat.combat_stats.for_member(0).hit_lines, 1)
        self.assertEqual(target.hp, hp_after_first_hit)
        self.assertGreater(self.combat.pending_hits[0].delay, 0.0)

        self.combat.update(0.0011, self.sound)
        self.assertEqual(len(self.combat.pending_hits), 4)
        self.assertEqual(self.combat.combat_stats.for_member(0).hit_lines, 2)
        self.assertEqual(target.hp, hp_after_first_hit - self.combat.pending_hits[0].damage)

    def test_same_delay_hits_execute_in_insertion_order_and_large_dt_consumes_all(self):
        self._freeze_actions_after_queue_processing()
        first = PendingHit(0.08, self.member, "first", "first", 11, False, "slash", (1, 2, 3))
        second = PendingHit(0.08, self.member, "second", "second", 22, True, "ice", (4, 5, 6))
        third = PendingHit(0.16, self.member, "third", "third", 33, False, "arrow", (7, 8, 9))
        self.combat.pending_hits = [first, second, third]
        executed = []
        self.combat._execute_pending_hit = lambda hit, sound: executed.append(hit.skill_name)

        self.combat.update(0.2, self.sound)

        self.assertEqual(executed, ["first", "second", "third"])
        self.assertEqual(self.combat.pending_hits, [])

    def test_critical_follow_up_payload_keeps_critical_flag_and_damage_payload(self):
        self._queue_hurricane(random_roll=0.0)

        self.assertTrue(all(hit.is_crit for hit in self.combat.pending_hits))
        self.assertTrue(all(hit.damage > 0 for hit in self.combat.pending_hits))
        self.assertTrue(all(hit.vfx_type == self.skill.effect_name for hit in self.combat.pending_hits))
        self.assertTrue(all(hit.vfx_color == self.skill.color for hit in self.combat.pending_hits))

    def test_dead_original_target_retargets_first_living_monster_when_follow_up_executes(self):
        self.combat.configure_training_dummy(200, 10**12, 0, 0, count=2)
        self._queue_hurricane()
        self.combat.pending_hits = [self.combat.pending_hits[0]]
        pending = self.combat.pending_hits[0]
        original_target, replacement_target = self.combat.monsters
        original_target.hp = 0
        replacement_hp_before = replacement_target.hp
        self._freeze_actions_after_queue_processing()

        self.combat.update(0.08, self.sound)

        self.assertEqual(self.combat.pending_hits, [])
        self.assertEqual(replacement_target.hp, replacement_hp_before - pending.damage)
        self.assertEqual(self.combat.combat_stats.for_member(0).hit_lines, 2)

    def test_pending_hits_remain_unchanged_while_no_monster_is_alive(self):
        self._queue_hurricane()
        self._freeze_actions_after_queue_processing()
        pending = self.combat.pending_hits[0]
        initial_delay = pending.delay
        self.combat.monsters[0].hp = 0

        self.combat.update(1.0, self.sound)

        self.assertEqual(len(self.combat.pending_hits), 5)
        self.assertIs(self.combat.pending_hits[0], pending)
        self.assertEqual(pending.delay, initial_delay)


if __name__ == "__main__":
    unittest.main()
