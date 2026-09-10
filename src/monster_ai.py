"""
《新楓之谷：放置遠征隊》怪物行為與技能施放模組 (monster_ai.py)
"""
import random
from settings import COLOR_HP_RED, COLOR_SHIELD_BLUE


def process_monster_attack(combat_mgr, m, sound_mgr):
    """怪物普通攻擊或技能判定"""
    """怪物個體或首領攻擊遠征隊成員 (多怪波次平滑傷害平衡，防秒殺)"""
    alive_members = [tm for tm in combat_mgr.player.team if tm.is_alive]

    if not alive_members:
        combat_mgr.is_resting = True
        combat_mgr.respawn_timer = 3.2
        combat_mgr.add_log(f"警告：遠征隊全員於第 {combat_mgr.current_floor}/10 層陣亡！緊急撤回重整 (3秒)...", (255, 80, 80))
        return

    # 優先判定首領專屬技能
    ready_skill = None
    for s in getattr(m, "skills", []):
        if s.is_ready:
            ready_skill = s
            break

    if ready_skill:
        ready_skill.trigger()
        combat_mgr._execute_monster_skill(ready_skill, alive_members, sound_mgr, boss_monster=m)
        return

    # 常規普攻：唯一鎖定核心主角血防進行攻擊與結算
    target = combat_mgr.player.team[0]
    m_atk = m.atk

    # ARC 1.5倍完全防禦壓制 (Official MapleStory Mechanic: 當 ARC >= 1.5倍時怪物傷害強制為 1 點!)
    zone = combat_mgr.get_current_zone()
    arc_req = zone.get("arc_req", 0)
    player_arc = combat_mgr.player.get_total_arc()
    if arc_req > 0 and player_arc >= int(arc_req * 1.5):
        dmg = 1
    else:
        raw_dmg = max(1.0, m_atk - target.get_defense(combat_mgr.player) * 0.48)
        # 多怪物波次攻擊力平衡因子：避免多隻怪同時秒殺主角
        alive_count = len([x for x in combat_mgr.monsters if x.is_alive])
        count_factor = 1.0 if alive_count <= 1 else max(0.48, 1.0 / (alive_count ** 0.5))
        dmg = max(1, int(raw_dmg * count_factor * random.uniform(0.9, 1.1)))

    hp_lost, absorbed = target.take_damage(dmg)
    combat_mgr.combat_stats.record_damage_taken(0, hp_lost, absorbed)
    sound_mgr.play("hit")
    if len(combat_mgr.shake_team) > 0:
        combat_mgr.shake_team[0] = 7.0

    m_idx = combat_mgr.monsters.index(m) if m in combat_mgr.monsters else 0
    m_pos = combat_mgr._get_monster_pos(m_idx, len(combat_mgr.monsters))
    t_pos = combat_mgr._get_slot_pos(0)
    combat_mgr.vfx_mgr.add_vfx("slash", m_pos[0], m_pos[1], t_pos[0], t_pos[1], COLOR_HP_RED,
                         source_slot=m_idx, target_slot=0)

    if absorbed > 0:
        combat_mgr.add_popup(f"[護盾抵扣 {int(absorbed)}]", "slot_0", COLOR_SHIELD_BLUE)
    if hp_lost > 0:
        combat_mgr.add_popup(f"-{int(hp_lost)}", "slot_0", COLOR_HP_RED)

    combat_mgr.add_log(f"[{m.name}] 狂暴襲擊核心主角 [{target.name}]！造成 {dmg} 點傷害。", COLOR_HP_RED)

    if target.current_hp <= 0:
        combat_mgr.combat_stats.record_death(0)
        combat_mgr.is_resting = True
        combat_mgr.respawn_timer = 3.2
        combat_mgr.add_log(f"警告：核心主角 [{target.name}] 戰敗倒下！遠征隊全體重創撤退 (3秒)...", (255, 80, 80))


