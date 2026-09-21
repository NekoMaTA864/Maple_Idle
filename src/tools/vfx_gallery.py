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
    QHBoxLayout,
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

    def queue_impact(self, effect, size, color, lifetime=0.30, **presentation):
        """Schedule a visual impact when a prototype effect reaches its target."""
        self.pending_impacts.append({
            "effect": effect,
            "size": float(size),
            "color": tuple(color),
            "lifetime": float(lifetime),
            "presentation": dict(presentation),
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
                    **sequence["presentation"],
                ))
            else:
                remaining.append(sequence)
        self.pending_impacts = remaining
        for popup in self.floating_popups:
            popup["life"] -= 1
            popup["offset_y"] -= 1.3
        self.floating_popups = [popup for popup in self.floating_popups if popup["life"] > 0]


GALLERY_CLASS_REGISTRY = (
    {
        "class_id": "hero",
        "class_label": "英雄",
        "avatar_id": "hero",
        "skills": (
            {"slot": 1, "skill_id": "hero_rage_attack", "skill_label": "狂暴攻擊", "preset": "hero_rage_attack", "trigger": "play_preset", "source_anchor": "tip", "target_anchor": "hit"},
            {"slot": 2, "skill_id": "hero_sword_illusion", "skill_label": "劍之幻象", "preset": "hero_sword_illusion", "trigger": "play_preset", "source_anchor": "tip", "target_anchor": "hit"},
            {"slot": 3, "skill_id": "hero_burning_soul_sword", "skill_label": "燃燒靈魂之劍", "preset": "hero_burning_soul_sword", "trigger": "play_preset", "source_anchor": "attack_origin", "target_anchor": "hit"},
            {"slot": 4, "skill_id": "hero_spatial_slash", "skill_label": "空間斬", "preset": "hero_spatial_slash", "trigger": "play_preset", "source_anchor": "tip", "target_anchor": "hit"},
            {"slot": 5, "skill_id": "hero_fighting_instinct", "skill_label": "鬥氣本能", "preset": "hero_fighting_instinct", "trigger": "play_preset", "source_anchor": "center", "target_anchor": "hit"},
            {"slot": 6, "skill_id": "hero_sacred_sword_descent", "skill_label": "聖劍降臨", "preset": "hero_sacred_sword_descent", "trigger": "play_preset", "source_anchor": "tip", "target_anchor": "hit"},
        ),
    },
    {
        "class_id": "night_lord",
        "class_label": "夜使者",
        "avatar_id": "night_lord",
        "skills": (
            {"slot": 1, "skill_id": "night_lord_shuriken", "skill_label": "手裏劍投擲", "preset": "night_lord_shuriken", "trigger": "play_preset", "source_anchor": "attack_origin", "target_anchor": "hit"},
        ),
    },
    {
        "class_id": "cannon",
        "class_label": "重砲指揮官",
        "avatar_id": "cannon",
        "skills": (
            {"slot": 1, "skill_id": "cannon_barrage", "skill_label": "加農砲連擊", "preset": "cannon_barrage", "trigger": "play_preset", "source_anchor": "muzzle", "target_anchor": "hit"},
            {"slot": 2, "skill_id": "monkey_assist", "skill_label": "輔助猴子", "preset": "monkey_assist", "trigger": "play_preset", "source_anchor": "attack_origin", "target_anchor": "hit"},
            {"slot": 3, "skill_id": "rolling_rainbow_cannon", "skill_label": "滾動彩虹加農砲", "preset": "rolling_rainbow_cannon", "trigger": "play_preset", "source_anchor": "attack_origin", "target_anchor": "hit"},
        ),
    },
    {
        "class_id": "bishop",
        "class_label": "主教",
        "avatar_id": "bishop",
        "skills": (
            {"slot": 1, "skill_id": "bishop_holy_area", "skill_label": "主教神聖領域", "preset": "bishop_holy_area", "trigger": "play_preset", "source_anchor": "tip", "target_anchor": "ground"},
        ),
    },
    {
        "class_id": "prototype",
        "class_label": "Prototype",
        "avatar_id": "hero",
        "skills": (
            {"slot": 1, "skill_id": "hero_slash", "skill_label": "舊版英雄斬擊", "preset": "hero_slash", "trigger": "play_preset", "source_anchor": "tip", "target_anchor": "hit"},
        ),
    },
)


