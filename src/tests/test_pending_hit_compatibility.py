"""Regression coverage for the PendingHit extraction boundary."""

import os
import sys
import unittest

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from combat_events import PendingHit
from combat_vfx_manager import PendingHit as VfxPendingHit


class TestPendingHitCompatibility(unittest.TestCase):
    def test_vfx_module_reexports_the_same_pending_hit_type(self):
        self.assertIs(PendingHit, VfxPendingHit)

    def test_pending_hit_preserves_legacy_constructor_and_fields(self):
        member = object()
        hit = PendingHit(
            0.08, member, "monster_2", "Skill", 123, True,
            "slash", (1, 2, 3), target_monster_idx=2,
        )

        self.assertEqual(hit.delay, 0.08)
        self.assertIs(hit.member, member)
        self.assertEqual(hit.target_name, "monster_2")
        self.assertEqual(hit.skill_name, "Skill")
        self.assertEqual(hit.damage, 123)
        self.assertTrue(hit.is_crit)
        self.assertEqual(hit.vfx_type, "slash")
        self.assertEqual(hit.vfx_color, (1, 2, 3))
        self.assertEqual(hit.target_monster_idx, 2)


if __name__ == "__main__":
    unittest.main()
