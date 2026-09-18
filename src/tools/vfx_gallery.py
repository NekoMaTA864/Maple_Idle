"""Standalone Debug Gallery for the vertical battle VFX prototype.

The gallery owns only dummy presentation state.  It deliberately uses the
formal ``CombatArenaWidget`` and the shared ``VisualEffectManager`` rather
than maintaining a second renderer or a real CombatManager battle.
"""

import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from arena_layout import ArenaLayout
from combat_vfx_manager import VisualEffectManager
from ui_arena import CombatArenaWidget
from vfx_prototype import (
    ImpactEffect,
    PRESETS,
    ProjectileEffect,
    emit_vfx,
    resolve_preset,
)


class GalleryMember:
    """Small player-shaped view model with no save/progression behavior."""

    name = "Prototype Player"
    slot_idx = 0
    current_hp = 1000
    max_hp = 1000
    shield = 0
    is_alive = True

    def get_max_hp(self, player):
        return self.max_hp


class GalleryPlayer:
    def __init__(self):
        self.team = [GalleryMember()]
        self.team_buffs = {}

    def get_total_arc(self):
        return 0

    def get_total_aut(self):
        return 0


class GalleryMonster:
    def __init__(self, name, is_boss=False):
        self.name = name
        self.lvl = 260 if is_boss else 255
        self.is_boss = is_boss
        self.is_elite = False
        self.max_hp = 100000 if is_boss else 50000
        self.hp = self.max_hp
        self.is_alive = True


class GalleryCombatState:
    """The minimum read-only shape required by ``CombatArenaWidget``."""

    def __init__(self):
        self.player = GalleryPlayer()
        self.monsters = [
            GalleryMonster("Training Shade"),
            GalleryMonster("VFX Prototype Boss", is_boss=True),
            GalleryMonster("Training Shade"),
        ]
        self.vfx_mgr = VisualEffectManager()
        self.floating_popups = []
        self.pending_impacts = []
        self.current_floor = 1
        self.max_floors = 1
        self.repeat_current_zone = False

    @property
    def monster(self):
        return self.monsters[0]

    def get_current_zone(self):
        return {"name": "Vertical VFX Prototype", "arc_req": 0, "aut_req": 0}

    def add_popup(self, text, target="monster_1", color=(255, 240, 180)):
        self.floating_popups.append({
            "text": text,
            "target": target,
            "color": color,
            "is_crit": False,
            "is_skill": True,
            "life": 40,
            "max_life": 40,
            "offset_y": -8,
            "offset_x": 0,
        })

    def clear_presentation(self):
        self.vfx_mgr.clear()
        self.floating_popups.clear()
        self.pending_impacts.clear()

    def queue_impact(self, effect, size, color, lifetime=0.30):
        """Schedule a visual impact when a prototype effect reaches its target."""
        self.pending_impacts.append({
            "effect": effect,
            "size": float(size),
            "color": tuple(color),
            "lifetime": float(lifetime),
        })

    def update_presentation(self, dt):
        self.vfx_mgr.update(dt)
        remaining = []
        for sequence in self.pending_impacts:
            effect = sequence["effect"]
            if effect.progress >= 1.0:
                self.vfx_mgr.add_effect(ImpactEffect(
                    effect.target,
                    size=sequence["size"],
                    lifetime=sequence["lifetime"],
                    color=sequence["color"],
                    seed=getattr(effect, "seed", 505) + 700,
                ))
            else:
                remaining.append(sequence)
        self.pending_impacts = remaining
        for popup in self.floating_popups:
            popup["life"] -= 1
            popup["offset_y"] -= 1.3
        self.floating_popups = [popup for popup in self.floating_popups if popup["life"] > 0]


