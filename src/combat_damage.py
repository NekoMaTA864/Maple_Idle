"""
《新楓之谷：放置遠征隊》遠征隊員攻擊、傷害計算與護盾模組 (combat_damage.py)
"""
import random
from settings import COLOR_GOLD, COLOR_HEAL_GREEN, COLOR_SHIELD_BLUE, COLOR_TEXT_MAIN
from skills import is_skill_aoe
from monster import get_skill_priority
from combat_vfx_manager import PendingHit


def execute_pending_hit(combat_mgr, hit, sound_mgr):
    """執行多段延遲打擊結算"""
    """執行多段連擊中的後續打擊"""
    alive = [m for m in combat_mgr.monsters if m.is_alive]
    if not alive:
        return

    target_m = alive[0]
    m_idx = combat_mgr.monsters.index(target_m)
    dmg = hit.damage
    target_m.hp = max(0, target_m.hp - dmg)
    combat_mgr.combat_stats.record_damage(hit.member.slot_idx, dmg, hit.is_crit, skill_name=hit.skill_name)

    m_pos = combat_mgr._get_monster_pos(m_idx, len(combat_mgr.monsters))
    origin_pos = combat_mgr._get_slot_pos(hit.member.slot_idx)
    combat_mgr.vfx_mgr.add_vfx(
        hit.vfx_type, origin_pos[0], origin_pos[1], m_pos[0], m_pos[1], hit.vfx_color,
        source_slot=hit.member.slot_idx, target_monster_idx=m_idx
    )

    combat_mgr.shake_monster = 7.0 if hit.is_crit else 4.0
    combat_mgr.add_popup(f"暴擊! {dmg}" if hit.is_crit else f"-{dmg}", f"monster_{m_idx}", COLOR_GOLD if hit.is_crit else (255, 240, 180), is_crit=hit.is_crit)

    if hit.is_crit:
        sound_mgr.play("crit")
    else:
        sound_mgr.play("hit")

    if not any(m.is_alive for m in combat_mgr.monsters):
        combat_mgr._on_monster_killed(sound_mgr)



def apply_member_shield(combat_mgr, caster, target, skill):
    """為目標施加護盾"""
    """依施法者與目標屬性計算護盾，避免固定值無限堆疊。"""
    formula = getattr(skill, "shield_formula", None)
    if not formula:
        return max(0, int(getattr(skill, "shield_bonus", 0)))

    player = combat_mgr.player
    target_max_hp = target.get_max_hp(player)
    raw_shield = (
        target_max_hp * formula.get("target_hp_ratio", 0.0)
        + caster.get_max_hp(player) * formula.get("caster_hp_ratio", 0.0)
        + caster.get_attack(player) * formula.get("caster_attack_ratio", 0.0)
        + caster.get_defense(player) * formula.get("caster_defense_ratio", 0.0)
        + target.get_defense(player) * formula.get("target_defense_ratio", 0.0)
    )
    cap = target_max_hp * formula.get("cap_target_hp_ratio", 1.0)
    shield_value = max(1, int(min(raw_shield, cap)))
    old_shield = target.shield
    target.shield = max(old_shield, shield_value)
    return max(0, int(target.shield - old_shield))