def execute_monster_skill(combat_mgr, skill, alive_members, sound_mgr, boss_monster=None):
    """怪物施放專屬技能 (受擊與傷害計算全額聚焦於核心主角)"""
    m = boss_monster if boss_monster is not None else combat_mgr.monster
    m_idx = combat_mgr.monsters.index(m) if (m and m in combat_mgr.monsters) else 0
    m_pos = combat_mgr._get_monster_pos(m_idx, len(combat_mgr.monsters))
    vfx_col = getattr(skill, "vfx_color", getattr(skill, "color", (255, 60, 60)))
    vfx_kind = getattr(skill, "vfx_kind", getattr(skill, "effect_name", "slash"))
    cast_desc = getattr(skill, "cast_desc", getattr(skill, "desc", ""))

    combat_mgr.add_popup(f"【{skill.name}】", f"monster_{m_idx}", vfx_col, is_skill=True)
    combat_mgr.add_log(f"⚡ 首領 [{m.name}] 施展【{skill.name}】！{cast_desc}", vfx_col)
    sound_mgr.play("crit")

    target_type = getattr(skill, "target_type", "damage")
    if target_type == "self_shield":
        sh_val = getattr(skill, "shield_val", 500)
        m.shield += sh_val
        combat_mgr.add_popup(f"[暗影護盾 +{sh_val}]", f"monster_{m_idx}", COLOR_SHIELD_BLUE, is_skill=True)
        combat_mgr.vfx_mgr.add_vfx(vfx_kind, m_pos[0], m_pos[1], color=vfx_col,
                             source_slot=m_idx, target_monster_idx=m_idx)
        return

    if target_type == "curse_all":
        debuff_dur = getattr(skill, "debuff_duration", 5.0)
        combat_mgr.player.apply_team_buff("boss_curse", "atk", -0.25, debuff_dur, f"{m.name}詛咒")
        combat_mgr.add_popup("[虛弱 -25%]", "slot_0", (180, 80, 255), is_skill=True)
        combat_mgr.vfx_mgr.add_vfx(vfx_kind, m_pos[0], m_pos[1], color=vfx_col,
                             source_slot=m_idx)
        return

    # 全面鎖定核心主角 (席位 0) 計算血防與受傷
    target = combat_mgr.player.team[0]
    zone = combat_mgr.get_current_zone()
    arc_req = zone.get("arc_req", 0)
    player_arc = combat_mgr.player.get_total_arc()
    is_arc_15x = (arc_req > 0 and player_arc >= int(arc_req * 1.5))

    if is_arc_15x:
        dmg = 1
    else:
        target_def = target.get_defense(combat_mgr.player)
        def_reduction = min(0.50, target_def / (target_def + m.atk * 0.85 + 10))
        raw_dmg = (m.atk * skill.dmg_mult) * (1.0 - def_reduction)
        dmg = max(1, int(raw_dmg * random.uniform(0.92, 1.08)))

    hp_lost, absorbed = target.take_damage(dmg)
    combat_mgr.combat_stats.record_damage_taken(0, hp_lost, absorbed)

    # 震動與全場特效
    is_aoe = (target_type == "aoe_all" or getattr(skill, "is_aoe", False))
    if is_aoe:
        combat_mgr.shake_monster = 10.0
        for idx in range(len(combat_mgr.shake_team)):
            combat_mgr.shake_team[idx] = 9.0
        # 全屏 AOE 特效波及全場
        for m_slot in range(len(combat_mgr.player.team)):
            t_pos = combat_mgr._get_slot_pos(m_slot)
            combat_mgr.vfx_mgr.add_vfx(vfx_kind, m_pos[0], m_pos[1], t_pos[0], t_pos[1], vfx_col,
                                 source_slot=m_idx, target_slot=m_slot)
    else:
        if len(combat_mgr.shake_team) > 0:
            combat_mgr.shake_team[0] = 8.0
        t_pos = combat_mgr._get_slot_pos(0)
        combat_mgr.vfx_mgr.add_vfx(vfx_kind, m_pos[0], m_pos[1], t_pos[0], t_pos[1], vfx_col,
                             source_slot=m_idx, target_slot=0)

    if absorbed > 0:
        combat_mgr.add_popup(f"[護盾抵扣 {int(absorbed)}]", "slot_0", COLOR_SHIELD_BLUE)
    if hp_lost > 0:
        combat_mgr.add_popup(f"-{int(hp_lost)}", "slot_0", vfx_col)

    if target.current_hp <= 0:
        combat_mgr.combat_stats.record_death(0)
        combat_mgr.is_resting = True
        combat_mgr.respawn_timer = 3.2
        combat_mgr.add_log(f"警告：核心主角 [{target.name}] 遭首領絕技重創倒下！全員重創撤退 (3秒)...", (255, 80, 80))
