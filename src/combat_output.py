"""Immediate presentation adapter used by the combat loop.

It owns VFX, popup, log, and shake presentation state while keeping every output
synchronous.  It does not buffer output, change RNG ownership, or model combat
events.
"""

from combat_vfx_manager import VisualEffectManager, sample_visual_variation


class GameplayCombatOutput:
    """Own and update the existing gameplay presentation state synchronously."""

    def __init__(self, vfx_mgr=None, team_size=0, max_logs=120):
        self.vfx_mgr = vfx_mgr if vfx_mgr is not None else VisualEffectManager()
        self.floating_popups = []
        self.combat_logs = []
        self.max_logs = max_logs
        self.shake_team = [0.0] * team_size
        self.shake_monster = 0.0

    def vfx(self, *args, **kwargs):
        return self.vfx_mgr.add_vfx(*args, **kwargs)

    def play_sound(self, sound_mgr, cue):
        return sound_mgr.play(cue)

    def add_popup(self, text, target, color, is_crit, is_skill, offset_x):
        life = 40 if is_crit or is_skill else 28
        self.floating_popups.append({
            "text": text,
            "target": target,
            "color": color,
            "is_crit": is_crit,
            "is_skill": is_skill,
            "life": life,
            "max_life": life,
            "offset_y": -8,
            "offset_x": offset_x,
        })

    def add_log(self, timestamp, text, color):
        self.combat_logs.append({
            "time": timestamp,
            "text": text,
            "color": color,
        })
        if len(self.combat_logs) > self.max_logs:
            self.combat_logs.pop(0)

    def set_shake(self, target, value, index=None):
        if target == "monster":
            self.shake_monster = value
        elif target == "team":
            self.shake_team[index] = value
        else:
            raise ValueError(f"Unknown shake target: {target}")

    def update(self, dt):
        self.vfx_mgr.update(dt)

        for index in range(len(self.shake_team)):
            if self.shake_team[index] > 0:
                self.shake_team[index] = max(0.0, self.shake_team[index] - 30.0 * dt)
        if self.shake_monster > 0:
            self.shake_monster = max(0.0, self.shake_monster - 30.0 * dt)

        for popup in self.floating_popups:
            popup["life"] -= 1
            popup["offset_y"] -= 1.3
        self.floating_popups = [popup for popup in self.floating_popups if popup["life"] > 0]


class SilentCombatOutput:
    """Consume required RNG while discarding all presentation output and state."""

    __slots__ = ()

    def vfx(self, kind, *args, **kwargs):
        sample_visual_variation(kind)

    def play_sound(self, sound_mgr, cue):
        return None

    def add_popup(self, text, target, color, is_crit, is_skill, offset_x):
        return None

    def add_log(self, timestamp, text, color):
        return None

    def set_shake(self, target, value, index=None):
        return None

    def update(self, dt):
        return None
