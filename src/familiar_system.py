"""
《新楓之谷：放置遠征隊》萌獸系統 (Familiar System / familiar_system.py)

原版 TMS (台灣新楓之谷) 特有超核心系統考究實作：
1. 3 隻萌獸召喚槽位：最多可同時召喚 3 隻萌獸陪伴戰鬥。
2. 潛能階級：
   普通 (common) -> 特殊 (rare) -> 稀有 (epic) -> 罕見 (unique) -> 傳說 (legendary)。
3. 核心神級潛能條目：
   - 最終傷害 (final_damage): TMS 頂級詞條！傳說級單排高達 20%！採「獨立相乘」乘區！
   - BOSS 怪物傷害 (boss_damage): 傳說級最高 40%！
   - 無視目標怪物防禦 (def_ignore): 傳說級最高 40%！
   - 全隊定時恢復光環 (team_hp_regen): 每 4 秒為全隊回復 10%~15% 生命值，首領戰保命神技！
   - 物理/魔法攻擊力百分比 (attack_pct): 傳說級 12%！
   - 暴擊傷害 (crit_damage): 傳說級 10%！
4. 萌獸卡洗煉：
   - 消耗萌獸卡包進行洗練，有固定機率跨階晉升至傳說階級。
   - 支援洗出「雙終一物」或「傳說三終」夢幻頂規配置！
"""

import random

FAMILIAR_TIER_ORDER = ["common", "rare", "epic", "unique", "legendary"]

FAMILIAR_TIER_NAMES = {
    "common": "普通",
    "rare": "特殊",
    "epic": "稀有",
    "unique": "罕見",
    "legendary": "傳說"
}

FAMILIAR_TIER_COLORS = {
    "common": (180, 180, 180),
    "rare": (120, 180, 255),
    "epic": (190, 120, 255),
    "unique": (255, 210, 60),
    "legendary": (80, 240, 120)
}

FAMILIAR_POTENTIAL_DEFINITIONS = {
    "final_damage": {
        "name": "最終傷害增加 (獨立乘區)",
        "min_tier": "rare",
        "values": {"rare": 0.04, "epic": 0.07, "unique": 0.12, "legendary": 0.20}
    },
    "boss_damage": {
        "name": "BOSS 怪物攻擊時傷害增加",
        "min_tier": "rare",
        "values": {"rare": 0.10, "epic": 0.20, "unique": 0.30, "legendary": 0.40}
    },
    "def_ignore": {
        "name": "無視怪物防禦率",
        "min_tier": "rare",
        "values": {"rare": 0.15, "epic": 0.20, "unique": 0.30, "legendary": 0.40}
    },
    "team_hp_regen": {
        "name": "召喚時每 4 秒全隊持續回復 HP",
        "min_tier": "rare",
        "values": {"rare": 0.05, "epic": 0.08, "unique": 0.10, "legendary": 0.15}
    },
    "attack_pct": {
        "name": "物理/魔法攻擊力增加",
        "min_tier": "rare",
        "values": {"rare": 0.03, "epic": 0.06, "unique": 0.09, "legendary": 0.12}
    },
    "crit_damage": {
        "name": "暴擊傷害增加",
        "min_tier": "rare",
        "values": {"rare": 0.02, "epic": 0.04, "unique": 0.06, "legendary": 0.10}
    }
}


class FamiliarLine:
    """萌獸單條潛能"""
    def __init__(self, pot_type: str = "final_damage", tier: str = "rare", val: float = 0.04):
        self.pot_type = pot_type
        self.tier = tier
        self.val = val

    @property
    def display_text(self) -> str:
        defn = FAMILIAR_POTENTIAL_DEFINITIONS.get(self.pot_type)
        if not defn:
            return f"{self.pot_type} +{self.val}"
        t_name = FAMILIAR_TIER_NAMES.get(self.tier, self.tier)
        pct_val = int(round(self.val * 100))
        return f"[{t_name}] {defn['name']} +{pct_val}%"

    def to_dict(self) -> dict:
        return {"pot_type": self.pot_type, "tier": self.tier, "val": self.val}

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            pot_type=d.get("pot_type", "final_damage"),
            tier=d.get("tier", "rare"),
            val=float(d.get("val", 0.04))
        )