def execute_member_attack(combat_mgr, member, sound_mgr, specific_skill=None, force_normal=False):
    """遠征隊員普通攻擊或技能攻擊傷害判定、增益、護盾與治療"""
    """遠征隊員施展普攻或新楓之谷特色招式 (支援全屏 AOE 掃蕩、指定技能佇列施放與多怪集火)"""
    p = combat_mgr.player
    alive_monsters = [m for m in combat_mgr.monsters if m.is_alive]
    if not alive_monsters:
        return

    # 決定使用的技能
    if force_normal:
        used_skill = None
    elif specific_skill is not None:
        used_skill = specific_skill
    else:
        ready_skills = [
            s for s in member.get_active_skills()
            if s.unlock_lvl <= p.level and s.is_ready
        ]
        if ready_skills:
            ready_skills.sort(key=get_skill_priority)
            used_skill = ready_skills[0]
        else:
            used_skill = None

    origin_pos = combat_mgr._get_slot_pos(member.slot_idx)
    sk_type = getattr(used_skill, "skill_type", "").lower() if used_skill else ""
    combat_mgr.combat_stats.record_attack(member.slot_idx, used_skill)

    # 特殊技能機制 1：主教群體治癒 (HEAL)
    if used_skill and sk_type in ["heal", "team_heal"]:
        alive_members = [tm for tm in p.team if tm.is_alive]
        if alive_members:
            is_team_heal = ("全體" in getattr(used_skill, "tag_name", "")) or ("全隊" in getattr(used_skill, "tag_name", "")) or sk_type == "team_heal" or "群體" in getattr(used_skill, "name", "")
            if is_team_heal:
                total_healed = 0
                for target in alive_members:
                    heal_amt = max(1, int(member.get_attack(p) * used_skill.dmg_mult + 15))
                    before_hp = target.current_hp
                    target.current_hp = min(target.get_max_hp(p), target.current_hp + heal_amt)
                    total_healed += int(target.current_hp - before_hp)
                    target_pos = combat_mgr._get_slot_pos(target.slot_idx)
                    combat_mgr.vfx_mgr.add_vfx("heal", target_pos[0], target_pos[1], color=COLOR_HEAL_GREEN)
                    combat_mgr.add_popup(f"+{heal_amt} HP", f"slot_{target.slot_idx}", COLOR_HEAL_GREEN, is_skill=True)
                combat_mgr.combat_stats.record_healing(member.slot_idx, total_healed, cast=True)
                combat_mgr.add_log(f"[{member.name}] 施展【{used_skill.name}】，為遠征隊全員恢復生命！", COLOR_HEAL_GREEN)
            else:
                target = min(alive_members, key=lambda tm: tm.current_hp / max(1, tm.get_max_hp(p)))
                heal_amt = int(member.get_attack(p) * used_skill.dmg_mult + 35)
                before_hp = target.current_hp
                target.current_hp = min(target.get_max_hp(p), target.current_hp + heal_amt)
                combat_mgr.combat_stats.record_healing(member.slot_idx, int(target.current_hp - before_hp), cast=True)
                target_pos = combat_mgr._get_slot_pos(target.slot_idx)
                combat_mgr.vfx_mgr.add_vfx("heal", target_pos[0], target_pos[1], color=COLOR_HEAL_GREEN)
                combat_mgr.add_popup(f"+{heal_amt} HP", f"slot_{target.slot_idx}", COLOR_HEAL_GREEN, is_skill=True)
                combat_mgr.add_log(f"[{member.name}] 施展【{used_skill.name}】，為 [{target.name}] 恢復 {heal_amt} 生命！", COLOR_HEAL_GREEN)
            used_skill.trigger()
            sound_mgr.play("hit")
            return

    # 特殊技能機制 2：全隊光環增益 (TEAM_BUFF) / 個人專屬增益 (SELF_BUFF)
    if used_skill and sk_type in ["team_buff", "buff"]:
        raw_b_type = getattr(used_skill, "buff_type", "attack_mult")
        buff_map = {
            "atk": "attack_mult", "attack": "attack_mult", "attack_mult": "attack_mult",
            "spd": "speed_bonus", "speed": "speed_bonus", "speed_bonus": "speed_bonus",
            "def": "defense_mult", "defense": "defense_mult", "defense_mult": "defense_mult",
            "crit": "crit_bonus", "crit_bonus": "crit_bonus", "union": "union"
        }
        buff_type = buff_map.get(raw_b_type, raw_b_type)
        buff_val = getattr(used_skill, "buff_val", 0.25)
        buff_duration_mult = 1.0 + getattr(p, "get_inner_ability_stat", lambda k: 0.0)("buff_duration")
        duration = getattr(used_skill, "buff_duration", 8.0) * buff_duration_mult
        p.apply_team_buff(used_skill.skill_id, buff_type, buff_val, duration, member.name, source_slot_idx=member.slot_idx)
        combat_mgr.combat_stats.record_buff(member.slot_idx)
        combat_mgr.vfx_mgr.add_vfx("holy", origin_pos[0], origin_pos[1], color=used_skill.color)
        combat_mgr.add_popup(f"[{used_skill.name}]", f"slot_{member.slot_idx}", used_skill.color, is_skill=True)
        combat_mgr.add_log(f"[{member.name}] 吟唱【{used_skill.name}】！全隊獲得【{used_skill.tag_name}】戰力大增！", used_skill.color)
        cd_skip = getattr(p, "get_inner_ability_stat", lambda k: 0.0)("cooldown_skip")
        if cd_skip > 0 and random.random() < cd_skip:
            combat_mgr.add_popup("[無冷!]", f"slot_{member.slot_idx}", (255, 215, 0), is_skill=True)
        else:
            used_skill.trigger()
        sound_mgr.play("levelup")
    elif used_skill and sk_type in ["self_buff"]:
        buff_duration_mult = 1.0 + getattr(p, "get_inner_ability_stat", lambda k: 0.0)("buff_duration")
        duration = getattr(used_skill, "buff_duration", 8.5) * buff_duration_mult
        member.is_buffed = True
        member.buff_timer = duration
        combat_mgr.vfx_mgr.add_vfx("holy", origin_pos[0], origin_pos[1], color=used_skill.color)
        combat_mgr.add_popup(f"[{used_skill.name}]", f"slot_{member.slot_idx}", used_skill.color, is_skill=True)
        combat_mgr.add_log(f"[{member.name}] 施展【{used_skill.name}】！獲得個人專屬強化！", used_skill.color)
        cd_skip = getattr(p, "get_inner_ability_stat", lambda k: 0.0)("cooldown_skip")
        if cd_skip > 0 and random.random() < cd_skip:
            combat_mgr.add_popup("[無冷!]", f"slot_{member.slot_idx}", (255, 215, 0), is_skill=True)
        else:
            used_skill.trigger()
        sound_mgr.play("levelup")

    # 判定是否為 AOE 全屏/群體橫掃技能
    is_aoe = is_skill_aoe(used_skill)

    # 特殊技能機制 3：極寒凍結控制 (FREEZE)
    if used_skill and sk_type == "freeze":
        freeze_dur = getattr(used_skill, "buff_duration", 0.0) or 2.2
        freeze_targets = alive_monsters if is_aoe else [alive_monsters[0]]
        for m in freeze_targets:
            m.freeze_timer = freeze_dur
            m_idx = combat_mgr.monsters.index(m)
            combat_mgr.combat_stats.record_control(member.slot_idx)
            m_pos = combat_mgr._get_monster_pos(m_idx, len(combat_mgr.monsters))
            combat_mgr.vfx_mgr.add_vfx("ice", origin_pos[0], origin_pos[1], m_pos[0], m_pos[1], (140, 230, 255),
                                 source_slot=member.slot_idx, target_monster_idx=m_idx)
            combat_mgr.add_popup(f"[極寒凍結 {freeze_dur:.1f}s]", f"monster_{m_idx}", (140, 230, 255), is_skill=True)
        combat_mgr.add_log(f"[{member.name}] 施展【{used_skill.name}】！{'全體' if is_aoe else ''}怪物行動被極寒徹底凍結！", (140, 230, 255))

    # 特殊技能機制 4：能量爆發 (BURST)
    burst_mult = 1.0
    if used_skill and sk_type in ["burst", "stack_burst"]:
        burst_mult = 1.0 + (member.mechanic_stacks * 0.35)
        member.mechanic_stacks = 0
        primary_m_idx = combat_mgr.monsters.index(alive_monsters[0])
        m_pos = combat_mgr._get_monster_pos(primary_m_idx, len(combat_mgr.monsters))
        combat_mgr.vfx_mgr.add_vfx("explosion", origin_pos[0], origin_pos[1], m_pos[0], m_pos[1], used_skill.color,
                             source_slot=member.slot_idx, target_monster_idx=primary_m_idx)
    else:
        member.mechanic_stacks = min(5, member.mechanic_stacks + 1)

    # 護盾技能判定：依技能公式計算，保留舊 shield_bonus 作為無公式 fallback。
    if used_skill and getattr(used_skill, "shield_bonus", 0) > 0:
        is_team_sh = getattr(used_skill, "is_team_shield", False) or ("全隊" in getattr(used_skill, "tag_name", "")) or (sk_type in ["team_shield", "party_shield"])
        if is_team_sh:
            for tm in p.team:
                if tm.is_alive:
                    shield_gain = combat_mgr._apply_member_shield(member, tm, used_skill)
                    if shield_gain > 0:
                        combat_mgr.combat_stats.record_shield(member.slot_idx, shield_gain)
                        combat_mgr.add_popup(f"[護盾 +{shield_gain}]", f"slot_{tm.slot_idx}", COLOR_SHIELD_BLUE, is_skill=True)
        else:
            shield_gain = combat_mgr._apply_member_shield(member, member, used_skill)
            if shield_gain > 0:
                combat_mgr.combat_stats.record_shield(member.slot_idx, shield_gain)
                combat_mgr.add_popup(f"[護盾 +{shield_gain}]", f"slot_{member.slot_idx}", COLOR_SHIELD_BLUE, is_skill=True)

    # 決定視覺特效類型
    eff_kind = getattr(used_skill, "effect_name", "")
    if not eff_kind:
        branch = member.branch
        if branch == "弓箭手":
            eff_kind = "arrow"
        elif branch == "盜賊":
            eff_kind = "star"
        elif branch == "法師":
            eff_kind = "holy"
        else:
            eff_kind = "slash"

    vfx_color = used_skill.color if used_skill else (255, 235, 160)
    hit_count = max(1, getattr(used_skill, "hit_count", 1) if used_skill else 1)
    m_atk = member.get_attack(p)
    skill_mult = (used_skill.dmg_mult if used_skill else 1.0) * burst_mult

    # 受擊目標列表：若為 AOE 技能則全體打擊，否則集火第一隻存活怪物
    target_monsters = alive_monsters if is_aoe else [alive_monsters[0]]
    total_dmg_dealt = 0
    any_crit = False

    for target_m in target_monsters:
        if not target_m.is_alive:
            continue
        # 無視防禦力 (Def Ignore，含角色裝備、套裝、內潛與萌獸無視防禦)
        gear_ign = (
            p.get_gear_stat_sum("def_ignore")
            + p.get_set_stat_sum("def_ignore")
            + getattr(p, "get_inner_ability_stat", lambda k: 0.0)("def_ignore")
            + getattr(p, "get_familiar_stat", lambda k: 0.0)("def_ignore")
        )
        skill_ign = getattr(used_skill, "ignore_defense_pct", 0.0) if used_skill else 0.0
        total_ign = min(0.95, gear_ign + skill_ign)
        # 新楓之谷正統防禦率機制 (Official Defense Rate Formula):
        # 傷害減免率 = 怪物防禦率 * (1.0 - 總無視防禦率)
        # 實質傷害係數 = max(0.05, 1.0 - 傷害減免率)
        # 當打 300% 防禦率頂級王時，若無視防禦不足將造成高額減傷 (保底 5% 刮痧)，無視堆高後恢復完整輸出
        m_def_rate = getattr(target_m, "defense_rate", None)
        if m_def_rate is None:
            # 兼容舊物件：若無 defense_rate 屬性則將整數轉換 (100以上視為百分比，否則推估)
            raw_d = getattr(target_m, "defense", 0)
            m_def_rate = raw_d / 100.0 if raw_d >= 5 else 0.20
        eff_def_reduction = m_def_rate * (1.0 - total_ign)
        def_multiplier = max(0.05, 1.0 - eff_def_reduction)
        raw_total_dmg = max(1.0, (m_atk * skill_mult) * def_multiplier)

        # 萌獸獨立終傷乘區 (TMS 原汁原味雙終/三終獨立相乘)
        raw_total_dmg *= getattr(p, "get_familiar_final_damage_mult", lambda: 1.0)()

        # 對處於異常狀態敵人增傷 (內在能力 damage_abnormal)
        if (getattr(target_m, "bleed_timer", 0) > 0 or getattr(target_m, "burn_timer", 0) > 0 or getattr(target_m, "freeze_timer", 0) > 0):
            abn_bonus = getattr(p, "get_inner_ability_stat", lambda k: 0.0)("damage_abnormal")
            if abn_bonus > 0:
                raw_total_dmg *= (1.0 + abn_bonus)

        # 斬殺 / 低血量額外增傷 (Execute Bonus)
        exec_b = getattr(used_skill, "execute_bonus", 0.0) if used_skill else 0.0
        if exec_b <= 0.0 and used_skill:
            desc_t = getattr(used_skill, "desc", "")
            tag_t = getattr(used_skill, "tag_name", "")
            if "斬殺" in tag_t or "斬殺" in desc_t or "低血量" in desc_t:
                exec_b = 0.40 if "低血量" in desc_t else 0.50
        if exec_b > 0.0 and (target_m.hp / max(1, target_m.max_hp) <= 0.35):
            raw_total_dmg *= (1.0 + exec_b)

        # 首領增傷 (Boss Damage，含裝備、套裝、內潛與萌獸)
        if getattr(target_m, "is_boss", False):
            b_dmg_mult = (
                p.get_gear_stat_sum("boss_dmg")
                + p.get_set_stat_sum("boss_dmg")
                + getattr(p, "get_inner_ability_stat", lambda k: 0.0)("boss_damage")
                + getattr(p, "get_familiar_stat", lambda k: 0.0)("boss_damage")
            )
            raw_total_dmg *= (1.0 + b_dmg_mult)

        total_dmg = int(raw_total_dmg * random.uniform(0.92, 1.08))

        # 暴擊判定 (含手套與套裝暴擊傷害、萌獸爆傷，以及技能必定暴擊 guaranteed_crit)
        has_guaranteed_crit = getattr(used_skill, "guaranteed_crit", False) if used_skill else False
        is_crit = has_guaranteed_crit or (random.random() < member.get_crit_chance(p))
        if is_crit:
            crit_dmg_bonus = (
                p.get_gear_stat_sum("crit_dmg")
                + p.get_set_stat_sum("crit_dmg")
                + getattr(p, "get_familiar_stat", lambda k: 0.0)("crit_damage")
            )
            total_dmg = int(total_dmg * (1.85 + crit_dmg_bonus))
            any_crit = True

        # ARC / AUT 增傷與壓制計算
        zone = combat_mgr.get_current_zone()
        arc_req = zone.get("arc_req", 0)
        aut_req = zone.get("aut_req", 0)
        if arc_req > 0:
            player_arc = p.get_total_arc()
            ratio = player_arc / max(1, arc_req)
            if ratio >= 1.5:
                total_dmg = int(total_dmg * 1.5)
            elif ratio >= 1.0:
                total_dmg = int(total_dmg * (1.0 + (ratio - 1.0) * 0.4))
            else:
                total_dmg = max(1, int(total_dmg * max(0.10, ratio)))
        elif aut_req > 0:
            player_aut = p.get_total_aut()
            ratio = player_aut / max(1, aut_req)
            if ratio < 1.0:
                total_dmg = max(1, int(total_dmg * max(0.05, ratio * 0.8)))

        # 多段連擊分段處理
        # 注意：total_dmg 在 ARC/AUT 嚴重壓制下可能被壓到極低(例如 AUT 未達標時
        # 只剩 5%)，若 total_dmg 小於 hit_count，first_dmg 可能算出 <= 0，
        # 對王造成 0 傷害甚至反向回血，故 first_dmg 也必須夾在 >= 1。
        single_dmg = max(1, total_dmg // hit_count)
        first_dmg = max(1, total_dmg - single_dmg * (hit_count - 1))

        target_m.hp = max(0, target_m.hp - first_dmg)
        combat_mgr.combat_stats.record_damage(
            member.slot_idx, first_dmg, is_crit,
            skill_name=used_skill.name if used_skill else "普攻"
        )
        total_dmg_dealt += total_dmg

        # 怪物異常狀態 DoT 連接 (中毒/流血/灼燒)
        if used_skill:
            d_type = getattr(used_skill, "dot_type", None)
            tag_n = getattr(used_skill, "tag_name", "")
            desc_t = getattr(used_skill, "desc", "")
            if d_type in ["bleed", "poison"] or any(k in tag_n or k in desc_t for k in ["中毒", "流血", "腐蝕"]):
                target_m.bleed_timer = getattr(used_skill, "buff_duration", 4.0) or 4.0
                target_m.bleed_dmg = max(1, int(m_atk * 0.15))
            if d_type == "burn" or any(k in tag_n or k in desc_t for k in ["灼燒", "高熱", "焚燒"]):
                target_m.burn_timer = getattr(used_skill, "buff_duration", 4.0) or 4.0
                target_m.burn_dmg = max(1, int(m_atk * 0.15))

        m_idx = combat_mgr.monsters.index(target_m)
        m_pos = combat_mgr._get_monster_pos(m_idx, len(combat_mgr.monsters))
        combat_mgr.vfx_mgr.add_vfx(
            eff_kind, origin_pos[0], origin_pos[1], m_pos[0], m_pos[1], vfx_color,
            source_slot=member.slot_idx, target_monster_idx=m_idx
        )
        combat_mgr.add_popup(f"暴擊! {first_dmg}" if is_crit else f"-{first_dmg}", f"monster_{m_idx}", COLOR_GOLD if is_crit else (255, 240, 180), is_crit=is_crit)

        # 後續連擊段數注入隊列
        if hit_count > 1 and target_m.hp > 0:
            for h in range(1, hit_count):
                combat_mgr.pending_hits.append(PendingHit(
                    delay=0.08 * h,
                    member=member,
                    target_name=f"monster_{m_idx}",
                    skill_name=used_skill.name if used_skill else "普攻",
                    damage=single_dmg,
                    is_crit=is_crit,
                    vfx_type=eff_kind,
                    vfx_color=vfx_color,
                    target_monster_idx=m_idx
                ))

    combat_mgr.shake_monster = 8.0 if any_crit else 4.0

    if used_skill:
        cd_skip = getattr(p, "get_inner_ability_stat", lambda k: 0.0)("cooldown_skip")
        if cd_skip > 0 and random.random() < cd_skip:
            combat_mgr.add_popup("[無冷!]", f"slot_{member.slot_idx}", (255, 215, 0), is_skill=True)
        else:
            used_skill.trigger()
        combat_mgr.add_popup(f"[{used_skill.name}]", f"slot_{member.slot_idx}", used_skill.color, is_skill=True)
        aoe_tag = "【全屏橫掃】" if is_aoe else ""
        combat_mgr.add_log(f"[{member.name}] 施放【{used_skill.name}】{aoe_tag}！造成合計 {total_dmg_dealt} 點{'暴擊' if any_crit else ''}傷害！({hit_count}段)", used_skill.color)
    else:
        combat_mgr.add_log(f"[{member.name}] 普攻命中，造成 {total_dmg_dealt} 點{'暴擊' if any_crit else ''}傷害。", COLOR_GOLD if any_crit else COLOR_TEXT_MAIN)

    if any_crit:
        sound_mgr.play("crit")
    else:
        sound_mgr.play("hit")

    # 吸血判定
    lifesteal = p.life_steal + (used_skill.lifesteal_bonus if used_skill else 0.0)
    if lifesteal > 0 and total_dmg_dealt > 0:
        healed = int(total_dmg_dealt * lifesteal)
        if healed > 0:
            member.current_hp = min(member.get_max_hp(p), member.current_hp + healed)
            combat_mgr.combat_stats.record_healing(member.slot_idx, healed)
            combat_mgr.add_popup(f"+{healed} HP", f"slot_{member.slot_idx}", COLOR_HEAL_GREEN)

    if not any(m.is_alive for m in combat_mgr.monsters):
        combat_mgr._on_monster_killed(sound_mgr)

