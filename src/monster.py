"""
《新楓之谷：放置遠征隊》怪物實體與技能優先級 (monster.py)
"""

class Monster:
    def __init__(self, data, is_boss=False):
        self.name = data["name"]
        self.lvl = data["lvl"]
        self.max_hp = data["hp"]
        self.hp = data["hp"]
        self.atk = data["atk"]
        self.defense = data.get("def", 0)
        # 新楓之谷正統防禦率機制 (defense_rate):
        # 若 data 中顯式指定 def_rate 則優先採用；否則依怪物定位動態推算：
        # - 木樁/自定義直接以傳入 def 或 def_rate 決定
        # - 頂級首領 (Lv.160+ 戴米安/史烏/黑魔法師/瑟倫等): 300% (3.0)
        # - 中階首領 (Lv.60~159 鐘樓/混龍/皮卡啾): 100% (1.0)
        # - 初階首領 (Lv.<60 菇菇/樹妖/水靈王): 50% (0.5)
        # - 一般菁英怪: 50% (0.5)
        # - 一般小怪: 10% ~ 30% (依等級平滑成長)
        if "def_rate" in data:
            self.defense_rate = float(data["def_rate"])
        elif "defense_rate" in data:
            self.defense_rate = float(data["defense_rate"])
        elif data.get("is_dummy", False):
            # 木樁防禦：若傳入數值大於等於 10 (例如 20, 100, 300)，視為百分比轉為小數；若 <= 5 則視為小數倍率
            raw_d = float(data.get("def", 0))
            self.defense_rate = raw_d / 100.0 if raw_d >= 5.0 else raw_d
        elif is_boss:
            if self.lvl >= 160:
                self.defense_rate = 3.0  # 300% (戴米安、史烏、黑魔法師、原初首領)
            elif self.lvl >= 60:
                self.defense_rate = 1.0  # 100% (鐘樓帕普拉圖斯、闇黑龍王、皮卡啾)
            else:
                self.defense_rate = 0.5  # 50% (新手村與初期首領)
        elif data.get("is_elite", False):
            self.defense_rate = 0.50
        else:
            self.defense_rate = min(0.30, 0.10 + (self.lvl * 0.0007))  # 10% ~ 30%
        self.attack_speed = data["spd"]
        self.is_boss = is_boss
        self.attack_timer = 0.0

        # 控制狀態：極寒凍結 (凍結期間無法累積攻擊條)
        self.freeze_timer = 0.0

        # 楓之谷異常狀態 (元素灼燒、流血、極寒)
        self.burn_timer = 0.0
        self.burn_tick = 0.0
        self.burn_dmg = 0

        self.bleed_timer = 0.0
        self.bleed_tick = 0.0
        self.bleed_dmg = 0

        self.chill_timer = 0.0

        # 首領與菁英怪戰鬥擴充：技能池、護盾、殘血狂暴、菁英詞綴
        self.skills = []
        self.shield = 0
        self.is_enraged = False
        self.is_elite = data.get("is_elite", False)
        self.elite_affix = data.get("elite_affix", "")

    def take_damage(self, amount):
        """護盾優先抵扣傷害"""
        absorbed = min(self.shield, amount)
        self.shield -= absorbed
        remaining = amount - absorbed
        self.hp = max(0, self.hp - remaining)
        return remaining, absorbed

    @property
    def is_alive(self):
        return self.hp > 0

    @property
    def exp_reward(self):
        mult = 3.2 if self.is_boss else (1.8 if getattr(self, "is_elite", False) else 1.0)
        return int(self.lvl * 32 * mult)

    @property
    def gold_reward(self):
        mult = 2.8 if self.is_boss else (1.6 if getattr(self, "is_elite", False) else 1.0)
        return int(self.lvl * 28 * mult)


def get_skill_priority(skill):
    """
    技能施放優先順序評分 (數值越小越優先施放)：
    1: 團隊光環與戰術增益 (team_buff, buff) - 優先開光環，使後續輸出吃滿加成
    2: 終極神罰 / 全屏大招 / 高倍率核能 (burst, stack_burst, aoe_beam, 或倍率 >= 3.0)
    3: 控場 / 護盾 / 急救 (freeze, shield, heal) - 壓制怪物行動並保護隊友
    4: 多段連擊打擊 (multi_hit) - 穿甲多段削血
    5: 常規短 CD 技能 (damage) - 補刀平砍
    """
    st = getattr(skill, "skill_type", "").lower()
    mult = getattr(skill, "dmg_mult", 1.0)
    if st in ["team_buff", "buff"]:
        return 1
    if st in ["burst", "stack_burst", "aoe_beam"] or mult >= 3.0:
        return 2
    if st in ["freeze", "shield", "heal"]:
        return 3
    if st == "multi_hit":
        return 4
    return 5