TIER_UP_EXP = {
    "common": 50,
    "rare": 120,
    "epic": 300,
    "unique": 800,
    "legendary": 999999
}

FODDER_EXP_VAL = {
    "common": 25,
    "rare": 60,
    "epic": 150,
    "unique": 400,
    "legendary": 1000
}


class Familiar:
    """單隻萌獸"""
    def __init__(self, fid: str, name: str, tier: str = "rare", lines: list = None, is_summoned: bool = False, exp: int = 0):
        self.fid = fid
        self.name = name
        self.tier = tier  # common, rare, epic, unique, legendary
        self.is_summoned = is_summoned
        self.exp = exp
        self.lines = lines or [
            FamiliarLine("final_damage", self.tier, 0.04),
            FamiliarLine("boss_damage", self.tier, 0.10),
            FamiliarLine("team_hp_regen", self.tier, 0.05)
        ]

    @property
    def tag_summary(self) -> str:
        """檢測雙終、三終等神級標記"""
        fd_count = sum(1 for line in self.lines if line.pot_type == "final_damage")
        if fd_count >= 3:
            return "👑 傳奇三終"
        elif fd_count == 2:
            return "⭐ 雙終極品"
        elif fd_count == 1:
            return "✨ 單終"
        return ""

    def add_exp(self, amount: int) -> tuple[bool, str]:
        """吞噬素材增加經驗值並判定升階突破"""
        if self.tier == "legendary":
            return False, f"【{self.name}】已達最高傳說階級！"
        self.exp += amount
        needed = TIER_UP_EXP.get(self.tier, 999999)
        upgraded = False
        msgs = []
        while self.exp >= needed and self.tier != "legendary":
            self.exp -= needed
            cur_idx = FAMILIAR_TIER_ORDER.index(self.tier)
            self.tier = FAMILIAR_TIER_ORDER[cur_idx + 1]
            upgraded = True
            msgs.append(f"🎉 突破極限！【{self.name}】成功晉升為【{FAMILIAR_TIER_NAMES[self.tier]}】階級！")
            self.reroll_potentials()
            needed = TIER_UP_EXP.get(self.tier, 999999)

        if upgraded:
            return True, "\n".join(msgs)
        return True, f"【{self.name}】獲得 {amount} 點萌獸經驗 (進度: {self.exp}/{needed} EXP)"

    def reroll_potentials(self) -> tuple[bool, str]:
        """重置萌獸潛能，並有機會突破升階"""
        # 升階機率：rare -> epic: 15%, epic -> unique: 8%, unique -> legendary: 3%
        upgraded = False
        if self.tier == "rare" and random.random() < 0.15:
            self.tier = "epic"
            upgraded = True
        elif self.tier == "epic" and random.random() < 0.08:
            self.tier = "unique"
            upgraded = True
        elif self.tier == "unique" and random.random() < 0.03:
            self.tier = "legendary"
            upgraded = True

        new_lines = []
        pot_keys = list(FAMILIAR_POTENTIAL_DEFINITIONS.keys())

        for idx in range(3):
            # 萌獸潛能階級：首排保底本階，二三排以本階或次一階為主
            if idx == 0:
                line_tier = self.tier
            else:
                cur_idx = FAMILIAR_TIER_ORDER.index(self.tier)
                if cur_idx > 1 and random.random() < 0.40:
                    line_tier = FAMILIAR_TIER_ORDER[cur_idx - 1]
                else:
                    line_tier = self.tier

            chosen_key = random.choice(pot_keys)
            defn = FAMILIAR_POTENTIAL_DEFINITIONS[chosen_key]
            # 取得該階數值
            val = defn["values"].get(line_tier, defn["values"].get("rare", 0.04))
            new_lines.append(FamiliarLine(chosen_key, line_tier, val))

        self.lines = new_lines
        msg = f"【{self.name}】潛能洗煉完成！"
        if upgraded:
            msg = f"🎉 萌獸突破極限！晉級至【{FAMILIAR_TIER_NAMES[self.tier]}】階級！\n" + msg
        if self.tag_summary:
            msg += f" ({self.tag_summary})"
        return True, msg

    def matches_target_condition(self, mode: str) -> bool:
        """檢驗萌獸潛能目標是否達成"""
        if mode == "legendary":
            return self.tier == "legendary"
        fd_cnt = sum(1 for l in self.lines if l.pot_type == "final_damage")
        if mode == "triple_final":
            return fd_cnt >= 3
        elif mode == "double_final":
            return fd_cnt >= 2
        elif mode == "any_fd":
            return fd_cnt >= 1
        elif mode == "boss_damage":
            return any(l.pot_type == "boss_damage" for l in self.lines)
        return True

    def auto_reroll_potentials(self, manager, target_mode: str = "any_fd", max_cubes: int = 100) -> tuple[bool, str]:
        """一鍵洗萌獸潛能：使用神奇萌獸方塊持續洗練直到達成目標"""
        if self.matches_target_condition(target_mode):
            return False, "當前萌獸潛能已滿足目標條件！"

        attempts = 0
        while attempts < max_cubes:
            if manager.familiar_cubes <= 0:
                break
            manager.familiar_cubes -= 1
            attempts += 1
            self.reroll_potentials()
            if self.matches_target_condition(target_mode):
                break

        lines_summary = "\n".join([f"• {l.display_text}" for l in self.lines])
        tag = f" ({self.tag_summary})" if self.tag_summary else ""

        if self.matches_target_condition(target_mode):
            return True, f"🎉 萌獸一鍵洗潛成功達成目標{tag}！\n階級：【{FAMILIAR_TIER_NAMES[self.tier]}】\n共消耗 {attempts} 顆神奇萌獸方塊\n詞條：\n{lines_summary}"
        elif manager.familiar_cubes <= 0:
            return False, f"⚠️ 神奇萌獸方塊已用盡中斷！\n當前階級：【{FAMILIAR_TIER_NAMES[self.tier]}】{tag}\n共洗練 {attempts} 次，請至轉蛋屋商店補充方塊！\n詞條：\n{lines_summary}"
        else:
            return False, f"⚠️ 已達單次洗練次數上限 ({max_cubes}次)！\n當前階級：【{FAMILIAR_TIER_NAMES[self.tier]}】{tag}\n詞條：\n{lines_summary}"

    def to_dict(self) -> dict:
        return {
            "fid": self.fid,
            "name": self.name,
            "tier": self.tier,
            "is_summoned": self.is_summoned,
            "exp": self.exp,
            "lines": [line.to_dict() for line in self.lines]
        }

    @classmethod
    def from_dict(cls, d: dict):
        lines = [FamiliarLine.from_dict(ld) for ld in d.get("lines", [])]
        return cls(
            fid=d.get("fid", "fam_balrog"),
            name=d.get("name", "巴洛古"),
            tier=d.get("tier", "rare"),
            lines=lines if len(lines) == 3 else None,
            is_summoned=bool(d.get("is_summoned", False)),
            exp=int(d.get("exp", 0))
        )