class VFXGalleryWindow(QMainWindow):
    PRESET_ORDER = (
        ("狂暴攻擊", "hero_rage_attack"),
        ("劍之幻象", "hero_sword_illusion"),
        ("燃燒靈魂之劍", "hero_burning_soul_sword"),
        ("空間斬", "hero_spatial_slash"),
        ("鬥氣本能", "hero_fighting_instinct"),
        ("聖劍降臨", "hero_sacred_sword_descent"),
        ("舊版英雄斬擊", "hero_slash"),
        ("夜使者手裏劍", "night_lord_shuriken"),
        ("重型加農砲彈", "cannonball_heavy"),
        ("主教神聖領域", "bishop_holy_area"),
    )
    PRESET_BINDINGS = {
        "hero_rage_attack": ("hero", "tip", "hit"),
        "hero_sword_illusion": ("hero", "tip", "hit"),
        "hero_burning_soul_sword": ("hero", "attack_origin", "hit"),
        "hero_spatial_slash": ("hero", "tip", "hit"),
        "hero_fighting_instinct": ("hero", "center", "hit"),
        "hero_sacred_sword_descent": ("hero", "tip", "hit"),
        "hero_slash": ("hero", "tip", "hit"),
        "night_lord_shuriken": ("night_lord", "attack_origin", "hit"),
        "cannonball_heavy": ("cannon", "muzzle", "hit"),
        "bishop_holy_area": ("bishop", "tip", "ground"),
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MapleIdle｜VFX 視覺檢視 Gallery")
        self.resize(760, 760)
        self.setMinimumSize(680, 650)
        self.setStyleSheet(
            "QMainWindow, QWidget { background: #0d111a; color: #e2e8f0; }"
            "QPushButton { background: #1e293b; border: 1px solid #475569;"
            " border-radius: 6px; padding: 8px 12px; color: #f8fafc; }"
            "QPushButton:hover { background: #263a5b; border-color: #60a5fa; }"
        )
        self.state = GalleryCombatState()
        self.arena = CombatArenaWidget(self.state, self)
        self.current_preset = None
        self._last_tick = time.monotonic()
        self._build_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)
        QTimer.singleShot(0, lambda: self.play_preset("hero_slash"))

    def _build_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        heading = QLabel(
            "<b style='font-size: 16px; color: #ffd75a;'>垂直戰場 VFX 視覺檢視</b>"
            "<br><span style='color: #94a3b8;'>敵人／Boss 上方 → 戰鬥區域 → 玩家下方</span>"
        )
        layout.addWidget(heading)
        layout.addWidget(self.arena, 1)

        button_grid = QGridLayout()
        for index, (label, preset) in enumerate(self.PRESET_ORDER):
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, name=preset: self.play_preset(name))
            button_grid.addWidget(button, index // 3, index % 3)
        layout.addLayout(button_grid)

        replay = QPushButton("重播")
        replay.clicked.connect(self.replay)
        layout.addWidget(replay)

        self.status_label = QLabel("僅限 Gallery：不使用存檔、成長資料或 CombatManager")
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(self.status_label)

    def _scene_points(self):
        scene = ArenaLayout(self.arena.width(), self.arena.height())
        return scene.player_position(), scene.enemy_anchor("hit", index=1, total=3)

    def play_preset(self, preset_name):
        definition = resolve_preset(preset_name)
        self.current_preset = preset_name
        self.state.clear_presentation()
        avatar_id, source_anchor, target_anchor = self.PRESET_BINDINGS[preset_name]
        self.arena.set_combat_avatar(avatar_id)
        self.arena.trigger_avatar_attack()
        source = self.arena.avatar_anchor(source_anchor)
        target = self.arena.enemy_anchor(target_anchor, index=1, total=3)

        effects = []
        if preset_name == "hero_sword_illusion":
            # The delayed copies are separate presentation effects.  Their
            # timing proves the phantom read without a combo counter or hit
            # count in the gallery.
            main = emit_vfx(self.state.vfx_mgr, definition, source, target)
            effects.append(main)
            for index, (delay, size, alpha_scale) in enumerate(
                ((0.13, 98.0, 0.48), (0.26, 92.0, 0.38)), start=1
            ):
                effects.append(emit_vfx(
                    self.state.vfx_mgr,
                    definition,
                    source,
                    target,
                    delay=delay,
                    size=size,
                    alpha_scale=alpha_scale,
                    seed=int(definition.params["seed"]) + index,
                ))
            self._add_delayed_impact(target, 34, (130, 183, 255), 0.38, 700, 0.38)
        elif preset_name == "hero_burning_soul_sword":
            # Ignition, retained sword, and one optional-looking flame trail
            # are all presentation effects with independent lifecycles.
            ignition = ImpactEffect(
                source, size=38, lifetime=0.46, color=(255, 142, 55), seed=2107
            )
            self.state.vfx_mgr.add_effect(ignition)
            effects.append(ignition)
            persistent = emit_vfx(
                self.state.vfx_mgr,
                definition,
                self.arena.avatar_anchor("center"),
                offset=(self.arena.width() * 0.15, -self.arena.height() * 0.018),
            )
            effects.append(persistent)
            soul_source = self.arena.avatar_anchor("center")
            soul_source = (
                soul_source[0] + self.arena.width() * 0.15,
                soul_source[1] - self.arena.height() * 0.018,
            )
            followup = ProjectileEffect(
                soul_source,
                target,
                lifetime=0.27,
                delay=0.10,
                speed=720.0,
                size=18.0,
                trail=True,
                trail_length=0.18,
                shape="sword",
                color=(255, 159, 64),
                seed=2108,
            )
            self.state.vfx_mgr.add_effect(followup)
            effects.append(followup)
            self._add_delayed_impact(target, 20, (255, 145, 64), 0.16, 2108 + 700, 0.33)
        elif preset_name == "hero_fighting_instinct":
            burst = ImpactEffect(
                source, size=52, lifetime=0.42, color=(116, 228, 255), seed=2109
            )
            self.state.vfx_mgr.add_effect(burst)
            effects.append(burst)
            effects.append(emit_vfx(
                self.state.vfx_mgr,
                definition,
                self.arena.avatar_anchor("center"),
                size=min(self.arena.width() * 0.12, 96.0),
            ))
        elif preset_name == "hero_sacred_sword_descent":
            # The source is derived from the target and arena size so the
            # blade remains a vertical descent at every gallery resolution.
            descent_source = (target[0], target[1] - self.arena.height() * 0.15)
            descent = emit_vfx(self.state.vfx_mgr, definition, descent_source, target)
            effects.append(descent)
            self._add_delayed_impact(target, 62, (167, 225, 255), 0.22, 2110, 0.40)
        elif preset_name == "hero_spatial_slash":
            spatial = emit_vfx(self.state.vfx_mgr, definition, source, target)
            effects.append(spatial)
            self._add_delayed_impact(target, 52, (105, 204, 255), 0.30, 2111, 0.31)
        elif preset_name == "night_lord_shuriken":
            # Three presentation-only throws prove the rapid-fire read without
            # introducing hit-count or multi-hit gameplay semantics.
            for index in range(3):
                effect = emit_vfx(
                    self.state.vfx_mgr, definition, source, target,
                    delay=index * 0.07,
                    seed=int(definition.params["seed"]) + index,
                )
                effects.append(effect)
                self.state.queue_impact(effect, size=16, color=(214, 182, 255), lifetime=0.22)
        elif preset_name == "cannonball_heavy":
            effect = emit_vfx(self.state.vfx_mgr, definition, source, target)
            effects.append(effect)
            self.state.queue_impact(effect, size=50, color=(255, 155, 74), lifetime=0.38)
        elif preset_name in ("hero_slash", "hero_rage_attack"):
            effect = emit_vfx(self.state.vfx_mgr, definition, source, target)
            effects.append(effect)
            self._add_delayed_impact(target, 30, (255, 225, 130), 0.26, 2112, 0.55)
        else:
            # Area presets resolve their visual center from the enemy ground
            # target; source remains the avatar cast anchor for the request.
            effects.append(emit_vfx(self.state.vfx_mgr, definition, source, target))

        effect = effects[-1]
        slot_index = [name for _label, name in self.PRESET_ORDER].index(preset_name)
        self.arena.set_skill_label(slot_index, f"S{slot_index + 1}")
        display_name = dict((preset, label) for label, preset in self.PRESET_ORDER)[preset_name]
        primitive_names = {
            "slash": "斬擊",
            "projectile": "投射物",
            "area": "地面範圍",
            "persistent": "持續效果",
        }
        self.state.add_popup(display_name)
        self.status_label.setText(
            f"目前效果：{display_name}｜類型：{primitive_names.get(definition.effect_type, definition.effect_type)}｜"
            "僅限視覺展示"
        )

    def _add_delayed_impact(self, target, size, color, lifetime, seed, delay=0.0):
        """Add an impact with the formal effect lifecycle, not a skill timer."""
        self.state.vfx_mgr.add_effect(ImpactEffect(
            target,
            size=size,
            color=color,
            lifetime=lifetime,
            seed=seed,
            delay=delay,
        ))

    def replay(self):
        if self.current_preset:
            self.play_preset(self.current_preset)

    def _tick(self):
        now = time.monotonic()
        dt = min(0.1, max(0.0, now - self._last_tick))
        self._last_tick = now
        self.state.update_presentation(dt)
        self.arena.update_vfx_timer(dt)
        self.arena.update()

    def closeEvent(self, event):
        self.timer.stop()
        self.state.clear_presentation()
        event.accept()


def main():
    app = QApplication.instance() or QApplication([])
    window = VFXGalleryWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