NIGHT_LORD_SKILLS = (
    {"slot": 1, "skill_id": "night_lord_four_flying", "skill_label": "四飛閃", "preset": "night_lord_four_flying", "trigger": "play_preset", "source_anchor": "attack_origin", "target_anchor": "hit"},
    {"slot": 2, "skill_id": "night_lord_taunt_contract", "skill_label": "挑釁契約", "preset": "night_lord_taunt_contract", "trigger": "play_preset", "source_anchor": "attack_origin", "target_anchor": "hit"},
    {"slot": 3, "skill_id": "night_lord_fuma_shuriken", "skill_label": "風魔手裏劍", "preset": "night_lord_fuma_shuriken", "trigger": "play_preset", "source_anchor": "attack_origin", "target_anchor": "hit"},
    {"slot": 4, "skill_id": "night_lord_dakrus_secret", "skill_label": "達克魯的秘傳", "preset": "night_lord_dakrus_secret", "trigger": "play_preset", "source_anchor": "attack_origin", "target_anchor": "hit"},
    {"slot": 5, "skill_id": "night_lord_spread_throw", "skill_label": "散式投擲", "preset": "night_lord_spread_throw", "trigger": "play_preset", "source_anchor": "attack_origin", "target_anchor": "hit"},
    {"slot": 6, "skill_id": "night_lord_detonation_talisman", "skill_label": "飛閃起爆符", "preset": "night_lord_detonation_talisman", "trigger": "play_preset", "source_anchor": "attack_origin", "target_anchor": "hit"},
)


def _class_skills(class_definition):
    if class_definition["class_id"] == "night_lord":
        return NIGHT_LORD_SKILLS
    return class_definition["skills"]


def _flatten_gallery_registry():
    skills = []
    bindings = {}
    class_ids = {}
    labels = {}
    for class_definition in GALLERY_CLASS_REGISTRY:
        for skill in _class_skills(class_definition):
            preset = skill["preset"]
            skills.append((skill["skill_label"], preset))
            bindings[preset] = (
                class_definition["avatar_id"],
                skill["source_anchor"],
                skill["target_anchor"],
            )
            class_ids[preset] = class_definition["class_id"]
            labels[preset] = skill["skill_label"]
    return tuple(skills), bindings, class_ids, labels


GALLERY_PRESET_ORDER, GALLERY_PRESET_BINDINGS, GALLERY_PRESET_CLASS_IDS, GALLERY_PRESET_LABELS = _flatten_gallery_registry()