class FamiliarManager:
    """萌獸管理庫 (限制同時出戰 1 隻、獨立終傷相乘計算、定時光環回復、吞噬升階)"""
    def __init__(self):
        self.familiar_cards = 20  # 萌獸洗潛方塊庫存 (alias: familiar_cubes)
        self.familiars = [
            # 初始預設僅 1 隻出戰主戰萌獸
            Familiar("fam_pinkbean", "皮卡啾", "unique", [
                FamiliarLine("final_damage", "unique", 0.12),
                FamiliarLine("boss_damage", "unique", 0.30),
                FamiliarLine("team_hp_regen", "unique", 0.10)
            ], is_summoned=True),
            Familiar("fam_lucid", "露希妲", "unique", [
                FamiliarLine("final_damage", "unique", 0.12),
                FamiliarLine("attack_pct", "unique", 0.09),
                FamiliarLine("def_ignore", "unique", 0.30)
            ], is_summoned=False),
            Familiar("fam_magnus", "暴君梅格耐斯", "rare", [
                FamiliarLine("boss_damage", "rare", 0.10),
                FamiliarLine("crit_damage", "rare", 0.02),
                FamiliarLine("final_damage", "rare", 0.04)
            ], is_summoned=False),
            Familiar("fam_balrog", "魔王巴洛古", "rare", is_summoned=False),
            Familiar("fam_zakum", "殘暴炎魔", "rare", is_summoned=False),
        ]
        self.aura_timer = 0.0  # 4 秒光環計時器

    @property
    def familiar_cubes(self) -> int:
        return self.familiar_cards

    @familiar_cubes.setter
    def familiar_cubes(self, val: int):
        self.familiar_cards = max(0, val)

    def add_familiar(self, fam: Familiar) -> tuple[bool, str]:
        """將萌獸收入卡冊"""
        self.familiars.append(fam)
        t_name = FAMILIAR_TIER_NAMES.get(fam.tier, fam.tier)
        return True, f"獲得【{fam.name} ({t_name})】！已存入萌獸卡冊。"

    def get_summoned_familiars(self) -> list[Familiar]:
        """同時間僅保留 1 隻主戰萌獸生效"""
        return [f for f in self.familiars if f.is_summoned][:1]

    def set_summoned(self, fid: str, summon: bool) -> tuple[bool, str]:
        """設定出戰萌獸 (同時間限 1 隻，召喚時自動收回其他萌獸)"""
        fam = next((f for f in self.familiars if f.fid == fid), None)
        if not fam:
            return False, "找不到指定萌獸"
        if summon:
            for f in self.familiars:
                f.is_summoned = False
            fam.is_summoned = True
            return True, f"【{fam.name}】已成功召喚出戰！(同時間生效 1 隻主戰萌獸)"
        else:
            fam.is_summoned = False
            return True, f"【{fam.name}】已收回萌獸卡冊。"

    def batch_feed_low_tier(self, target_fid: str) -> tuple[bool, str]:
        """一鍵吞噬所有未出戰的低階萌獸 (普通/特殊) 升級主戰萌獸"""
        target = next((f for f in self.familiars if f.fid == target_fid), None)
        if not target:
            return False, "找不到目標主戰萌獸"
        if target.tier == "legendary":
            return False, "該萌獸已達傳說最高階級，無需再吞噬升級！"

        fodders = [
            f for f in self.familiars
            if f.fid != target_fid and not f.is_summoned and f.tier in ["common", "rare"]
        ]
        if not fodders:
            return False, "卡冊中沒有多餘的未出戰低階萌獸 (普通/特殊)！請至冒險關卡討伐怪物掉落獲取。"

        total_exp = 0
        count = len(fodders)
        for fodder in fodders:
            total_exp += FODDER_EXP_VAL.get(fodder.tier, 25)
            self.familiars.remove(fodder)

        ok, msg = target.add_exp(total_exp)
        return True, f"成功吞噬 {count} 隻素材萌獸，為【{target.name}】注入 {total_exp} EXP！\n{msg}"

    def feed_fodder(self, target_fid: str, fodder_fid: str) -> tuple[bool, str]:
        """單隻吞噬升階"""
        target = next((f for f in self.familiars if f.fid == target_fid), None)
        fodder = next((f for f in self.familiars if f.fid == fodder_fid), None)
        if not target or not fodder:
            return False, "找不到指定萌獸"
        if target.fid == fodder.fid:
            return False, "不能吞噬自己！"
        if fodder.is_summoned:
            return False, "出戰中的萌獸不可作為素材！"
        if fodder.tier in ["unique", "legendary"]:
            return False, "保護機制：罕見與傳說高階萌獸不可直接作為素材消耗！"

        exp_gain = FODDER_EXP_VAL.get(fodder.tier, 25)
        self.familiars.remove(fodder)
        ok, msg = target.add_exp(exp_gain)
        return True, f"成功吞噬【{fodder.name}】(+{exp_gain} EXP)！\n{msg}"

    def get_final_damage_multiplier(self) -> float:
        """
        計算出戰萌獸的『獨立終傷乘區』：
        TMS 原汁原味公式：每一條終傷獨立相乘！
        例如兩條 20% 終傷：(1 + 0.20) * (1 + 0.20) = 1.44 (+44%)
        """
        mult = 1.0
        for fam in self.get_summoned_familiars():
            for line in fam.lines:
                if line.pot_type == "final_damage":
                    mult *= (1.0 + line.val)
        return mult

    def get_stat_sum(self, pot_type: str) -> float:
        """加總出戰萌獸的特定屬性 (如 boss_damage, def_ignore, attack_pct 等)"""
        total = 0.0
        for fam in self.get_summoned_familiars():
            for line in fam.lines:
                if line.pot_type == pot_type:
                    total += line.val
        return total

    def update_regen_aura(self, dt: float, player) -> int:
        """
        每 4 秒觸發萌獸定時全隊回復光環
        :return: 觸發回復的全隊總治療量 (若未觸發則為 0)
        """
        self.aura_timer += dt
        if self.aura_timer < 4.0:
            return 0

        self.aura_timer -= 4.0
        regen_ratio = self.get_stat_sum("team_hp_regen")
        if regen_ratio <= 0.0:
            return 0

        total_healed = 0
        for m in player.team:
            if m.is_alive:
                m_max_hp = m.get_max_hp(player)
                heal = int(m_max_hp * regen_ratio)
                if heal > 0:
                    old_hp = m.current_hp
                    m.current_hp = min(float(m_max_hp), m.current_hp + heal)
                    total_healed += int(m.current_hp - old_hp)

        return total_healed

    def to_dict(self) -> dict:
        return {
            "familiar_cards": self.familiar_cards,
            "familiars": [f.to_dict() for f in self.familiars]
        }

    @classmethod
    def from_dict(cls, d: dict):
        obj = cls()
        if not d:
            return obj
        obj.familiar_cards = int(d.get("familiar_cards", 20))
        f_list = d.get("familiars", [])
        if f_list:
            obj.familiars = [Familiar.from_dict(fd) for fd in f_list]
        return obj


