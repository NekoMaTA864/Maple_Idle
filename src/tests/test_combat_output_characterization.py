"""Characterization safety net for the current synchronous combat presentation output.

These tests deliberately observe today's call order before CombatOutput exists.  They
are not a proposed presentation API.
"""

import math
import os
import random
import sys
import unittest
from unittest.mock import patch


SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from combat_events import PendingHit
from combat_output import GameplayCombatOutput
from combat_system import CombatManager
from combat_vfx_manager import VisualEffect, VisualEffectManager
from monster import Monster
from player_data import Player
from skills import Skill


class TraceRng:
    """Deterministic combat RNG sufficient for the exercised existing paths."""

    def __init__(self, random_value=0.99):
        self.random_value = random_value
        self.calls = []

    def uniform(self, low, high):
        self.calls.append(("uniform", low, high))
        return 1.0 if (low, high) == (0.92, 1.08) else (low + high) / 2

    def random(self):
        self.calls.append("random")
        return self.random_value

    def choice(self, values):
        self.calls.append(("choice", tuple(values)))
        return values[0]


class RecordingSound:
    def __init__(self, timeline):
        self.timeline = timeline
        self.played = []

    def play(self, name):
        self.played.append(name)
        self.timeline.append(f"audio:{name}")


class TraceList(list):
    def __init__(self, timeline, label, values=()):
        super().__init__(values)
        self.timeline = timeline
        self.label = label

    def append(self, value):
        self.timeline.append(self.label)
        super().append(value)

    def __setitem__(self, index, value):
        self.timeline.append(self.label)
        super().__setitem__(index, value)


class TracingMonster(Monster):
    def __init__(self, data, timeline, is_boss=False):
        object.__setattr__(self, "_trace_timeline", timeline)
        object.__setattr__(self, "_trace_enabled", False)
        super().__init__(data, is_boss=is_boss)
        object.__setattr__(self, "_trace_enabled", True)

    def __setattr__(self, name, value):
        if getattr(self, "_trace_enabled", False) and name in {"hp", "shield", "burn_timer"}:
            label = {"hp": "domain:monster_hp", "shield": "domain:shield", "burn_timer": "status:burn"}[name]
            self._trace_timeline.append(label)
        super().__setattr__(name, value)


class TraceCombatManager(CombatManager):
    def __init__(self, *args, **kwargs):
        object.__setattr__(self, "timeline", [])
        object.__setattr__(self, "_trace_enabled", False)
        super().__init__(*args, **kwargs)
        object.__setattr__(self, "_trace_enabled", True)

    def __setattr__(self, name, value):
        if getattr(self, "_trace_enabled", False):
            if name == "shake_monster":
                self.timeline.append("shake:monster")
            elif name == "is_resting" and value:
                self.timeline.append("rest")
            elif name == "floating_popups":
                self.timeline.append("popup:update")
        super().__setattr__(name, value)


class TraceGameplayCombatOutput(GameplayCombatOutput):
    def __init__(self, timeline, **kwargs):
        object.__setattr__(self, "timeline", timeline)
        object.__setattr__(self, "_trace_enabled", False)
        super().__init__(**kwargs)
        object.__setattr__(self, "_trace_enabled", True)

    def __setattr__(self, name, value):
        if getattr(self, "_trace_enabled", False):
            if name == "shake_monster":
                self.timeline.append("shake:monster")
            elif name == "floating_popups":
                self.timeline.append("popup:update")
        super().__setattr__(name, value)


def wrap_method(obj, method_name, timeline, label):
    original = getattr(obj, method_name)

    def wrapped(*args, **kwargs):
        timeline.append(label)
        return original(*args, **kwargs)

    setattr(obj, method_name, wrapped)


def install_presentation_trace(combat):
    timeline = combat.timeline
    wrap_method(combat.vfx_mgr, "add_vfx", timeline, "vfx")
    wrap_method(combat, "add_popup", timeline, "popup")
    wrap_method(combat, "add_log", timeline, "log")
    original_set_shake = combat.set_shake

    def traced_set_shake(target, value, index=None):
        timeline.append(f"shake:{target}")
        return original_set_shake(target, value, index=index)

    combat.set_shake = traced_set_shake


