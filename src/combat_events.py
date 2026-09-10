"""Pure combat data payloads shared by the battle loop and presentation adapters."""


class PendingHit:
    """A delayed follow-up hit in a multi-hit combat sequence."""

    def __init__(self, delay, member, target_name, skill_name, damage, is_crit, vfx_type, vfx_color, target_monster_idx=None):
        self.delay = delay
        self.member = member
        self.target_name = target_name
        self.skill_name = skill_name
        self.damage = damage
        self.is_crit = is_crit
        self.vfx_type = vfx_type
        self.vfx_color = vfx_color
        self.target_monster_idx = target_monster_idx