STAGE_COMMON_FAMILIARS = [
    ("fam_slime", "綠水靈"),
    ("fam_mushroom", "菇菇寶貝"),
    ("fam_ribbon_pig", "漂漂豬"),
    ("fam_stump", "木妖"),
    ("fam_blue_snail", "藍水靈"),
]

STAGE_RARE_FAMILIARS = [
    ("fam_golem", "巨石人"),
    ("fam_evil_eye", "幼魔精靈"),
    ("fam_zombie_mush", "殭屍蘑菇"),
    ("fam_mush_king", "蘑菇王"),
    ("fam_balrog_mini", "小巴洛古"),
]

GACHAPON_HIGH_FAMILIARS = [
    ("fam_lucid", "夢之主露希妲", "unique"),
    ("fam_will", "蜘蛛之王威爾", "unique"),
    ("fam_damien", "破滅之翼戴米安", "unique"),
    ("fam_seren", "純白聖靈賽蓮", "legendary"),
    ("fam_hilla", "真·希拉", "unique"),
    ("fam_kalos", "守護者卡羅斯", "legendary"),
]


def drop_stage_familiar(is_boss: bool = False, has_elite: bool = False) -> Familiar:
    """生成關卡掉落的野生萌獸 (普通/特殊)"""
    import uuid
    if is_boss or (has_elite and random.random() < 0.40):
        base_id, base_name = random.choice(STAGE_RARE_FAMILIARS)
        fid = f"{base_id}_{uuid.uuid4().hex[:6]}"
        return Familiar(fid, base_name, tier="rare", is_summoned=False)
    else:
        base_id, base_name = random.choice(STAGE_COMMON_FAMILIARS)
        fid = f"{base_id}_{uuid.uuid4().hex[:6]}"
        return Familiar(fid, base_name, tier="common", is_summoned=False)


