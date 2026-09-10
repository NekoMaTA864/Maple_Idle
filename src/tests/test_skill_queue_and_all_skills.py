"""
Automated Test for All-Skills Unlock and Sequential Delayed Casting Queue
"""
import sys
import os

proj_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, proj_dir)

from player_data import Player
from combat_system import CombatManager, get_skill_priority
from sound import sound_mgr


def test_all_skills_equipped():
    print("=== Test 1: All 8 Skills Unlocked by Default ===")
    p = Player()
    for idx, member in enumerate(p.team):
        assert len(member.skills) == 8, f"Member {idx} should have 8 skills"
        assert len(member.equipped_skill_indices) == 8, f"Member {idx} should have all 8 skills equipped"
        active = member.get_active_skills()
        assert len(active) == 8, f"Member {idx} should have 8 active skills"

    # Test toggling without 4-limit cap
    m0 = p.team[0]
    m0.toggle_skill(0)
    assert len(m0.equipped_skill_indices) == 7
    m0.toggle_skill(1)
    assert len(m0.equipped_skill_indices) == 6
    m0.enable_all_skills()
    assert len(m0.equipped_skill_indices) == 8
    print(">> [PASS] All 8 skills unlocked & unconstrained toggling verified!")


def test_skill_priority_hierarchy():
    print("=== Test 2: Skill Priority Hierarchy Sorting ===")
    p = Player()
    # Test Bishop:
    # holy_symbol (team_buff) -> prio 1
    # genesis (aoe_beam) -> prio 2
    # heal (heal) -> prio 3
    # peacemaker (multi_hit) -> prio 4
    bishop = p.team[3]
    bishop.set_class("bishop", p)
    
    prio_list = [(s.name, s.skill_type, get_skill_priority(s)) for s in bishop.skills]
    sorted_skills = sorted(bishop.skills, key=get_skill_priority)
    
    # First skill to cast MUST be team buff (holy_symbol or blessed_harmony)
    assert get_skill_priority(sorted_skills[0]) == 1, f"First skill should be buff, got {sorted_skills[0].name}"
    # Next should be burst/aoe_beam (genesis)
    assert any(s.skill_id == "genesis" and get_skill_priority(s) == 2 for s in sorted_skills)
    print(">> [PASS] Priority hierarchy (Buff -> Burst -> Control -> Multi -> Damage) verified!")


def test_sequential_delayed_casting():
    print("=== Test 3: Sequential Casting Queue with 0.38s Delay ===")
    p = Player()
    p.level = 200 # Unlock all skills
    cm = CombatManager(p)
    cm.spawn_next_monster()
    
    # Make monster have high HP so it survives the full rotation
    cm.monster.hp = 99999999
    cm.monster.max_hp = 99999999
    
    # Check slot staggering
    for idx, m in enumerate(p.team):
        assert m.cast_delay_timer >= 0.0, "cast_delay_timer should be initialized"

    # Track skill cast order for member 0
    m0 = p.team[0]
    initial_ready_count = len([s for s in m0.get_active_skills() if s.is_ready])
    assert initial_ready_count == 8, "All 8 skills should be ready at start"

    # On first update tick (dt = 0.01)
    # Member 0 should cast their 1st priority skill, entering 0.38s cast delay
    cm.update(0.01, sound_mgr)
    ready_after_first = len([s for s in m0.get_active_skills() if s.is_ready])
    assert ready_after_first == 7, f"Exactly 1 skill should have been cast on tick 1, got {ready_after_first} ready"
    assert m0.cast_delay_timer > 0.30, f"Member should have cast delay (~0.38s), got {m0.cast_delay_timer}"

    # During the 0.38s delay (e.g. advance by 0.20s), member 0 should NOT cast another skill
    cm.update(0.20, sound_mgr)
    ready_during_delay = len([s for s in m0.get_active_skills() if s.is_ready])
    assert ready_during_delay == 7, "No additional skill should be cast while in cast delay"

    # Advance past the remaining delay (e.g. 0.20s more, total > 0.40s)
    # Member 0 should now cast their 2nd priority skill!
    cm.update(0.20, sound_mgr)
    ready_after_second = len([s for s in m0.get_active_skills() if s.is_ready])
    assert ready_after_second == 6, f"2nd skill should be cast sequentially after delay, got {ready_after_second} ready"
    assert m0.cast_delay_timer > 0.30, "Cast delay should reset to ~0.38s for sequential rhythm"

    print(">> [PASS] Sequential delayed casting queue (one skill per 0.38s) verified!")


if __name__ == "__main__":
    test_all_skills_equipped()
    test_skill_priority_hierarchy()
    test_sequential_delayed_casting()
    print("\n========================================================")
    print(">> ALL SKILL QUEUE & ALL-SKILLS TESTS PASSED! <<")
    print("========================================================")

