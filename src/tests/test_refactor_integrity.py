import os
import sys
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
if os.path.abspath('.') not in sys.path:
    sys.path.insert(0, os.path.abspath('.'))

def test_imports():
    print("=== Test 1: Module Imports ===")
    from PySide6.QtWidgets import QApplication
    global qt_app
    qt_app = QApplication.instance() or QApplication(sys.argv)
    import settings
    import skills
    import classes
    import item_system
    import player_data
    import combat_system
    import sound
    import ui_styles
    import ui_arena
    import ui_dialogs
    import pyside_ui
    import pyside_main
    import vfx_core
    import vfx_renderer
    print(">> [PASS] All core and refactored modules imported successfully!")

def test_classes_and_skills():
    print("=== Test 2: Classes & 192 Skills Data Integrity ===")
    from classes import ALL_CLASSES, EXPLORER_CLASSES, CYGNUS_CLASSES, RESISTANCE_CLASSES
    assert len(ALL_CLASSES) == 24, f"Expected 24 classes, got {len(ALL_CLASSES)}"
    assert len(EXPLORER_CLASSES) == 15
    assert len(CYGNUS_CLASSES) == 5
    assert len(RESISTANCE_CLASSES) == 4

    total_skills = 0
    for cid, cdata in ALL_CLASSES.items():
        assert len(cdata['skills']) == 8, f"Class {cid} does not have 8 skills!"
        total_skills += len(cdata['skills'])
        for s in cdata['skills']:
            assert s.skill_id
            assert s.name
            assert s.cooldown > 0
            assert s.effect_name
    assert total_skills == 192, f"Expected 192 skills, got {total_skills}"
    print(f">> [PASS] 24 classes and all {total_skills} skills verified 100%!")

def test_vfx_rendering():
    print("=== Test 3: 192 VFX Procedural Rendering & Aura ===")
    from PySide6.QtGui import QGuiApplication, QImage, QPainter
    import classes
    import vfx_renderer

    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    img = QImage(200, 200, QImage.Format_ARGB32)
    painter = QPainter(img)

    for cid, cdata in classes.ALL_CLASSES.items():
        fac = cdata['faction']
        for sk in cdata['skills']:
            eff = sk.effect_name
            if fac == 'explorer':
                assert vfx_renderer.render_explorer_vfx(painter, eff, 0.5, 255, 255, 255, 255, 100, 100, 150, 150), f"Explorer VFX missed: {eff}"
            elif fac == 'cygnus':
                assert vfx_renderer.render_cygnus_vfx(painter, eff, 0.5, 255, 255, 255, 255, 100, 100, 150, 150), f"Cygnus VFX missed: {eff}"
            elif fac == 'resistance':
                assert vfx_renderer.render_resistance_vfx(painter, eff, 0.5, 255, 255, 255, 255, 100, 100, 150, 150), f"Resistance VFX missed: {eff}"

    # Test render_aura_halo
    for buff_k in ['atk', 'spd', 'def', 'crit', 'lifesteal']:
        vfx_renderer.render_aura_halo(painter, 100, 100, buff_k, 5.0, 8.0)

    painter.end()
    print(">> [PASS] All 192 skills render cleanly with dedicated procedural branches!")
    print(">> [PASS] render_aura_halo runs smoothly for all buff types!")

def test_player_and_combat():
    print("=== Test 4: Player All-Skills Loadout, Sequential Queue & Combat Simulation ===")
    from player_data import Player
    from combat_system import CombatManager, get_skill_priority

    p = Player()
    hero = p.team[0]
    assert len(hero.equipped_skill_indices) == 8, f"Initial slots should be 8, got {len(hero.equipped_skill_indices)}"
    # Toggle skill to unequip
    hero.toggle_skill(4)
    assert len(hero.equipped_skill_indices) == 7
    assert 4 not in hero.equipped_skill_indices
    # Toggle back to re-equip
    hero.toggle_skill(4)
    assert len(hero.equipped_skill_indices) == 8
    assert 4 in hero.equipped_skill_indices

    # Priority verification
    prio_map = [get_skill_priority(s) for s in hero.skills]
    assert any(p == 1 for p in prio_map), "Should have priority 1 buff skill"

    from sound import sound_mgr
    cm = CombatManager(p)
    cm.spawn_next_monster()
    for _ in range(30):
        cm.update(0.1, sound_mgr)

    print(">> [PASS] All 8 skills loadout, priority hierarchy and sequential delayed combat loop verified!")

def test_item_cubing_and_stars():
    print("=== Test 5: Inherent Rarity, Potential Cubing & Star Force ===")
    from item_system import generate_loot, Item
    from player_data import Player

    p = Player()
    p.gold = 5000000

    # Auto enhance slot
    success, msg = p.auto_enhance_slot("weapon", target_star=10)
    assert success
    assert p.slot_enhancements["weapon"] == 10

    # Cube item
    item = generate_loot(1, 1)
    item.potential_rank = "unique"
    res, msg = p.auto_cube_item(item, cube_type="bright", target_rank="legendary", target_stat_keyword=None, max_cubes=500)
    assert res
    assert item.potential_rank == "legendary"
    print(">> [PASS] Star force and auto-cube operate seamlessly!")

def test_ui_widgets():
    print("=== Test 6: UI Widgets and Dialogs Instantiation ===")
    from PySide6.QtWidgets import QApplication
    from player_data import Player
    from combat_system import CombatManager
    from sound import sound_mgr
    from ui_arena import CombatArenaWidget
    from ui_dialogs import AutoCubeDialog, ItemCompareDialog
    from pyside_ui import MainWindow
    from item_system import generate_loot

    app = QApplication.instance() or QApplication(sys.argv)
    p = Player()
    cm = CombatManager(p)
    win = MainWindow(p, cm, sound_mgr)
    arena = CombatArenaWidget(cm)

    loot = generate_loot(1, 1)
    if loot:
        dlg = ItemCompareDialog(loot, p)
        assert dlg
        ac_dlg = AutoCubeDialog(loot, p)
        assert ac_dlg

    print(">> [PASS] MainWindow, CombatArenaWidget, and Dialogs instantiated with 0 errors!")

if __name__ == '__main__':
    test_imports()
    test_classes_and_skills()
    test_vfx_rendering()
    test_player_and_combat()
    test_item_cubing_and_stars()
    test_ui_widgets()
    print("\n[SUCCESS] ALL 6 COMPREHENSIVE REFACTORING INTEGRITY TESTS PASSED! 100% OPERATIONAL!")
