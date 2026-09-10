"""
《新楓之谷：放置遠征隊》內在能力系統 (Inner Ability / inner_ability.py)

原版 TMS 機制考究實作：
1. 四大階級：特殊 (rare) -> 稀有 (epic) -> 罕見 (unique) -> 傳說 (legendary)。
2. 防掉階機制：洗練永不降階；有固定機率突破升階（最高傳說）。
3. 排數規則：
   - 達到傳說階級時，第一排必定為「傳說級」詞條。
   - 第二、三排最高僅能洗出「罕見級」詞條。
4. 鎖定機制：可鎖定階級與特定排數，鎖定需消耗額外名譽點數 (Honor EXP)。
5. 核心熱門詞條：
   - BOSS 傷害增加 (傳說 +20%, 罕見 +10%)
   - 增益效果持續時間 (傳說 +50%, 罕見 +35%)
   - 技能冷卻時間略過 (無冷，傳說 20%, 罕見 10%)
   - 攻擊速度階段提升 (傳說專屬)
   - 被動技能等級提升 +1 (傳說專屬)
   - 對異常狀態敵人增傷 (傳說 +10%, 罕見 +5%)
   - 爆擊機率增加 (傳說 +30%, 罕見 +18%)
   - 道具掉落率 / 楓幣獲得量增加 (傳說 +20%, 罕見 +12%)
   - 攻擊力 (傳說 +30, 罕見 +20)
"""

import random

TIER_ORDER = ["rare", "epic", "unique", "legendary"]

TIER_NAMES = {
    "rare": "特殊",
    "epic": "稀有",
    "unique": "罕見",
    "legendary": "傳說"
}

TIER_COLORS = {
    "rare": (120, 180, 255),      # 藍色
    "epic": (190, 120, 255),      # 紫色
    "unique": (255, 210, 60),     # 金黃色
    "legendary": (80, 240, 120)   # 翠綠色
}

# 各階級基本洗練名譽消耗
REROLL_COST_BY_TIER = {
    "rare": 100,
    "epic": 500,
    "unique": 2000,
    "legendary": 5000
}

# 鎖定排數額外名譽消耗 (鎖定 1 排 +3,000, 鎖定 2 排 +10,000)
LOCK_LINE_EXTRA_COST = {
    0: 0,
    1: 3000,
    2: 10000,
}

# 詞條定義池
ABILITY_DEFINITIONS = {
    "boss_damage": {
        "name": "BOSS 怪物傷害增加",
        "min_tier": "rare",
        "max_tier": "legendary",
        "is_percent": True,
        "values": {"rare": 0.03, "epic": 0.06, "unique": 0.10, "legendary": 0.20}
    },
    "buff_duration": {
        "name": "增益效果持續時間增加",
        "min_tier": "rare",
        "max_tier": "legendary",
        "is_percent": True,
        "values": {"rare": 0.10, "epic": 0.20, "unique": 0.35, "legendary": 0.50}
    },
    "cooldown_skip": {
        "name": "使用技能時一定機率略過冷卻 (無冷)",
        "min_tier": "epic",
        "max_tier": "legendary",
        "is_percent": True,
        "values": {"epic": 0.05, "unique": 0.10, "legendary": 0.20}
    },
    "attack_speed": {
        "name": "攻擊速度增加 (攻擊間隔縮短)",
        "min_tier": "legendary",
        "max_tier": "legendary",
        "is_percent": False,
        "values": {"legendary": 0.20}
    },
    "passive_level": {
        "name": "被動技能等級提升 +1 (全隊傷害 +10%)",
        "min_tier": "legendary",
        "max_tier": "legendary",
        "is_percent": False,
        "values": {"legendary": 1}
    },
    "crit_chance": {
        "name": "爆擊機率增加",
        "min_tier": "rare",
        "max_tier": "legendary",
        "is_percent": True,
        "values": {"rare": 0.05, "epic": 0.10, "unique": 0.18, "legendary": 0.30}
    },
    "damage_abnormal": {
        "name": "對處於異常狀態敵人增傷",
        "min_tier": "epic",
        "max_tier": "legendary",
        "is_percent": True,
        "values": {"epic": 0.03, "unique": 0.05, "legendary": 0.10}
    },
    "drop_rate": {
        "name": "道具掉落率增加",
        "min_tier": "epic",
        "max_tier": "legendary",
        "is_percent": True,
        "values": {"epic": 0.06, "unique": 0.12, "legendary": 0.20}
    },
    "meso_rate": {
        "name": "楓幣獲得量增加",
        "min_tier": "epic",
        "max_tier": "legendary",
        "is_percent": True,
        "values": {"epic": 0.06, "unique": 0.12, "legendary": 0.20}
    },
    "attack": {
        "name": "物理/魔法攻擊力增加",
        "min_tier": "rare",
        "max_tier": "legendary",
        "is_percent": False,
        "values": {"rare": 6, "epic": 12, "unique": 20, "legendary": 30}
    },
    "def_ignore": {
        "name": "無視目標怪物防禦力",
        "min_tier": "epic",
        "max_tier": "legendary",
        "is_percent": True,
        "values": {"epic": 0.05, "unique": 0.10, "legendary": 0.20}
    }
}


