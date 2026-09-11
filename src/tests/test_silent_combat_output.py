"""Parity and presentation-absence tests for SilentCombatOutput."""

import copy
from dataclasses import asdict
import os
import random
import sys
import unittest
from unittest.mock import patch


SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from combat_output import GameplayCombatOutput, SilentCombatOutput
from combat_system import CombatManager
from dps_calculator import run_dps_simulation
from player_data import Player


class FailIfPlayedSound:
    def play(self, cue):
        raise AssertionError(f"silent output delegated audio cue: {cue}")


class TestSilentCombatOutput(unittest.TestCase):
    def make_player(self):
        random.seed(7001)
        player = Player()
        player.level = 200
        return player

    def combat_snapshot(self, combat):
        return {
            "monsters": [
                (
                    monster.name, monster.hp, monster.max_hp, monster.shield,
                    monster.freeze_timer, monster.burn_timer, monster.burn_tick,
                    monster.burn_dmg, monster.bleed_timer, monster.bleed_tick,
                    monster.bleed_dmg, monster.chill_timer, monster.attack_timer,
                    monster.is_alive,
                )
                for monster in combat.monsters
            ],
            "members": [
                (
                    member.slot_idx, member.current_hp, member.shield,
                    member.is_buffed, member.buff_timer, member.mechanic_stacks,
                    member.attack_timer, member.cast_delay_timer,
                    tuple((skill.skill_id, skill.current_cd) for skill in member.skills),
                )
                for member in combat.player.team
            ],
            "stats": asdict(combat.combat_stats),
            "pending_hits": [
                (
                    hit.delay, hit.member.slot_idx, hit.target_name, hit.skill_name,
                    hit.damage, hit.is_crit, hit.vfx_type, hit.vfx_color,
                    hit.target_monster_idx,
                )
                for hit in combat.pending_hits
            ],
            "team_buffs": copy.deepcopy(combat.player.team_buffs),
            "progression": (
                combat.current_zone_idx, combat.current_floor, combat.unlocked_zones,
                combat.is_boss_active, combat.is_resting, combat.respawn_timer,
                combat.boss_miasma_timer,
            ),
            "player": (
                combat.player.level, combat.player.exp, combat.player.gold,
            ),
        }

    def run_training_case(self, base_player, output_factory, visual_state):
        player = copy.deepcopy(base_player)
        combat_rng = random.Random(20260911)
        random.setstate(visual_state)
        combat = CombatManager(player, rng=combat_rng, output=output_factory(len(player.team)))
        combat.configure_training_dummy(200, 10**12, 0, 300, count=2, is_boss=True)
        sound = FailIfPlayedSound() if isinstance(combat.output, SilentCombatOutput) else type(
            "NoopSound", (), {"play": lambda self, cue: None}
        )()
        for _ in range(40):
            combat.update(0.05, sound)
        return self.combat_snapshot(combat), combat_rng.getstate(), random.getstate()

    def test_gameplay_and_silent_outputs_keep_domain_and_both_rng_states_equal(self):
        base_player = self.make_player()
        random.seed(314159)
        visual_state = random.getstate()

        gameplay = self.run_training_case(
            base_player,
            lambda team_size: GameplayCombatOutput(team_size=team_size),
            visual_state,
        )
        silent = self.run_training_case(
            base_player,
            lambda team_size: SilentCombatOutput(),
            visual_state,
        )

        self.assertEqual(silent, gameplay)

    def test_gold_dungeon_reward_progression_and_rng_match_gameplay_output(self):
        base_player = self.make_player()
        random.seed(271828)
        visual_state = random.getstate()

        def run(output_factory):
            player = copy.deepcopy(base_player)
            combat_rng = random.Random(99)
            random.setstate(visual_state)
            combat = CombatManager(player, rng=combat_rng, output=output_factory(len(player.team)))
            combat.enter_gold_dungeon()
            combat.monsters[0].hp = 0
            sound = FailIfPlayedSound() if isinstance(combat.output, SilentCombatOutput) else type(
                "NoopSound", (), {"play": lambda self, cue: None}
            )()
            combat._on_monster_killed(sound)
            result = (
                player.gold, player.exp, combat.current_zone_idx, combat.current_floor,
                tuple((monster.name, monster.hp, monster.max_hp) for monster in combat.monsters),
            )
            return result, combat_rng.getstate(), random.getstate()

        gameplay = run(lambda team_size: GameplayCombatOutput(team_size=team_size))
        silent = run(lambda team_size: SilentCombatOutput())

        self.assertEqual(silent, gameplay)

    def test_silent_vfx_consumes_the_same_one_and_nineteen_visual_random_draws(self):
        for kind in ("slash", "dimension_rift"):
            with self.subTest(kind=kind):
                random.seed(123456)
                GameplayCombatOutput().vfx(kind, 1, 2)
                gameplay_state = random.getstate()

                random.seed(123456)
                SilentCombatOutput().vfx(kind, 1, 2)
                silent_state = random.getstate()

                self.assertEqual(silent_state, gameplay_state)

    def test_silent_combat_creates_no_manager_or_presentation_state(self):
        player = self.make_player()
        output = SilentCombatOutput()

        with patch("combat_output.VisualEffectManager.__init__", side_effect=AssertionError("VFX manager created")):
            combat = CombatManager(player, rng=random.Random(7), output=output)
            combat.configure_training_dummy(200, 10**9, 0, 0)
            combat.update(0.05, FailIfPlayedSound())

        for attribute in (
            "vfx_mgr", "effects", "floating_popups", "combat_logs",
            "shake_team", "shake_monster",
        ):
            self.assertFalse(hasattr(output, attribute), attribute)
        with self.assertRaises(AttributeError):
            _ = combat.vfx_mgr

    def test_dps_runner_uses_silent_output_without_vfx_manager(self):
        player = self.make_player()

        with patch("combat_output.VisualEffectManager.__init__", side_effect=AssertionError("VFX manager created")):
            result = run_dps_simulation(
                player,
                duration_sec=3.0,
                sim_dt=0.05,
                rng=random.Random(88),
            )

        self.assertGreater(result["team_damage"], 0)
        self.assertGreater(result["team_dps"], 0)


if __name__ == "__main__":
    unittest.main()
