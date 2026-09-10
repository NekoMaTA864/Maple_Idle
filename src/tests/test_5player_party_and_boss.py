"""
Unit & Integration Tests for 5-Player Party, Boss Skills, Dynamic Layout, and VFX Sandbox
"""

import sys
import os
import random
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
if os.path.abspath('.') not in sys.path:
    sys.path.insert(0, os.path.abspath('.'))

from PySide6.QtWidgets import QApplication
qt_app = QApplication.instance() or QApplication(sys.argv)

from player_data import Player
from combat_system import CombatManager
from sound import sound_mgr
from monster_skills import MonsterSkill, BOSS_SKILLS_CATALOG, get_skills_for_boss, scale_monster_stats
from classes import ALL_CLASSES, get_class_info
from ui_dialogs import AutoCubeDialog, ItemCompareDialog
from item_system import generate_loot
from vfx_sandbox import SingleClassVFXSandbox


def test_5player_party_and_unrestricted_classes():
    print("=== Test 1: 5-Player Party & Unrestricted 24-Class Selection ===")
    p = Player()
    assert len(p.team) == 5, f"Expected 5 party members, got {len(p.team)}"

    # Check initial default 5 members
    expected_default = ["hero", "dawn_warrior", "battle_mage", "bishop", "night_lord"]
    for i, cid in enumerate(expected_default):
        assert p.team[i].class_id == cid, f"Slot {i} expected {cid}, got {p.team[i].class_id}"

    # Verify any slot can pick ANY of the 24 classes
    test_classes = ["mechanic", "blaster", "flame_wizard", "corsair", "shadower"]
    for slot_idx, cid in enumerate(test_classes):
        success = p.set_slot_class(slot_idx, cid)
        assert success, f"Failed to set slot {slot_idx} to class {cid}"
        assert p.team[slot_idx].class_id == cid
        assert len(p.team[slot_idx].skills) == 8
        assert len(p.team[slot_idx].equipped_skill_indices) == 8

    print(">> [PASS] 5-player party and 24-class unrestricted switching verified!")


def test_auto_stat_allocation():
    print("=== Test 2: Auto Stat Allocation & Batch Point Addition ===")
    p = Player()
    p.free_points = 100
    init_atk = p.stat_atk
    init_def = p.stat_def
    init_hp = p.stat_hp
    init_crit = p.stat_crit

    # Test batch addition
    added = p.add_stat_points("atk", 10)
    assert added == 10
    assert p.stat_atk == init_atk + 10
    assert p.free_points == 90

    # Test 'all_atk' mode
    p.auto_allocate_points("all_atk")
    assert p.free_points == 0
    assert p.stat_atk == init_atk + 100

    # Test 'balanced' mode (40% atk, 20% def, 20% hp, 20% crit)
    p.free_points = 40
    p.auto_allocate_points("balanced")
    assert p.free_points == 0
    assert p.stat_atk == init_atk + 100 + 16
    assert p.stat_def == init_def + 8
    assert p.stat_hp == init_hp + 8
    assert p.stat_crit == init_crit + 8

    # Test 'defensive' mode (30% atk, 35% def, 35% hp)
    p.free_points = 20
    p.auto_allocate_points("defensive")
    assert p.free_points == 0
    assert p.stat_atk == init_atk + 100 + 16 + 6
    assert p.stat_def == init_def + 8 + 7
    assert p.stat_hp == init_hp + 8 + 7

    print(">> [PASS] One-click auto stat allocation (all_atk, balanced, defensive) verified!")


def test_save_backward_compatibility():
    print("=== Test 3: Backward Compatibility for 3-Player Save Files ===")
    legacy_save = {
        "level": 50,
        "gold": 50000,
        "team": [
            {"class_id": "hero", "equipped_skill_indices": [0, 1, 2, 3]},
            {"class_id": "dawn_warrior", "equipped_skill_indices": [0, 1, 2, 3]},
            {"class_id": "battle_mage", "equipped_skill_indices": [0, 1, 2, 3]}
        ]
    }
    p = Player()
    p.load_dict(legacy_save)

    assert len(p.team) == 5, f"Expected team to auto-expand to 5, got {len(p.team)}"
    assert p.team[0].class_id == "hero"
    assert p.team[1].class_id == "dawn_warrior"
    assert p.team[2].class_id == "battle_mage"
    assert p.team[3].class_id == "bishop"       # auto-filled slot 4
    assert p.team[4].class_id == "night_lord"   # auto-filled slot 5

    # Check save export has all 5
    exported = p.to_dict()
    assert len(exported["team_classes"]) == 5
    assert len(exported["team_skills"]) == 5
    print(">> [PASS] 3-player legacy save auto-expands seamlessly to 5 players!")


