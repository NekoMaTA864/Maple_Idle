"""Tests for the narrow synchronous VFX/audio CombatOutput boundary."""

import math
import os
import random
import sys
import unittest
from unittest.mock import patch


SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from combat_output import GameplayCombatOutput
from combat_system import CombatManager
from combat_vfx_manager import VisualEffectManager
from player_data import Player


class RecordingSound:
    def __init__(self):
        self.played = []

    def play(self, cue):
        self.played.append(cue)


class RecordingOutput(GameplayCombatOutput):
    def __init__(self, team_size):
        super().__init__(team_size=team_size)
        self.calls = []

    def vfx(self, *args, **kwargs):
        self.calls.append(("vfx", args, kwargs))
        return self.vfx_mgr.add_vfx(*args, **kwargs)

    def play_sound(self, sound_mgr, cue):
        self.calls.append(("audio", cue))
        return sound_mgr.play(cue)


class TestCombatOutputBoundary(unittest.TestCase):
    def make_player(self):
        random.seed(7001)
        player = Player()
        player.level = 200
        return player

    def test_default_output_keeps_the_existing_vfx_manager_facade_and_metadata(self):
        combat = CombatManager(self.make_player())

        self.assertIsInstance(combat.output, GameplayCombatOutput)
        self.assertIs(combat.vfx_mgr, combat.output.vfx_mgr)
        random.seed(13579)
        before = random.getstate()
        combat.emit_vfx(
            "dimension_rift", 10, 20, 30, 40, (1, 2, 3), duration=0.75,
            source_slot=2, target_monster_idx=1, target_slot=4,
        )
        after = random.getstate()
        random.setstate(before)
        random.uniform(0, 6.28)
        for _ in range(6):
            random.uniform(0, math.tau)
            random.uniform(50, 110)
            random.uniform(-0.4, 0.4)
        effect = combat.vfx_mgr.effects[-1]
        self.assertEqual(
            (effect.kind, effect.x, effect.y, effect.target_x, effect.target_y, effect.color, effect.duration,
             effect.source_slot, effect.target_monster_idx, effect.target_slot),
            ("dimension_rift", 10.0, 20.0, 30.0, 40.0, (1, 2, 3), 0.75, 2, 1, 4),
        )
        self.assertEqual(len(effect.fracture_lines), 6)
        self.assertEqual(after, random.getstate())

    def test_default_output_preserves_existing_vfx_cap_and_drop_telemetry(self):
        combat = CombatManager(self.make_player())

        for index in range(VisualEffectManager.MAX_CONCURRENT_EFFECTS + 1):
            combat.emit_vfx("slash", index, 0)

        self.assertEqual(len(combat.vfx_mgr.effects), VisualEffectManager.MAX_CONCURRENT_EFFECTS)
        self.assertEqual(combat.vfx_mgr.total_dropped_effects, 1)

    def test_injected_output_receives_vfx_and_audio_immediately_without_participant_contracts(self):
        player = self.make_player()
        output = RecordingOutput(team_size=len(player.team))
        combat = CombatManager(player, output=output)
        sound = RecordingSound()

        combat.emit_vfx("slash", 10, 20, source_slot=0, target_monster_idx=0)
        combat.play_sound(sound, "hit")

        self.assertIs(combat.vfx_mgr, output.vfx_mgr)
        self.assertEqual(output.calls, [
            ("vfx", ("slash", 10, 20), {"source_slot": 0, "target_monster_idx": 0}),
            ("audio", "hit"),
        ])
        self.assertEqual(sound.played, ["hit"])

    def test_presentation_state_is_owned_by_output_behind_legacy_manager_properties(self):
        combat = CombatManager(self.make_player())

        self.assertIs(combat.vfx_mgr, combat.output.vfx_mgr)
        self.assertIs(combat.floating_popups, combat.output.floating_popups)
        self.assertIs(combat.combat_logs, combat.output.combat_logs)
        self.assertIs(combat.shake_team, combat.output.shake_team)
        combat.shake_monster = 4.0
        combat.shake_team[0] = 3.0

        self.assertEqual(combat.output.shake_monster, 4.0)
        self.assertEqual(combat.output.shake_team[0], 3.0)

    def test_log_timestamp_order_and_cap_are_preserved_by_legacy_facade(self):
        combat = CombatManager(self.make_player())
        combat.combat_logs.clear()
        combat.max_logs = 2

        with patch("combat_system.time.strftime", side_effect=["01:02:03", "01:02:04", "01:02:05"]):
            combat.add_log("first", (1, 1, 1))
            combat.add_log("second", (2, 2, 2))
            combat.add_log("third", (3, 3, 3))

        self.assertEqual(combat.combat_logs, [
            {"time": "01:02:04", "text": "second", "color": (2, 2, 2)},
            {"time": "01:02:05", "text": "third", "color": (3, 3, 3)},
        ])
        self.assertIs(combat.combat_logs, combat.output.combat_logs)

    def test_shake_assignment_and_decay_keep_existing_rate_and_floor(self):
        combat = CombatManager(self.make_player())
        combat.set_shake("team", 7.0, index=0)
        combat.set_shake("monster", 10.0)

        combat.output.update(0.1)

        self.assertEqual(combat.shake_team[0], 4.0)
        self.assertEqual(combat.shake_monster, 7.0)
        combat.output.update(1.0)
        self.assertEqual(combat.shake_team[0], 0.0)
        self.assertEqual(combat.shake_monster, 0.0)


if __name__ == "__main__":
    unittest.main()