class TestCombatOutputCharacterization(unittest.TestCase):
    def make_combat(self, rng=None):
        random.seed(7001)  # Player construction currently uses module-level RNG.
        player = Player()
        player.level = 200
        return TraceCombatManager(player, rng=rng)

    def replace_with_trace_monster(self, combat, hp=10**9, atk=1, is_boss=False):
        monster = TracingMonster(
            {"name": "trace target", "lvl": 200, "hp": hp, "atk": atk, "def": 0, "spd": 2.0},
            combat.timeline,
            is_boss=is_boss,
        )
        combat.monsters = [monster]
        return monster

    def test_player_single_hit_orders_damage_stats_vfx_popup_shake_log_audio_and_lifesteal(self):
        combat = self.make_combat(rng=TraceRng())
        target = self.replace_with_trace_monster(combat)
        member = combat.player.team[0]
        member.current_hp = max(1, member.current_hp - 1000)
        install_presentation_trace(combat)
        wrap_method(combat.combat_stats, "record_damage", combat.timeline, "stats:damage")
        wrap_method(combat.combat_stats, "record_healing", combat.timeline, "stats:healing")
        sound = RecordingSound(combat.timeline)

        combat._member_attack(member, sound, force_normal=True)

        self.assertEqual(combat.timeline, [
            "domain:monster_hp", "stats:damage", "vfx", "popup", "shake:monster",
            "log", "audio:hit", "stats:healing", "popup",
        ])
        self.assertGreater(target.hp, 0)

    def test_player_multi_hit_applies_status_before_vfx_and_queues_after_popup(self):
        combat = self.make_combat(rng=TraceRng())
        self.replace_with_trace_monster(combat)
        install_presentation_trace(combat)
        wrap_method(combat.combat_stats, "record_damage", combat.timeline, "stats:damage")
        combat.pending_hits = TraceList(combat.timeline, "pending:append")
        skill = Skill(
            "trace_burn_combo", "Trace Burn Combo", cooldown=3.0, dmg_mult=1.0,
            skill_type="multi_hit", hit_count=2, dot_type="burn", buff_duration=4.0,
            effect_name="slash", color=(1, 2, 3),
        )
        original_trigger = skill.trigger

        def traced_trigger():
            combat.timeline.append("cooldown")
            original_trigger()

        skill.trigger = traced_trigger
        sound = RecordingSound(combat.timeline)

        combat._member_attack(combat.player.team[0], sound, specific_skill=skill)

        self.assertEqual(combat.timeline, [
            "domain:monster_hp", "stats:damage", "status:burn", "vfx", "popup",
            "pending:append", "shake:monster", "cooldown", "popup", "log", "audio:hit", "popup",
        ])
        self.assertEqual([hit.delay for hit in combat.pending_hits], [0.08])

    def test_pending_hit_execution_orders_damage_vfx_shake_popup_audio_then_kill_handler(self):
        combat = self.make_combat(rng=TraceRng())
        target = self.replace_with_trace_monster(combat, hp=10)
        install_presentation_trace(combat)
        wrap_method(combat.combat_stats, "record_damage", combat.timeline, "stats:damage")
        combat._on_monster_killed = lambda sound: combat.timeline.append("kill:handler")
        hit = PendingHit(0.0, combat.player.team[0], "target", "Trace", 10, False, "slash", (1, 2, 3))

        combat._execute_pending_hit(hit, RecordingSound(combat.timeline))

        self.assertEqual(target.hp, 0)
        self.assertEqual(combat.timeline, [
            "domain:monster_hp", "stats:damage", "vfx", "shake:monster", "popup", "audio:hit", "kill:handler",
        ])

    def test_monster_normal_attack_orders_damage_audio_shake_vfx_popup_log_then_death_and_rest(self):
        combat = self.make_combat(rng=TraceRng())
        monster = self.replace_with_trace_monster(combat, atk=10**9)
        member = combat.player.team[0]
        member.current_hp = 1
        install_presentation_trace(combat)
        wrap_method(combat.combat_stats, "record_damage_taken", combat.timeline, "stats:damage_taken")
        wrap_method(combat.combat_stats, "record_death", combat.timeline, "stats:death")
        original_take_damage = member.take_damage

        def traced_take_damage(damage):
            result = original_take_damage(damage)
            combat.timeline.append("domain:member_hp")
            return result

        member.take_damage = traced_take_damage
        combat._monster_attack_unit(monster, RecordingSound(combat.timeline))

        self.assertEqual(combat.timeline, [
            "domain:member_hp", "stats:damage_taken", "audio:hit", "shake:team", "vfx", "popup", "log",
            "stats:death", "rest", "log",
        ])

    def test_boss_self_shield_cast_orders_popup_log_audio_before_shield_effect(self):
        combat = self.make_combat(rng=TraceRng())
        boss = self.replace_with_trace_monster(combat, is_boss=True)
        install_presentation_trace(combat)

        class ShieldSkill:
            name = "Trace Barrier"
            target_type = "self_shield"
            shield_val = 321
            vfx_kind = "support_gate"
            vfx_color = (9, 8, 7)
            cast_desc = "trace"

        combat._execute_monster_skill(ShieldSkill(), combat.player.team, RecordingSound(combat.timeline), boss_monster=boss)

        self.assertEqual(combat.timeline, ["popup", "log", "audio:crit", "domain:shield", "popup", "vfx"])
        self.assertEqual(boss.shield, 321)

    def test_gold_dungeon_reward_mutates_before_immediate_outputs_then_respawns(self):
        combat = self.make_combat(rng=TraceRng())
        combat.enter_gold_dungeon()
        combat.timeline.clear()
        install_presentation_trace(combat)
        wrap_method(combat.player, "add_gold", combat.timeline, "domain:gold")
        wrap_method(combat, "_spawn_gold_dungeon_monster", combat.timeline, "spawn:gold_dungeon")

        combat._on_monster_killed(RecordingSound(combat.timeline))

        self.assertEqual(combat.timeline, [
            "domain:gold", "audio:coin", "popup", "log", "spawn:gold_dungeon",
        ])

    def test_plain_vfx_consumes_one_module_random_uniform_and_advances_state_once(self):
        random.seed(24680)
        before = random.getstate()
        calls = []
        original_uniform = random.uniform

        def recording_uniform(low, high):
            calls.append((low, high))
            return original_uniform(low, high)

        with patch("combat_vfx_manager.random.uniform", side_effect=recording_uniform):
            VisualEffect("slash", 1, 2)
        after = random.getstate()
        random.setstate(before)
        original_uniform(0, 6.28)
        expected_after = random.getstate()

        self.assertEqual(calls, [(0, 6.28)])
        self.assertEqual(after, expected_after)

    def test_dimension_rift_vfx_consumes_nineteen_module_random_uniform_calls(self):
        random.seed(13579)
        before = random.getstate()
        calls = []
        original_uniform = random.uniform

        def recording_uniform(low, high):
            calls.append((low, high))
            return original_uniform(low, high)

        with patch("combat_vfx_manager.random.uniform", side_effect=recording_uniform):
            VisualEffect("dimension_rift", 1, 2)
        after = random.getstate()
        random.setstate(before)
        original_uniform(0, 6.28)
        for _ in range(6):
            original_uniform(0, math.tau)
            original_uniform(50, 110)
            original_uniform(-0.4, 0.4)
        expected_after = random.getstate()

        self.assertEqual(len(calls), 19)
        self.assertEqual(calls[0], (0, 6.28))
        self.assertEqual(calls[1:], [(0, math.tau), (50, 110), (-0.4, 0.4)] * 6)
        self.assertEqual(after, expected_after)

    def test_popup_payload_lifecycle_and_rng_consumption_are_currently_manager_owned(self):
        rng = TraceRng()
        combat = self.make_combat(rng=rng)
        rng.calls.clear()  # Combat construction also legitimately consumes its injected RNG.
        popups = combat.floating_popups

        combat.add_popup("trace", "monster_0", (1, 2, 3), is_crit=True, is_skill=True)

        self.assertIs(combat.floating_popups, popups)
        self.assertEqual(combat.floating_popups, [{
            "text": "trace", "target": "monster_0", "color": (1, 2, 3), "is_crit": True,
            "is_skill": True, "life": 40, "max_life": 40, "offset_y": -8, "offset_x": 0.0,
        }])
        self.assertEqual(rng.calls, [("uniform", -10, 10)])

        combat.is_resting = True
        combat.respawn_timer = 999.0
        combat.update(0.0, RecordingSound(combat.timeline))
        self.assertEqual(combat.floating_popups[0]["life"], 39)
        self.assertEqual(combat.floating_popups[0]["offset_y"], -9.3)
        for _ in range(39):
            combat.update(0.0, RecordingSound(combat.timeline))
        self.assertEqual(combat.floating_popups, [])

    def test_legacy_presentation_facade_exposes_mutable_collections_and_in_place_add_helpers(self):
        combat = self.make_combat(rng=TraceRng())
        vfx_mgr = combat.vfx_mgr
        popups = combat.floating_popups
        logs = combat.combat_logs
        shakes = combat.shake_team

        self.assertIsInstance(vfx_mgr, VisualEffectManager)
        self.assertIsInstance(popups, list)
        self.assertIsInstance(logs, list)
        self.assertIsInstance(shakes, list)
        combat.vfx_mgr.effects.append("direct-vfx-state")
        combat.floating_popups.append({"direct": "popup"})
        combat.combat_logs.append({"direct": "log"})
        combat.shake_team[0] = 3.0
        combat.shake_monster = 4.0
        combat.add_popup("helper", "monster_0", (1, 2, 3))
        combat.add_log("helper", (4, 5, 6))

        self.assertIs(combat.vfx_mgr, vfx_mgr)
        self.assertIs(combat.floating_popups, popups)
        self.assertIs(combat.combat_logs, logs)
        self.assertIs(combat.shake_team, shakes)
        self.assertEqual(combat.vfx_mgr.effects[0], "direct-vfx-state")
        self.assertEqual(combat.floating_popups[0], {"direct": "popup"})
        self.assertEqual(combat.combat_logs[0], {"direct": "log"})
        self.assertEqual(combat.shake_team[0], 3.0)
        self.assertEqual(combat.shake_monster, 4.0)

    def test_update_runs_vfx_then_shake_then_popup_before_due_pending_hit(self):
        combat = self.make_combat(rng=TraceRng())
        combat.output = TraceGameplayCombatOutput(
            combat.timeline,
            vfx_mgr=combat.vfx_mgr,
            team_size=len(combat.player.team),
        )
        combat.vfx_mgr.add_vfx("slash", 1, 2)
        original_vfx_update = combat.vfx_mgr.update

        def traced_vfx_update(*args, **kwargs):
            combat.timeline.append("vfx:update")
            return original_vfx_update(*args, **kwargs)

        combat.vfx_mgr.update = traced_vfx_update
        combat.shake_team = TraceList(combat.timeline, "shake:team", combat.shake_team)
        combat.shake_team[0] = 1.0
        combat.shake_monster = 1.0
        combat.floating_popups = [{
            "text": "trace", "target": "monster_0", "color": (1, 2, 3), "is_crit": False,
            "is_skill": False, "life": 2, "max_life": 2, "offset_y": -8, "offset_x": 0,
        }]
        combat.pending_hits = [PendingHit(0.0, combat.player.team[0], "target", "Trace", 1, False, "slash", (1, 2, 3))]
        combat._execute_pending_hit = lambda hit, sound: combat.timeline.append("pending:execute")
        combat.is_resting = True
        combat.respawn_timer = 999.0
        combat.timeline.clear()

        combat.update(0.1, RecordingSound(combat.timeline))

        self.assertEqual(combat.timeline, [
            "vfx:update", "shake:team", "shake:monster", "popup:update", "pending:execute",
        ])


if __name__ == "__main__":
    unittest.main()
