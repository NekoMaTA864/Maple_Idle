"""職業與技能快速建構輔助 (helpers.py)"""
from skills import Skill

def _s(id, name, cd, dmg=1.0, hc=1, st="damage", bt=None, bv=0.0, bd=0.0, ls=0.0, sh=0, lvl=1, ico="[技]", clr=(255, 215, 60), eff="slash", tag="[輸出]", desc="", aoe=False, team_sh=False, dot=None, exec_b=0.0, gc=False, ign_def=0.0):
    return Skill(id, name, cd, dmg_mult=dmg, hit_count=hc, skill_type=st, buff_type=bt, buff_val=bv, buff_duration=bd, lifesteal_bonus=ls, shield_bonus=sh, unlock_lvl=lvl, icon=ico, color=clr, effect_name=eff, tag_name=tag, desc=desc, is_aoe=aoe, is_team_shield=team_sh, dot_type=dot, execute_bonus=exec_b, guaranteed_crit=gc, ignore_defense_pct=ign_def)

def _c(cid, name, faction, branch, mech, desc, spd, hp, df, atk, crit, tank, skills):
    return {
        "id": cid, "name": name, "faction": faction, "branch": branch, "mechanic_name": mech,
        "desc": desc, "base_speed": spd, "hp_mult": hp, "def_mult": df, "atk_mult": atk,
        "crit_bonus": crit, "is_tank": tank, "skills": skills
    }