class VFXGalleryWindow(QMainWindow):
    # Legacy flat maps retained for compatibility; the canonical registry below overrides them.
    PRESET_ORDER = (
        ("狂暴攻擊", "hero_rage_attack"),
        ("劍之幻象", "hero_sword_illusion"),
        ("燃燒靈魂之劍", "hero_burning_soul_sword"),
        ("空間斬", "hero_spatial_slash"),
        ("鬥氣本能", "hero_fighting_instinct"),
        ("聖劍降臨", "hero_sacred_sword_descent"),
        ("四飛閃", "night_lord_four_flying"),
        ("挑釁契約", "night_lord_taunt_contract"),
        ("風魔手裏劍", "night_lord_fuma_shuriken"),
        ("達克魯的秘傳", "night_lord_dakrus_secret"),
        ("散式投擲", "night_lord_spread_throw"),
        ("飛閃起爆符", "night_lord_detonation_talisman"),
        ("舊版英雄斬擊", "hero_slash"),
        ("夜使者手裏劍", "night_lord_shuriken"),
        ("加農砲連擊", "cannon_barrage"),
        ("滾動彩虹加農砲", "rolling_rainbow_cannon"),
        ("主教神聖領域", "bishop_holy_area"),
    )
    PRESET_BINDINGS = {
        "hero_rage_attack": ("hero", "tip", "hit"),
        "hero_sword_illusion": ("hero", "tip", "hit"),
        "hero_burning_soul_sword": ("hero", "attack_origin", "hit"),
        "hero_spatial_slash": ("hero", "tip", "hit"),
        "hero_fighting_instinct": ("hero", "center", "hit"),
        "hero_sacred_sword_descent": ("hero", "tip", "hit"),
        "night_lord_four_flying": ("night_lord", "attack_origin", "hit"),
        "night_lord_taunt_contract": ("night_lord", "attack_origin", "hit"),
        "night_lord_fuma_shuriken": ("night_lord", "attack_origin", "hit"),
        "night_lord_dakrus_secret": ("night_lord", "attack_origin", "hit"),
        "night_lord_spread_throw": ("night_lord", "attack_origin", "hit"),
        "night_lord_detonation_talisman": ("night_lord", "attack_origin", "hit"),
        "hero_slash": ("hero", "tip", "hit"),
        "night_lord_shuriken": ("night_lord", "attack_origin", "hit"),
        "cannon_barrage": ("cannon", "muzzle", "hit"),
        "rolling_rainbow_cannon": ("cannon", "attack_origin", "hit"),
        "bishop_holy_area": ("bishop", "tip", "ground"),
    }
    # Canonical class-driven Gallery maps.
    CLASS_REGISTRY = GALLERY_CLASS_REGISTRY
    PRESET_ORDER = GALLERY_PRESET_ORDER
    PRESET_BINDINGS = GALLERY_PRESET_BINDINGS
    PRESET_CLASS_IDS = GALLERY_PRESET_CLASS_IDS
    PRESET_LABELS = GALLERY_PRESET_LABELS
    PRESET_ALIASES = {
        "cannonball_heavy": "cannon_barrage",
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
        self.current_class_id = "hero"
        self.current_preset = None
        self.current_variant = "normal"
        self.class_buttons = {}
        self.skill_buttons = []
        self.variant_buttons = {}
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

        class_bar = QHBoxLayout()
        for class_definition in self.CLASS_REGISTRY:
            class_id = class_definition["class_id"]
            button = QPushButton(class_definition["class_label"])
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, selected=class_id: self.select_class(selected))
            self.class_buttons[class_id] = button
            class_bar.addWidget(button)
        layout.addLayout(class_bar)

        self.skill_grid = QGridLayout()
        layout.addLayout(self.skill_grid)
        self._render_skill_buttons()

        self.variant_row = QHBoxLayout()
        self.variant_label = QLabel("空間斬變體")
        self.variant_label.setStyleSheet("color: #c4b5fd; font-size: 11px;")
        self.variant_row.addWidget(self.variant_label)
        for variant, label in (
            ("normal", "Normal"),
            ("empowered", "Empowered"),
            ("maximum", "Maximum"),
        ):
            button = QPushButton(label)
            button.setCheckable(True)
            button.clicked.connect(
                lambda _checked=False, selected=variant: self.play_preset(
                    "hero_spatial_slash", variant=selected
                )
            )
            self.variant_row.addWidget(button)
            self.variant_buttons[variant] = button
        layout.addLayout(self.variant_row)
        self._set_spatial_variant_controls(False)

        replay = QPushButton("重播")
        replay.clicked.connect(self.replay)
        layout.addWidget(replay)

        self.status_label = QLabel("僅限 Gallery：不使用存檔、成長資料或 CombatManager")
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(self.status_label)
        self.class_buttons["hero"].setChecked(True)

    def _class_definition(self, class_id):
        for class_definition in self.CLASS_REGISTRY:
            if class_definition["class_id"] == class_id:
                return class_definition
        raise KeyError(f"Unknown Gallery class: {class_id}")

    def _skill_definition(self, preset_name):
        preset_name = self.PRESET_ALIASES.get(preset_name, preset_name)
        for class_definition in self.CLASS_REGISTRY:
            for skill in _class_skills(class_definition):
                if skill["preset"] == preset_name:
                    return class_definition, skill
        raise KeyError(f"Unknown Gallery preset: {preset_name}")

    def _render_skill_buttons(self):
        while self.skill_grid.count():
            item = self.skill_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.skill_buttons = []
        class_definition = self._class_definition(self.current_class_id)
        for index, skill in enumerate(_class_skills(class_definition)):
            button = QPushButton(skill["skill_label"])
            button.clicked.connect(
                lambda _checked=False, preset=skill["preset"]: self.play_preset(preset)
            )
            self.skill_grid.addWidget(button, index // 3, index % 3)
            self.skill_buttons.append(button)

    def _set_spatial_variant_controls(self, visible, selected="normal"):
        self.variant_label.setVisible(visible)
        for variant, button in self.variant_buttons.items():
            button.setVisible(visible)
            button.setChecked(visible and variant == selected)

    def select_class(self, class_id):
        class_definition = self._class_definition(class_id)
        self.current_class_id = class_id
        self.current_preset = None
        self.current_variant = "normal"
        self.state.clear_presentation()
        self.arena.set_combat_avatar(class_definition["avatar_id"])
        self._set_spatial_variant_controls(False)
        for button_id, button in self.class_buttons.items():
            button.setChecked(button_id == class_id)
        self._render_skill_buttons()
        if hasattr(self, "status_label"):
            self.status_label.setText(
                f"目前職業：{class_definition['class_label']}｜僅限視覺展示，不建立 CombatManager"
            )

    def _scene_points(self):
        scene = ArenaLayout(self.arena.width(), self.arena.height())
        return scene.player_position(), scene.enemy_anchor("hit", index=1, total=3)

    def play_preset(self, preset_name, variant=None):
        preset_name = self.PRESET_ALIASES.get(preset_name, preset_name)
        class_definition, skill = self._skill_definition(preset_name)
        if self.current_class_id != class_definition["class_id"]:
            self.select_class(class_definition["class_id"])
        definition = resolve_preset(preset_name)
        self.current_preset = preset_name
        selected_variant = str(variant or "normal")
        self.current_variant = selected_variant if preset_name == "hero_spatial_slash" else "normal"
        self._set_spatial_variant_controls(
            preset_name == "hero_spatial_slash",
            self.current_variant,
        )
        self.state.clear_presentation()
        self.arena.set_combat_avatar(class_definition["avatar_id"])
        self.arena.trigger_avatar_attack()
        source = self.arena.avatar_anchor(skill["source_anchor"])
        target = self.arena.enemy_anchor(skill["target_anchor"], index=1, total=3)

        effects = []
        if preset_name == "hero_sword_illusion":
            # The delayed copies are thin residual blade marks, not three more
            # copies of the primary curved sword arc.
            main = emit_vfx(self.state.vfx_mgr, definition, source, target)
            effects.append(main)
            for index, (delay, size, alpha_scale, angle) in enumerate(
                ((0.15, 88.0, 0.36, -112.0), (0.28, 80.0, 0.25, -68.0)), start=1
            ):
                offset = (-18.0, -6.0) if index == 1 else (18.0, -12.0)
                effects.append(emit_vfx(
                    self.state.vfx_mgr,
                    definition,
                    source,
                    target,
                    delay=delay,
                    size=size,
                    alpha_scale=alpha_scale,
                    style="phantom",
                    angle=angle,
                    offset=offset,
                    seed=int(definition.params["seed"]) + index,
                ))
            self._add_delayed_impact(
                target, 30, (130, 183, 255), 0.30, 700, 0.38,
                ring=False, style="angular_shard",
            )
        elif preset_name == "hero_burning_soul_sword":
            # Ignition, retained sword, and one optional-looking flame trail
            # are all presentation effects with independent lifecycles.
            ignition = ImpactEffect(
                source, size=38, lifetime=0.46, color=(255, 142, 55), seed=2107,
                ring=False,
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
            self._add_delayed_impact(
                target, 20, (255, 145, 64), 0.16, 2108 + 700, 0.33,
                ring=False,
            )
        elif preset_name == "hero_fighting_instinct":
            burst = ImpactEffect(
                source, size=52, lifetime=0.42, color=(116, 228, 255), seed=2109,
                ring=False, style="angular_shard",
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
            ground = self.arena.enemy_anchor("ground", index=1, total=3)
            self._add_delayed_impact(
                ground, 68, (167, 225, 255), 0.30, 2110, 0.40,
                ring=False, style="ground_crack",
            )
        elif preset_name == "hero_spatial_slash":
            spatial_profiles = {
                "normal": (0.52, 52, 0.30, 0.31, 5),
                "empowered": (0.60, 62, 0.34, 0.26, 7),
                "maximum": (0.68, 74, 0.40, 0.20, 10),
            }
            spatial_lifetime, impact_size, impact_lifetime, impact_delay, shard_count = spatial_profiles.get(
                self.current_variant, spatial_profiles["normal"]
            )
            spatial = emit_vfx(
                self.state.vfx_mgr,
                definition,
                source,
                target,
                variant=self.current_variant,
                lifetime=spatial_lifetime,
            )
            effects.append(spatial)
            self._add_delayed_impact(
                target, impact_size, (126, 94, 205), impact_lifetime, 2111,
                impact_delay, ring=False, style="angular_shard", shard_count=shard_count,
            )
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
        elif preset_name == "night_lord_four_flying":
            # Four short, tightly spaced throws are one presentation sequence.
            # They do not expose hit-count or any gameplay multi-hit state.
            for index in range(4):
                effect = emit_vfx(
                    self.state.vfx_mgr,
                    definition,
                    source,
                    target,
                    delay=index * 0.055,
                    seed=int(definition.params["seed"]) + index,
                )
                effects.append(effect)
                self.state.queue_impact(
                    effect, size=13, color=(205, 168, 255), lifetime=0.16
                )
        elif preset_name == "night_lord_taunt_contract":
            # The mark is a pressure/debuff read only; it does not create a
            # debuff object or any gameplay state.
            effects.append(emit_vfx(self.state.vfx_mgr, definition, source, target))
        elif preset_name == "night_lord_fuma_shuriken":
            effect = emit_vfx(self.state.vfx_mgr, definition, source, target)
            effects.append(effect)
            self.state.queue_impact(
                effect,
                size=64,
                color=(218, 181, 255),
                lifetime=0.36,
                flash=False,
                ring=False,
                burst=False,
                style="angular_shard",
                shard_count=7,
            )
        elif preset_name == "night_lord_dakrus_secret":
            # The main throw starts at the attack anchor. Two thin shadow
            # routes enter from offset sources and cross toward offset target
            # points, making the skill read as secret path technique rather
            # than delayed copies of one projectile.
            main = emit_vfx(self.state.vfx_mgr, definition, source, target)
            effects.append(main)
            dx = target[0] - source[0]
            dy = target[1] - source[1]
            distance = max(1.0, (dx * dx + dy * dy) ** 0.5)
            normal = (-dy / distance, dx / distance)
            for index, (delay, offset, size, alpha_scale) in enumerate(
                ((0.045, -26.0, 16.0, 0.40), (0.090, 26.0, 13.0, 0.26)), start=1
            ):
                shadow_source = (
                    source[0] + normal[0] * offset,
                    source[1] + normal[1] * offset,
                )
                shadow_target = (
                    target[0] - normal[0] * offset * 0.55,
                    target[1] - normal[1] * offset * 0.55,
                )
                effects.append(emit_vfx(
                    self.state.vfx_mgr,
                    definition, shadow_source,
                    shadow_target,
                    delay=delay,
                    size=size,
                    alpha_scale=alpha_scale,
                    seed=int(definition.params["seed"]) + index,
                ))
            self.state.queue_impact(
                main,
                size=50,
                color=(168, 128, 235),
                lifetime=0.30,
                flash=False,
                ring=False,
                burst=False,
                style="cross_cut",
            )
        elif preset_name == "night_lord_spread_throw":
            effect = emit_vfx(self.state.vfx_mgr, definition, source, target)
            effects.append(effect)
            self.state.queue_impact(
                effect,
                size=48,
                color=(200, 164, 255),
                lifetime=0.30,
                flash=False,
                ring=False,
                burst=False,
                style="fan_cut",
                shard_count=5,
            )
        elif preset_name == "night_lord_detonation_talisman":
            # MarkDetonationEffect owns the mark -> delay -> detonation visual
            # timeline; the gallery does not create a gameplay debuff/timer.
            effects.append(emit_vfx(self.state.vfx_mgr, definition, source, target))
        elif preset_name == "cannon_barrage":
            effect = emit_vfx(self.state.vfx_mgr, definition, source, target)
            effects.append(effect)
            self.state.queue_impact(effect, size=50, color=(255, 155, 74), lifetime=0.38)
        elif preset_name == "hero_rage_attack":
            effect = emit_vfx(self.state.vfx_mgr, definition, source, target)
            effects.append(effect)
            self._add_delayed_impact(
                target, 24, (255, 225, 130), 0.22, 2112, 0.38,
                ring=False, burst=False, style="angular_shard", shard_count=3,
            )
        elif preset_name == "hero_slash":
            effect = emit_vfx(self.state.vfx_mgr, definition, source, target)
            effects.append(effect)
            self._add_delayed_impact(
                target, 30, (255, 225, 130), 0.26, 2112, 0.55,
            )
        else:
            # Area presets resolve their visual center from the enemy ground
            # target; source remains the avatar cast anchor for the request.
            effects.append(emit_vfx(self.state.vfx_mgr, definition, source, target))

        effect = effects[-1]
        slot_index = (int(skill["slot"]) - 1) % len(self.arena.skill_slots)
        self.arena.set_skill_label(slot_index, f"S{slot_index + 1}")
        display_name = skill["skill_label"]
        primitive_names = {
            "slash": "斬擊",
            "projectile": "投射物",
            "spread": "扇形投射",
            "mark": "符咒／起爆",
            "area": "地面範圍",
            "persistent": "持續效果",
        }
        self.state.add_popup(display_name)
        self.status_label.setText(
            f"目前效果：{display_name}｜類型：{primitive_names.get(definition.effect_type, definition.effect_type)}｜"
            "僅限視覺展示"
        )

    def _add_delayed_impact(self, target, size, color, lifetime, seed, delay=0.0, **kwargs):
        """Add an impact with the formal effect lifecycle, not a skill timer."""
        self.state.vfx_mgr.add_effect(ImpactEffect(
            target,
            size=size,
            color=color,
            lifetime=lifetime,
            seed=seed,
            delay=delay,
            **kwargs,
        ))

    def replay(self):
        if self.current_preset:
            self.play_preset(self.current_preset, variant=self.current_variant)

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
