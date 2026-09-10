"""目前戰鬥週期的輸出、生存與輔助統計。"""

from dataclasses import dataclass, field


@dataclass
class MemberCombatStats:
    damage_dealt: int = 0
    attack_count: int = 0
    skill_cast_count: int = 0
    critical_count: int = 0
    highest_hit: int = 0
    damage_taken: int = 0
    deaths: int = 0
    healing_done: int = 0
    heal_cast_count: int = 0
    shield_granted: int = 0
    shield_absorbed: int = 0
    buff_cast_count: int = 0
    control_trigger_count: int = 0
    hit_lines: int = 0
    skill_damage: dict[str, int] = field(default_factory=dict)
    skill_casts: dict[str, int] = field(default_factory=dict)


@dataclass
class CombatStats:
    member_count: int
    elapsed_seconds: float = 0.0
    members: dict[int, MemberCombatStats] = field(default_factory=dict)

    def __post_init__(self):
        self.reset()

    def reset(self):
        self.elapsed_seconds = 0.0
        self.members = {idx: MemberCombatStats() for idx in range(self.member_count)}

    def tick(self, dt):
        self.elapsed_seconds += max(0.0, float(dt))

    def for_member(self, slot_idx):
        if slot_idx not in self.members:
            self.members[slot_idx] = MemberCombatStats()
        return self.members[slot_idx]

    def record_attack(self, slot_idx, skill=None):
        stats = self.for_member(slot_idx)
        stats.attack_count += 1
        if skill is not None:
            stats.skill_cast_count += 1
            s_name = getattr(skill, "name", str(skill))
            stats.skill_casts[s_name] = stats.skill_casts.get(s_name, 0) + 1
        else:
            stats.skill_casts["普攻"] = stats.skill_casts.get("普攻", 0) + 1

    def record_damage(self, slot_idx, amount, is_critical=False, skill_name=None):
        amount = max(0, int(amount))
        stats = self.for_member(slot_idx)
        stats.damage_dealt += amount
        stats.hit_lines += 1
        stats.highest_hit = max(stats.highest_hit, amount)
        if is_critical:
            stats.critical_count += 1
        if skill_name:
            stats.skill_damage[skill_name] = stats.skill_damage.get(skill_name, 0) + amount
        else:
            stats.skill_damage["普攻"] = stats.skill_damage.get("普攻", 0) + amount

    def record_damage_taken(self, slot_idx, amount, absorbed=0):
        stats = self.for_member(slot_idx)
        stats.damage_taken += max(0, int(amount))
        stats.shield_absorbed += max(0, int(absorbed))

    def record_death(self, slot_idx):
        self.for_member(slot_idx).deaths += 1

    def record_healing(self, slot_idx, amount, cast=False):
        stats = self.for_member(slot_idx)
        stats.healing_done += max(0, int(amount))
        if cast:
            stats.heal_cast_count += 1

    def record_shield(self, slot_idx, amount):
        self.for_member(slot_idx).shield_granted += max(0, int(amount))

    def record_buff(self, slot_idx):
        self.for_member(slot_idx).buff_cast_count += 1

    def record_control(self, slot_idx):
        self.for_member(slot_idx).control_trigger_count += 1

    @property
    def total_damage(self):
        return sum(stats.damage_dealt for stats in self.members.values())

    @property
    def team_dps(self):
        return self.total_damage / max(self.elapsed_seconds, 1.0)

    def member_dps(self, slot_idx):
        return self.for_member(slot_idx).damage_dealt / max(self.elapsed_seconds, 1.0)
