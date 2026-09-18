"""Focused tests for the vertical VFX prototype presentation layer."""

import os
import random
import sys
import unittest

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication


SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from arena_layout import ArenaLayout
from combat_avatar import AVATAR_DEFINITIONS, CombatAvatar
from combat_vfx_manager import VisualEffectManager
from tools.vfx_gallery import GalleryCombatState
from vfx_prototype import (
    AreaEffect,
    ImpactEffect,
    LightningEffect,
    MarkDetonationEffect,
    PRESETS,
    PersistentEffect,
    ProjectileEffect,
    SlashEffect,
    SpreadProjectileEffect,
    create_effect,
    emit_vfx,
    resolve_preset,
)


class TestVerticalVFXPrototype(unittest.TestCase):
    def test_vertical_layout_places_enemy_above_player_and_skills_below(self):
        layout = ArenaLayout(800, 600)
        enemy = layout.enemy_position(1, 3)
        player = layout.player_position()
        skills = layout.skill_positions(4)

        self.assertLess(enemy[1], player[1])
        self.assertGreater(skills[0][1], player[1])
        self.assertEqual(len(layout.enemy_positions(3)), 3)
        self.assertEqual(len(skills), 4)

    def test_enemy_and_avatar_anchor_resolution(self):
        layout = ArenaLayout(800, 600)
        avatar = CombatAvatar("cannon")
        center = layout.player_position()
        anchors = avatar.anchors(center)
        self.assertEqual(set(anchors), set(AVATAR_DEFINITIONS["cannon"].anchors))
        self.assertLess(anchors["muzzle"][1], anchors["center"][1])
        enemy = layout.enemy_anchors(1, 3)
        self.assertEqual(set(enemy), {"center", "hit", "ground"})
        self.assertGreater(enemy["ground"][1], enemy["hit"][1])

    def test_anchor_positions_follow_arbitrary_arena_sizes(self):
        avatar = CombatAvatar("hero")
        small = ArenaLayout(480, 440)
        large = ArenaLayout(1200, 900)
        small_tip = avatar.anchor("tip", small.player_position())
        large_tip = avatar.anchor("tip", large.player_position())
        self.assertNotEqual(small_tip, large_tip)
        self.assertAlmostEqual(small_tip[0], 240.0, places=4)
        self.assertAlmostEqual(large_tip[0], 600.0, places=4)

    def test_projectile_starts_from_avatar_attack_anchor(self):
        avatar = CombatAvatar("night_lord")
        origin = avatar.anchor("attack_origin", (400, 400))
        effect = create_effect("night_lord_shuriken", origin, (400, 130))
        self.assertEqual(effect.source, origin)
        self.assertEqual(effect.shape, "shuriken")

    def test_all_required_presets_resolve_to_presentation_types(self):
        expected = {
            "hero_slash": SlashEffect,
            "hero_rage_attack": SlashEffect,
            "hero_sword_illusion": SlashEffect,
            "hero_burning_soul_sword": PersistentEffect,
            "hero_spatial_slash": SlashEffect,
            "hero_fighting_instinct": PersistentEffect,
            "hero_sacred_sword_descent": ProjectileEffect,
            "night_lord_shuriken": ProjectileEffect,
            "night_lord_four_flying": ProjectileEffect,
            "night_lord_taunt_contract": MarkDetonationEffect,
            "night_lord_fuma_shuriken": ProjectileEffect,
            "night_lord_dakrus_secret": ProjectileEffect,
            "night_lord_spread_throw": SpreadProjectileEffect,
            "night_lord_detonation_talisman": MarkDetonationEffect,
            "cannonball_heavy": ProjectileEffect,
            "bishop_holy_area": AreaEffect,
        }
        for name, effect_type in expected.items():
            definition = resolve_preset(name)
            self.assertEqual(definition.effect_type, PRESETS[name].effect_type)
            effect = create_effect(name, (400, 480), (400, 120))
            self.assertIsInstance(effect, effect_type)

    def test_hero_presets_keep_variants_in_presentation_data(self):
        spatial = create_effect("hero_spatial_slash", (400, 480), (400, 120))
        spatial.set_progress(0.5)
        self.assertEqual(spatial.style, "rift")
        self.assertEqual(spatial.variant, "normal")

        empowered = create_effect(
            "hero_spatial_slash", (400, 480), (400, 120), variant="empowered"
        )
        self.assertEqual(empowered.variant, "empowered")
        sacred = create_effect(
            "hero_sacred_sword_descent", (400, 300), (400, 120), variant="stronger"
        )
        self.assertEqual(sacred.variant, "stronger")

    def test_presets_contain_no_gameplay_parameters(self):
        forbidden = {"damage", "cooldown", "hit_count", "buff", "priority", "progression"}
        for definition in PRESETS.values():
            self.assertTrue(forbidden.isdisjoint(definition.params))

    def test_slash_lifecycle_and_directional_geometry(self):
        effect = SlashEffect((300, 500), (150, 140), lifetime=0.4)
        self.assertTrue(effect.is_alive)
        effect.update(0.2)
        self.assertAlmostEqual(effect.progress, 0.5, places=4)
        effect.update(0.2)
        self.assertFalse(effect.is_alive)
        self.assertEqual(effect.source, (300.0, 500.0))
        self.assertEqual(effect.target, (150.0, 140.0))

    def test_projectile_moves_from_source_to_target_without_axis_assumption(self):
        effect = ProjectileEffect((320, 80), (40, 260), lifetime=1.0)
        effect.update(0.5)
        self.assertAlmostEqual(effect.position[0], 180.0, places=4)
        self.assertAlmostEqual(effect.position[1], 170.0, places=4)
        effect.update(0.5)
        self.assertAlmostEqual(effect.position[0], 40.0, places=4)
        self.assertAlmostEqual(effect.position[1], 260.0, places=4)

    def test_projectile_homing_can_update_target_without_gameplay_state(self):
        effect = ProjectileEffect((0, 0), (100, 100), lifetime=1.0, homing=True)
        effect.update(0.25, target=(200, 40))
        self.assertEqual(effect.target, (200.0, 40.0))
        self.assertGreater(effect.position[0], 0.0)

    def test_night_lord_spread_composition_uses_arbitrary_source_and_target(self):
        effect = create_effect(
            "night_lord_spread_throw",
            (320, 80),
            (40, 260),
        )
        self.assertIsInstance(effect, SpreadProjectileEffect)
        self.assertEqual(len(effect.projectile_targets), 5)
        effect.set_progress(0.5)
        positions = effect.projectile_positions
        self.assertEqual(len(positions), 5)
        self.assertNotEqual(positions[0], positions[-1])
        self.assertTrue(effect.is_alive)
        manager = VisualEffectManager()
        manager.add_effect(effect)
        manager.update(effect.duration + 0.01)
        self.assertFalse(effect.is_alive)
        self.assertEqual(manager.effects, [])

    def test_night_lord_mark_and_delayed_detonation_lifecycle(self):
        mark = create_effect(
            "night_lord_taunt_contract",
            (320, 480),
            (80, 170),
        )
        self.assertIsInstance(mark, MarkDetonationEffect)
        self.assertFalse(mark.detonation)
        self.assertEqual(mark.style, "contract")

        talisman = create_effect(
            "night_lord_detonation_talisman",
            (320, 480),
            (80, 170),
        )
        self.assertEqual(talisman.style, "talisman")
        self.assertEqual(talisman.source, (320.0, 480.0))
        talisman.update(0.18)
        self.assertFalse(talisman.detonation_started)
        talisman.update(0.20)
        self.assertTrue(talisman.detonation_started)
        talisman.update(talisman.duration + 0.01)
        self.assertFalse(talisman.is_alive)

    def test_night_lord_mark_styles_draw_distinct_presentation_phases(self):
        image = QImage(800, 600, QImage.Format_ARGB32)
        image.fill(0)
        contract = create_effect("night_lord_taunt_contract", (220, 180), (400, 500))
        talisman = create_effect("night_lord_detonation_talisman", (580, 180), (400, 500))
        painter = QPainter(image)
        try:
            for progress in (0.08, 0.42, 0.86):
                contract.set_progress(progress)
                contract.draw(painter)
                talisman.set_progress(progress)
                talisman.draw(painter)
        finally:
            painter.end()
        self.assertFalse(painter.isActive())

    def test_night_lord_compositions_do_not_consume_global_rng(self):
        image = QImage(800, 600, QImage.Format_ARGB32)
        image.fill(0)
        effects = [
            create_effect("night_lord_four_flying", (400, 500), (220, 140)),
            create_effect("night_lord_fuma_shuriken", (400, 500), (220, 140)),
            create_effect("night_lord_dakrus_secret", (400, 500), (220, 140)),
            create_effect("night_lord_spread_throw", (400, 500), (220, 140)),
            create_effect("night_lord_detonation_talisman", (400, 500), (220, 140)),
        ]
        random.seed(7171)
        before = random.getstate()
        painter = QPainter(image)
        try:
            for effect in effects:
                effect.set_progress(0.8)
                effect.draw(painter)
        finally:
            painter.end()
        self.assertEqual(before, random.getstate())

    def test_night_lord_projectile_visual_roles_are_distinct(self):
        rapid = create_effect("night_lord_four_flying", (400, 500), (220, 140))
        fuma = create_effect("night_lord_fuma_shuriken", (400, 500), (220, 140))
        dakrus = create_effect("night_lord_dakrus_secret", (400, 500), (220, 140))
        spread = create_effect("night_lord_spread_throw", (400, 500), (220, 140))

        self.assertLess(rapid.duration, fuma.duration)
        self.assertEqual(rapid.wind_streaks, 0)
        self.assertEqual(fuma.wind_streaks, 1)
        self.assertEqual(fuma.style, "heavy_shuriken")
        self.assertGreater(fuma.size, rapid.size)
        self.assertGreater(fuma.spin_rate, rapid.spin_rate)
        self.assertEqual(dakrus.style, "secret_route")
        self.assertLess(dakrus.size, fuma.size)
        self.assertGreater(dakrus.trail_length, rapid.trail_length)
        self.assertEqual(spread.style, "fan_burst")
        self.assertEqual(spread.projectile_count, 5)
        self.assertLess(spread.size, fuma.size)
        self.assertLess(spread.trail_length, dakrus.trail_length)

    def test_night_lord_spread_impact_is_fan_cut_without_ring(self):
        app = QApplication.instance() or QApplication([])
        from tools.vfx_gallery import VFXGalleryWindow

        window = VFXGalleryWindow()
        window.play_preset("night_lord_spread_throw")
        effect = window.state.vfx_mgr.effects[0]
        window.state.update_presentation(effect.duration + 0.01)
        impacts = [
            item for item in window.state.vfx_mgr.effects
            if isinstance(item, ImpactEffect)
        ]
        self.assertEqual(len(impacts), 1)
        self.assertFalse(impacts[0].ring)
        self.assertFalse(impacts[0].burst)
        self.assertFalse(impacts[0].flash)
        self.assertEqual(impacts[0].style, "fan_cut")
        self.assertEqual(impacts[0].shard_count, 5)
        window.close()

    def test_night_lord_fuma_impact_is_cutting_without_ring(self):
        app = QApplication.instance() or QApplication([])
        from tools.vfx_gallery import VFXGalleryWindow

        window = VFXGalleryWindow()
        window.play_preset("night_lord_fuma_shuriken")
        effect = window.state.vfx_mgr.effects[0]
        window.state.update_presentation(effect.duration + 0.01)
        impacts = [
            item for item in window.state.vfx_mgr.effects
            if isinstance(item, ImpactEffect)
        ]
        self.assertEqual(len(impacts), 1)
        self.assertFalse(impacts[0].ring)
        self.assertFalse(impacts[0].burst)
        self.assertEqual(impacts[0].style, "angular_shard")
        self.assertEqual(impacts[0].shard_count, 7)
        window.close()

    def test_night_lord_dakrus_impact_is_cross_cut_without_ring(self):
        app = QApplication.instance() or QApplication([])
        from tools.vfx_gallery import VFXGalleryWindow

        window = VFXGalleryWindow()
        window.play_preset("night_lord_dakrus_secret")
        effect = window.state.vfx_mgr.effects[0]
        window.state.update_presentation(effect.duration + 0.11)
        impacts = [
            item for item in window.state.vfx_mgr.effects
            if isinstance(item, ImpactEffect)
        ]
        self.assertEqual(len(impacts), 1)
        self.assertFalse(impacts[0].ring)
        self.assertFalse(impacts[0].burst)
        self.assertFalse(impacts[0].flash)
        self.assertEqual(impacts[0].style, "cross_cut")
        window.close()

    def test_night_lord_projectile_primitives_draw_to_a_qimage(self):
        image = QImage(800, 600, QImage.Format_ARGB32)
        image.fill(0)
        effects = [
            create_effect("night_lord_four_flying", (400, 500), (220, 140)),
            create_effect("night_lord_fuma_shuriken", (400, 500), (220, 140)),
            create_effect("night_lord_dakrus_secret", (400, 500), (220, 140)),
        ]
        painter = QPainter(image)
        try:
            for effect in effects:
                effect.set_progress(0.55)
                effect.draw(painter)
        finally:
            painter.end()
        self.assertFalse(painter.isActive())

    def test_night_lord_projectile_compositions_clean_up_after_presentation(self):
        app = QApplication.instance() or QApplication([])
        from tools.vfx_gallery import VFXGalleryWindow

        window = VFXGalleryWindow()
        for preset in (
            "night_lord_four_flying",
            "night_lord_fuma_shuriken",
            "night_lord_dakrus_secret",
        ):
            window.play_preset(preset)
            longest = max(
                (effect.duration + effect.delay for effect in window.state.vfx_mgr.effects),
                default=0.0,
            )
            window.state.update_presentation(longest + 0.01)
            window.state.update_presentation(0.50)
            self.assertEqual(window.state.vfx_mgr.effects, [])
            self.assertEqual(window.state.pending_impacts, [])
        window.close()

    def test_area_effect_is_localized_and_expires(self):
        effect = AreaEffect((400, 160), width=180, height=64, lifetime=0.6)
        self.assertEqual(effect.layer, "ground")
        self.assertEqual(effect.center, (400.0, 160.0))
        effect.update(0.3)
        self.assertTrue(effect.is_alive)
        effect.update(0.3)
        self.assertFalse(effect.is_alive)

    def test_area_preset_uses_target_as_battlefield_center(self):
        effect = create_effect("bishop_holy_area", (400, 500), (400, 160))
        self.assertEqual(effect.center, (400.0, 160.0))

    def test_lightning_lifecycle_segment_count_and_branching(self):
        effect = LightningEffect(
            (100, 500), (680, 90), lifetime=0.3,
            segment_count=9, visual_jitter=24, branching=True,
        )
        self.assertEqual(effect.segment_count, 9)
        self.assertTrue(effect.branching)
        effect.update(0.3)
        self.assertFalse(effect.is_alive)

    def test_impact_effect_lifecycle(self):
        effect = ImpactEffect((400, 160), size=44, lifetime=0.25)
        self.assertTrue(effect.is_alive)
        effect.update(0.25)
        self.assertFalse(effect.is_alive)

    def test_delayed_effect_waits_then_expires(self):
        effect = ImpactEffect((400, 160), lifetime=0.3, delay=0.2)
        effect.update(0.1)
        self.assertTrue(effect.is_alive)
        self.assertFalse(effect.has_started)
        effect.update(0.1001)
        self.assertTrue(effect.has_started)
        self.assertLess(effect.progress, 0.001)
        effect.update(0.3)
        self.assertFalse(effect.is_alive)

    def test_persistent_presentation_can_be_cleared(self):
        manager = VisualEffectManager()
        aura = PersistentEffect((400, 420), style="aura", lifetime=8.0)
        sword = PersistentEffect((400, 420), style="sword", lifetime=8.0)
        manager.add_effect(aura)
        manager.add_effect(sword)
        manager.update(1.0)
        self.assertEqual({effect.layer for effect in manager.effects}, {"before_avatar", "after_avatar"})
        manager.clear()
        self.assertEqual(manager.effects, [])

    def test_cannonball_creates_presentation_impact_on_arrival(self):
        state = GalleryCombatState()
        cannonball = create_effect("cannonball_heavy", (400, 400), (400, 140))
        state.vfx_mgr.add_effect(cannonball)
        state.queue_impact(cannonball, size=50, color=(255, 155, 74), lifetime=0.38)
        state.update_presentation(cannonball.duration + 0.01)
        self.assertTrue(any(isinstance(effect, ImpactEffect) for effect in state.vfx_mgr.effects))

    def test_debug_anchor_overlay_is_hidden_by_default(self):
        app = QApplication.instance() or QApplication([])
        from ui_arena import CombatArenaWidget
        widget = CombatArenaWidget(GalleryCombatState())
        self.assertFalse(widget.show_debug_anchors)
        widget.set_debug_anchors(True)
        self.assertTrue(widget.show_debug_anchors)
        widget.close()

    def test_shared_manager_accepts_prototype_effects_and_cleans_them_up(self):
        manager = VisualEffectManager()
        effect = emit_vfx(manager, "hero_slash", (400, 500), (400, 120))
        self.assertIs(manager.effects[0], effect)
        manager.update(effect.duration + 0.01)
        self.assertEqual(manager.effects, [])

    def test_presentation_seed_does_not_consume_global_gameplay_rng(self):
        random.seed(9090)
        before = random.getstate()
        _ = LightningEffect((0, 0), (100, 100), seed=77)
        after = random.getstate()
        self.assertEqual(before, after)

    def test_all_primitives_draw_to_a_qimage(self):
        image = QImage(800, 600, QImage.Format_ARGB32)
        image.fill(0)
        effects = [
            SlashEffect((400, 500), (400, 120)),
            ProjectileEffect((400, 500), (250, 150), lifetime=1.0, trail=True),
            AreaEffect((400, 160)),
            LightningEffect((400, 500), (550, 120), branching=True),
            PersistentEffect((400, 420), style="aura"),
            PersistentEffect((460, 420), style="sword"),
            create_effect("hero_spatial_slash", (400, 500), (400, 120)),
            create_effect("hero_sacred_sword_descent", (400, 30), (400, 120)),
        ]
        painter = QPainter(image)
        try:
            for effect in effects:
                effect.set_progress(0.5)
                effect.draw(painter)
        finally:
            painter.end()
        self.assertFalse(painter.isActive())

    def test_gallery_state_is_not_a_formal_combat_manager(self):
        state = GalleryCombatState()
        self.assertIsInstance(state.vfx_mgr, VisualEffectManager)
        self.assertFalse(hasattr(state, "combat_stats"))
        self.assertEqual(len(state.player.team), 1)
        hp_before = state.player.team[0].current_hp
        state.update_presentation(0.2)
        self.assertEqual(state.player.team[0].current_hp, hp_before)

    def test_gallery_exposes_each_hero_skill_without_combat_manager(self):
        from tools.vfx_gallery import VFXGalleryWindow

        hero_presets = {
            "hero_rage_attack",
            "hero_sword_illusion",
            "hero_burning_soul_sword",
            "hero_spatial_slash",
            "hero_fighting_instinct",
            "hero_sacred_sword_descent",
        }
        listed = {preset for _label, preset in VFXGalleryWindow.PRESET_ORDER}
        self.assertTrue(hero_presets.issubset(listed))
        self.assertFalse(hasattr(VFXGalleryWindow, "combat_mgr"))

    def test_gallery_exposes_each_night_lord_skill_without_combat_manager(self):
        from tools.vfx_gallery import VFXGalleryWindow

        night_lord_presets = {
            "night_lord_four_flying",
            "night_lord_taunt_contract",
            "night_lord_fuma_shuriken",
            "night_lord_dakrus_secret",
            "night_lord_spread_throw",
            "night_lord_detonation_talisman",
        }
        listed = {preset for _label, preset in VFXGalleryWindow.PRESET_ORDER}
        self.assertTrue(night_lord_presets.issubset(listed))
        self.assertFalse(hasattr(VFXGalleryWindow, "combat_mgr"))

    def test_gallery_uses_chinese_display_names_for_review(self):
        from tools.vfx_gallery import VFXGalleryWindow

        labels = {preset: label for label, preset in VFXGalleryWindow.PRESET_ORDER}
        self.assertEqual(labels["hero_rage_attack"], "狂暴攻擊")
        self.assertEqual(labels["hero_sword_illusion"], "劍之幻象")
        self.assertEqual(labels["hero_burning_soul_sword"], "燃燒靈魂之劍")
        self.assertEqual(labels["hero_spatial_slash"], "空間斬")
        self.assertEqual(labels["hero_fighting_instinct"], "鬥氣本能")
        self.assertEqual(labels["hero_sacred_sword_descent"], "聖劍降臨")

        # Night Lord's canonical class registry exposes all six WIP skills.
        self.assertEqual(labels["night_lord_four_flying"], "四飛閃")
        self.assertEqual(labels["night_lord_taunt_contract"], "挑釁契約")
        self.assertEqual(labels["night_lord_fuma_shuriken"], "風魔手裏劍")
        self.assertEqual(labels["night_lord_dakrus_secret"], "達克魯的秘傳")
        self.assertEqual(labels["night_lord_spread_throw"], "散式投擲")
        self.assertEqual(labels["night_lord_detonation_talisman"], "飛閃起爆符")

    def test_gallery_hero_triggers_build_presentation_compositions(self):
        app = QApplication.instance() or QApplication([])
        from tools.vfx_gallery import VFXGalleryWindow

        window = VFXGalleryWindow()
        expected_counts = {
            "hero_rage_attack": 2,
            "hero_sword_illusion": 4,
            "hero_burning_soul_sword": 4,
            "hero_spatial_slash": 2,
            "hero_fighting_instinct": 2,
            "hero_sacred_sword_descent": 2,
        }
        for preset, expected_count in expected_counts.items():
            window.play_preset(preset)
            self.assertEqual(len(window.state.vfx_mgr.effects), expected_count)
            for effect in window.state.vfx_mgr.effects:
                self.assertFalse(any(hasattr(effect, name) for name in (
                    "damage", "cooldown", "hit_count", "buff", "resource", "progression"
                )))
        window.close()

    def test_gallery_night_lord_triggers_presentation_compositions(self):
        app = QApplication.instance() or QApplication([])
        from tools.vfx_gallery import VFXGalleryWindow

        window = VFXGalleryWindow()
        expected_counts = {
            "night_lord_four_flying": 4,
            "night_lord_taunt_contract": 1,
            "night_lord_fuma_shuriken": 1,
            "night_lord_dakrus_secret": 3,
            "night_lord_spread_throw": 1,
            "night_lord_detonation_talisman": 1,
        }
        for preset, expected_count in expected_counts.items():
            window.play_preset(preset)
            self.assertEqual(len(window.state.vfx_mgr.effects), expected_count)
            for effect in window.state.vfx_mgr.effects:
                self.assertFalse(any(hasattr(effect, name) for name in (
                    "damage", "cooldown", "hit_count", "buff", "resource", "progression"
                )))
        window.play_preset("night_lord_dakrus_secret")
        self.assertEqual(len(window.state.pending_impacts), 1)
        dakrus_effects = list(window.state.vfx_mgr.effects)
        self.assertEqual(len(dakrus_effects), 3)
        self.assertNotEqual(dakrus_effects[1].target, dakrus_effects[2].target)
        self.assertNotEqual(dakrus_effects[1].target, dakrus_effects[0].target)
        self.assertNotEqual(dakrus_effects[1].source, dakrus_effects[2].source)
        window.close()


if __name__ == "__main__":
    unittest.main()