class InnerAbilityLine:
    """單條內在能力屬性"""
    def __init__(self, stat_type: str = "attack", tier: str = "rare", val: float = 6.0, locked: bool = False):
        self.stat_type = stat_type
        self.tier = tier
        self.val = val
        self.locked = locked

    @property
    def name(self) -> str:
        defn = ABILITY_DEFINITIONS.get(self.stat_type)
        return defn["name"] if defn else self.stat_type

    @property
    def display_text(self) -> str:
        defn = ABILITY_DEFINITIONS.get(self.stat_type)
        if not defn:
            return f"{self.stat_type} +{self.val}"
        tier_name = TIER_NAMES.get(self.tier, self.tier)
        if defn["is_percent"]:
            val_str = f"+{int(round(self.val * 100))}%"
        elif self.stat_type == "passive_level":
            val_str = "+1"
        elif self.stat_type == "attack_speed":
            val_str = f"+{self.val:.2f}s"
        else:
            val_str = f"+{int(self.val)}"
        return f"[{tier_name}] {defn['name']} {val_str}"

    def to_dict(self) -> dict:
        return {
            "stat_type": self.stat_type,
            "tier": self.tier,
            "val": self.val,
            "locked": self.locked
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            stat_type=data.get("stat_type", "attack"),
            tier=data.get("tier", "rare"),
            val=float(data.get("val", 6.0)),
            locked=bool(data.get("locked", False))
        )


