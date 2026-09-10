"""
《新楓之谷：放置遠征隊》戰鬥視覺特效與多段打擊隊列 (combat_vfx_manager.py)
"""
import math
import random

class VisualEffect:
    def __init__(self, kind, x, y, target_x=None, target_y=None, color=(255, 255, 255), duration=0.45,
                 source_slot=None, target_monster_idx=None, target_slot=None):
        self.kind = kind
        self.x = float(x)
        self.y = float(y)
        self.target_x = float(target_x if target_x is not None else x)
        self.target_y = float(target_y if target_y is not None else y)
        self.color = color
        self.duration = duration
        self.timer = duration
        self.seed = random.uniform(0, 6.28)
        self.source_slot = source_slot
        self.target_monster_idx = target_monster_idx
        self.target_slot = target_slot
        self.fracture_lines = []
        if self.kind == "dimension_rift":
            for _ in range(6):
                angle = random.uniform(0, math.pi * 2)
                length = random.uniform(50, 110)
                mid_len = length * 0.5
                mid_ang = angle + random.uniform(-0.4, 0.4)
                p_start = (self.target_x, self.target_y)
                p_mid = (self.target_x + math.cos(mid_ang) * mid_len, self.target_y + math.sin(mid_ang) * mid_len)
                p_end = (self.target_x + math.cos(angle) * length, self.target_y + math.sin(angle) * length)
                self.fracture_lines.append((p_start, p_mid, p_end))

    @property
    def progress(self):
        return max(0.0, min(1.0, 1.0 - (self.timer / self.duration)))

    @property
    def is_alive(self):
        return self.timer > 0

    def update(self, dt):
        self.timer -= dt


# 核心大招與全域視覺特效集合（享有最高保留優先權）
HIGH_PRIORITY_VFX = {
    "holy", "aoe_beam", "dimension_rift", "dark_genesis_thunder",
    "screen_ultimate", "team_buff", "sanctuary_ray", "inferno_tempest"
}


def _get_vfx_priority(eff: VisualEffect) -> float:
    """計算特效保留優先權評分（分數越低越優先剔除）"""
    p = eff.progress
    # 播放進度已逾 70% 的特效即將淡出，優先淘汰
    progress_weight = 0.15 if p > 0.70 else (1.0 - p * 0.6)
    # 高階大招與全屏技能享有更高保護加權
    kind_weight = 3.5 if eff.kind in HIGH_PRIORITY_VFX else 1.0
    return progress_weight * kind_weight


class VisualEffectManager:
    MAX_CONCURRENT_EFFECTS = 18

    def __init__(self):
        self.effects = []
        self.total_dropped_effects = 0

    def add_vfx(self, kind, x, y, target_x=None, target_y=None, color=(255, 255, 255), duration=0.45,
                source_slot=None, target_monster_idx=None, target_slot=None):
        if len(self.effects) >= self.MAX_CONCURRENT_EFFECTS:
            # 依優先權剔除最低評分特效，避免多隊員同發大招時卡頓
            lowest_eff = min(self.effects, key=_get_vfx_priority)
            self.effects.remove(lowest_eff)
            self.total_dropped_effects += 1

        self.effects.append(VisualEffect(kind, x, y, target_x, target_y, color, duration,
                                         source_slot=source_slot, target_monster_idx=target_monster_idx, target_slot=target_slot))

    def update(self, dt):
        for eff in self.effects:
            eff.update(dt)
        self.effects = [e for e in self.effects if e.is_alive]


# =========================================================================
# 多段連擊隊列 (PendingHit)
# =========================================================================
class PendingHit:
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


