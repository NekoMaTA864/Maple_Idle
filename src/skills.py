"""
主動技能與戰技系統 (skills.py)
支援新楓之谷正統技能機制：多段連擊、全隊光環增益、急救治療、護盾壁壘、冰凍控場、疊層引爆
"""

class Skill:
    def __init__(
        self,
        skill_id,
        name,
        cooldown,
        dmg_mult=1.0,
        lifesteal_bonus=0.0,
        shield_bonus=0,
        unlock_lvl=1,
        icon="[技]",
        color=(255, 215, 60),
        desc="",
        skill_type="damage",     # damage, multi_hit, team_buff, heal, shield, freeze, stack_burst
        hit_count=1,             # 連擊段數 (如多段連擊為 4~6 段)
        buff_type=None,          # atk, crit, spd, lifesteal, defense
        buff_val=0.0,            # 增益數值 (例如 0.20 代表 +20%)
        buff_duration=0.0,       # 增益持續秒數
        effect_name="slash",     # slash, arrow_storm, holy_beam, fire_explosion, ice_freeze, heal_cross, shield_glow
        tag_name="[輸出]",        # [多段連擊], [全隊增益], [急救治療], [神聖天罰], [極凍控場], [護盾屏障], [疊層引爆]
        is_aoe=False,
        is_team_shield=False,
        dot_type=None,
        execute_bonus=0.0,
        shield_formula=None,
        guaranteed_crit=False,
        ignore_defense_pct=0.0
    ):
        self.skill_id = skill_id
        self.name = name
        self.cooldown = cooldown
        self.current_cd = 0.0
        self.dmg_mult = dmg_mult
        self.lifesteal_bonus = lifesteal_bonus
        self.shield_bonus = shield_bonus
        self.unlock_lvl = unlock_lvl
        self.icon = icon
        self.color = color
        self.desc = desc

        # 進階機制參數
        self.skill_type = skill_type
        self.hit_count = hit_count
        self.buff_type = buff_type
        self.buff_val = buff_val
        self.buff_duration = buff_duration
        self.effect_name = effect_name
        self.tag_name = tag_name
        self.is_team_shield = is_team_shield or ("全隊" in tag_name and shield_bonus > 0)
        self.shield_formula = shield_formula or self._default_shield_formula()
        self.dot_type = dot_type
        self.execute_bonus = execute_bonus
        self.guaranteed_crit = guaranteed_crit
        self.ignore_defense_pct = ignore_defense_pct
        self.is_aoe = is_aoe or (skill_type in ["aoe", "aoe_beam"])

    @property
    def id(self):
        return self.skill_id

    @property
    def timer(self):
        return self.current_cd

    @timer.setter
    def timer(self, value):
        self.current_cd = float(value)

    def _default_shield_formula(self):
        if self.shield_bonus <= 0:
            return None
        if self.is_team_shield:
            return {
                "target_hp_ratio": 0.07,
                "caster_defense_ratio": 0.45,
                "cap_target_hp_ratio": 0.25,
            }
        return {
            "caster_hp_ratio": 0.12,
            "caster_defense_ratio": 0.80,
            "cap_target_hp_ratio": 0.35,
        }

    @property
    def is_ready(self):
        return self.current_cd <= 0.0

    def update(self, dt):
        if self.current_cd > 0:
            self.current_cd = max(0.0, self.current_cd - dt)

    def trigger(self):
        self.current_cd = self.cooldown

    def clone(self):
        s = Skill(
            skill_id=self.skill_id,
            name=self.name,
            cooldown=self.cooldown,
            dmg_mult=self.dmg_mult,
            lifesteal_bonus=self.lifesteal_bonus,
            shield_bonus=self.shield_bonus,
            unlock_lvl=self.unlock_lvl,
            icon=self.icon,
            color=self.color,
            desc=self.desc,
            skill_type=self.skill_type,
            hit_count=self.hit_count,
            buff_type=self.buff_type,
            buff_val=self.buff_val,
            buff_duration=self.buff_duration,
            effect_name=self.effect_name,
            tag_name=self.tag_name,
            is_aoe=self.is_aoe,
            is_team_shield=self.is_team_shield,
            dot_type=self.dot_type,
            execute_bonus=self.execute_bonus,
            shield_formula=self.shield_formula
        )
        s.current_cd = self.current_cd
        return s


    def to_dict(self):
        return {
            "skill_id": self.skill_id,
            "current_cd": self.current_cd
        }


def is_skill_aoe(skill):
    """判定技能是否為範圍橫掃 / 全屏 AOE 打擊"""
    if not skill:
        return False
    if getattr(skill, "is_aoe", False):
        return True
    st = getattr(skill, "skill_type", "").lower()
    if st in ["aoe", "aoe_beam"]:
        return True
    tag = getattr(skill, "tag_name", "")
    if any(k in tag for k in ["全屏", "群體", "AOE", "全體打擊", "全螢幕"]):
        return True
    name = getattr(skill, "name", "")
    aoe_names = [
        "天怒", "暴風雪", "火焰流星", "火流星", "暗黑世紀", "聖域", "空間斬", "ICBM",
        "滾動彩虹", "宇宙之雨", "狂豹風暴", "巨型雷射砲", "焰火滅世", "日蝕", "霹靂",
        "阿修羅", "楓幣炸彈", "遺物解放", "章魚砲台", "冰霜新星"
    ]
    if any(k in name for k in aoe_names):
        return True
    return False