class InnerAbility:
    """角色內在能力 (3 排潛能、階級與洗練)"""
    def __init__(self):
        self.tier = "rare"  # rare, epic, unique, legendary
        self.honor_exp = 20000  # 初始給予兩萬名譽點數體驗
        self.lines = [
            InnerAbilityLine("attack", "rare", 6.0),
            InnerAbilityLine("crit_chance", "rare", 0.05),
            InnerAbilityLine("boss_damage", "rare", 0.03)
        ]

    def get_reroll_cost(self) -> int:
        """計算當前鎖定配置下洗練所需名譽點數"""
        base = REROLL_COST_BY_TIER.get(self.tier, 100)
        locked_count = sum(1 for line in self.lines if line.locked)
        extra = LOCK_LINE_EXTRA_COST.get(min(2, locked_count), 0)
        return base + extra

    def can_reroll(self) -> tuple[bool, str]:
        cost = self.get_reroll_cost()
        locked_count = sum(1 for line in self.lines if line.locked)
        if locked_count >= 3:
            return False, "不能鎖定全部 3 排進行洗練！"
        if self.honor_exp < cost:
            return False, f"名譽點數不足！需要 {cost:,} 點 (當前: {self.honor_exp:,})"
        return True, ""

    def reroll(self) -> tuple[bool, str]:
        """執行洗練邏輯：防掉階、升階判定、首排頂級保底、二三排最高罕見"""
        can, msg = self.can_reroll()
        if not can:
            return False, msg

        cost = self.get_reroll_cost()
        self.honor_exp -= cost

        # 升階判定 (若尚未達到傳說)
        upgraded = False
        if self.tier == "rare" and random.random() < 0.20:
            self.tier = "epic"
            upgraded = True
        elif self.tier == "epic" and random.random() < 0.10:
            self.tier = "unique"
            upgraded = True
        elif self.tier == "unique" and random.random() < 0.05:
            self.tier = "legendary"
            upgraded = True

        # 重骰未鎖定的排數
        used_stat_types = {line.stat_type for line in self.lines if line.locked}

        for idx, line in enumerate(self.lines):
            if line.locked:
                continue

            # 決定該排的階級
            if idx == 0:
                # 第一排必定為當前潛能階級！
                line_tier = self.tier
            else:
                # 第二、三排最高僅為罕見！
                if self.tier == "legendary":
                    r = random.random()
                    if r < 0.18:
                        line_tier = "unique"
                    elif r < 0.65:
                        line_tier = "epic"
                    else:
                        line_tier = "rare"
                elif self.tier == "unique":
                    r = random.random()
                    if r < 0.20:
                        line_tier = "unique"
                    elif r < 0.65:
                        line_tier = "epic"
                    else:
                        line_tier = "rare"
                elif self.tier == "epic":
                    line_tier = "epic" if random.random() < 0.40 else "rare"
                else:
                    line_tier = "rare"

            # 從定義池中選取合適詞條 (不重複已鎖定或同次選出的詞條)
            candidates = []
            for stype, sdata in ABILITY_DEFINITIONS.items():
                if stype in used_stat_types:
                    continue
                min_idx = TIER_ORDER.index(sdata["min_tier"])
                max_idx = TIER_ORDER.index(sdata["max_tier"])
                cur_idx = TIER_ORDER.index(line_tier)
                if min_idx <= cur_idx <= max_idx and line_tier in sdata["values"]:
                    candidates.append(stype)

            if not candidates:
                candidates = ["attack", "crit_chance"]

            chosen_type = random.choice(candidates)
            used_stat_types.add(chosen_type)
            defn = ABILITY_DEFINITIONS[chosen_type]
            val = defn["values"][line_tier]

            self.lines[idx] = InnerAbilityLine(chosen_type, line_tier, val, locked=False)

        res_msg = f"內在能力洗練成功！消耗 {cost:,} 名譽點數。"
        if upgraded:
            res_msg = f"🎉 突破極限！內在能力晉級至【{TIER_NAMES[self.tier]}】階級！\n" + res_msg

        return True, res_msg

    def matches_target(self, target_tier: str = None, target_stat: str = None) -> bool:
        """檢測是否達成目標階級與指定詞條"""
        if target_tier and target_tier != "any":
            tgt_idx = TIER_ORDER.index(target_tier) if target_tier in TIER_ORDER else 0
            cur_idx = TIER_ORDER.index(self.tier) if self.tier in TIER_ORDER else 0
            if cur_idx < tgt_idx:
                return False
        if target_stat and target_stat != "any":
            found = False
            for line in self.lines:
                if line.stat_type == target_stat:
                    found = True
                    break
                if target_stat in line.name or target_stat in line.display_text:
                    found = True
                    break
            if not found:
                return False
        return True

    def auto_reroll(self, target_stat: str = None, target_tier: str = "legendary", max_attempts: int = 1000) -> tuple[bool, str]:
        """一鍵洗內潛：洗到達成指定階級或詞條為止"""
        if self.matches_target(target_tier=target_tier, target_stat=target_stat):
            return False, "當前內在能力已滿足目標條件！"

        attempts = 0
        honor_spent = 0

        while attempts < max_attempts:
            can, msg = self.can_reroll()
            if not can:
                break
            cost = self.get_reroll_cost()
            success, r_msg = self.reroll()
            if not success:
                break
            attempts += 1
            honor_spent += cost
            if self.matches_target(target_tier=target_tier, target_stat=target_stat):
                break

        tier_name = TIER_NAMES.get(self.tier, self.tier)
        lines_summary = "\n".join([f"• {l.display_text}" for l in self.lines])

        if self.matches_target(target_tier=target_tier, target_stat=target_stat):
            return True, f"🎉 達成內潛目標！\n當前階級：【{tier_name}】\n共洗練 {attempts} 次，消耗 {honor_spent:,} 點名譽點數\n詞條：\n{lines_summary}"
        elif self.honor_exp < self.get_reroll_cost():
            return False, f"⚠️ 名譽點數不足中斷！\n當前階級：【{tier_name}】\n共洗練 {attempts} 次，消耗 {honor_spent:,} 點名譽點數\n詞條：\n{lines_summary}"
        else:
            return False, f"⚠️ 已達最大洗練次數 ({max_attempts}次)！\n當前階級：【{tier_name}】\n消耗 {honor_spent:,} 點名譽點數\n詞條：\n{lines_summary}"

    def toggle_lock(self, line_idx: int) -> tuple[bool, str]:
        """切換排數鎖定狀態"""
        if line_idx < 0 or line_idx >= len(self.lines):
            return False, "無效排數"
        cur = self.lines[line_idx].locked
        if not cur:
            locked_count = sum(1 for line in self.lines if line.locked)
            if locked_count >= 2:
                return False, "最多只能同時鎖定 2 排！"
            self.lines[line_idx].locked = True
            return True, f"已鎖定第 {line_idx + 1} 排"
        else:
            self.lines[line_idx].locked = False
            return True, f"已解除鎖定第 {line_idx + 1} 排"

    def get_stat_sum(self, stat_type: str) -> float:
        """加總特定數值"""
        return sum(line.val for line in self.lines if line.stat_type == stat_type)

    def to_dict(self) -> dict:
        return {
            "tier": self.tier,
            "honor_exp": self.honor_exp,
            "lines": [line.to_dict() for line in self.lines]
        }

    @classmethod
    def from_dict(cls, data: dict):
        obj = cls()
        if not data:
            return obj
        obj.tier = data.get("tier", "rare")
        obj.honor_exp = int(data.get("honor_exp", 20000))
        lines_data = data.get("lines", [])
        if lines_data and len(lines_data) == 3:
            obj.lines = [InnerAbilityLine.from_dict(ld) for ld in lines_data]
        return obj