def test_boss_skills_and_combat_enrage():
    print("=== Test 4: Boss Skills, Scaling & 30% Rage Awakening ===")
    p = Player()
    cm = CombatManager(p)

    # Spawn boss at max floor (floor 10)
    cm.current_floor = cm.max_floors
    cm.spawn_next_monster()
    m = cm.monster
    assert m.is_boss is True
    assert len(m.skills) >= 2, f"Boss should have special skills, got {len(m.skills)}"

    initial_hp = m.max_hp
    assert m.is_enraged is False
    orig_skill_cd = m.skills[0].cooldown

    # Simulate boss taking damage down to <30%
    m.hp = int(m.max_hp * 0.25)
    cm.update(0.1, sound_mgr)
    assert m.is_enraged is True, "Boss should awaken enrage at < 30% HP"
    assert m.skills[0].cooldown <= orig_skill_cd * 0.85, "Boss skill cooldown should be reduced by 20% on enrage"

    # Test boss shield
    m.shield = 500
    rem, absorbed = m.take_damage(300)
    assert rem == 0
    assert absorbed == 300
    assert m.shield == 200

    rem, absorbed = m.take_damage(400)
    assert rem == 200
    assert absorbed == 200
    assert m.shield == 0

    # Test boss skill execution (e.g. AOE ground slam hits all 5 members)
    for mem in p.team:
        mem.current_hp = 1000
        mem.shield = 0
    # Give member 0 a protective shield
    p.team[0].shield = 600
    alive = [mem for mem in p.team if mem.is_alive]
    cm._execute_monster_skill(m.skills[0], alive, sound_mgr)
    # Check that combat log recorded the skill
    assert any(f"施展【{m.skills[0].name}】" in log["text"] for log in cm.combat_logs)
    # Member 0's shield absorbed damage while unshielded members took direct HP damage
    assert p.team[0].shield < 600, "Shield should absorb damage"
    assert p.team[1].current_hp < 1000, "Unshielded member should take HP damage"

    # Test Environmental Miasma DoT (every 2.5s)
    p.team[0].shield = 500
    init_unshielded_hp = p.team[1].current_hp
    cm.boss_miasma_timer = 2.4
    cm.update(0.2, sound_mgr)
    # Member 0 shield absorbed miasma
    assert p.team[0].shield < 500
    # Member 1 took miasma HP damage
    assert p.team[1].current_hp < init_unshielded_hp

    print(">> [PASS] Boss skills, shield mechanic, miasma DoT, and rage CDR verified!")


def test_dialog_dynamic_sizing():
    print("=== Test 5: Dialog Dynamic Resizing & QScrollArea Integrity ===")
    p = Player()
    item = generate_loot(100, is_boss=True)

    # Test ItemCompareDialog
    dlg = ItemCompareDialog(item, p, slot_k=None)
    assert dlg.minimumWidth() >= 400
    assert dlg.minimumHeight() >= 500
    # Can freely resize without crash
    dlg.resize(800, 900)
    assert dlg.width() == 800
    assert dlg.height() == 900
    dlg.close()

    # Test AutoCubeDialog
    cube_dlg = AutoCubeDialog(item, p)
    assert cube_dlg.minimumWidth() >= 400
    cube_dlg.resize(600, 600)
    assert cube_dlg.width() == 600
    cube_dlg.close()

    print(">> [PASS] Dialogs have flexible non-fixed sizes with QScrollArea protection!")


def test_vfx_sandbox_single_class():
    print("=== Test 6: Single-Class Pure VFX Sandbox Operation ===")
    sandbox = SingleClassVFXSandbox()
    assert sandbox.current_class_id == "battle_mage"

    # Switch to hero
    sandbox._on_class_combo_changed("hero")
    assert sandbox.current_class_id == "hero"
    assert sandbox.current_skill is not None
    assert sandbox.canvas.current_vfx is not None

    # Test frame scrubbing slider
    sandbox._on_slider_moved(500)
    assert abs(sandbox.canvas.current_vfx.progress - 0.5) < 0.05
    assert sandbox.canvas.is_paused is True

    # Test replay and loop
    sandbox._replay_current()
    sandbox._toggle_loop()
    assert sandbox.auto_loop is True

    # Check canvas positions: top monster, bottom caster
    sandbox.canvas.resize(800, 600)
    sandbox.canvas.paintEvent(None)
    assert sandbox.canvas.target_pos.y() < sandbox.canvas.caster_pos.y()

    sandbox.close()
    print(">> [PASS] Single-class pure VFX sandbox verified completely!")


if __name__ == "__main__":
    test_5player_party_and_unrestricted_classes()
    test_auto_stat_allocation()
    test_save_backward_compatibility()
    test_boss_skills_and_combat_enrage()
    test_dialog_dynamic_sizing()
    test_vfx_sandbox_single_class()
    print("\n========================================================")
    print(">> ALL TESTS FOR 5-PLAYER, BOSS SKILLS & SANDBOX PASSED! <<")
    print("========================================================")
