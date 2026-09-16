"""The standalone vertical combat visual sandbox widget and orchestration."""

import math

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


MODE_MANUAL = "MANUAL"
MODE_AUTO_PRIORITY = "AUTO_PRIORITY"
MODE_AUTO_SEQUENCE = "AUTO_SEQUENCE"
MODE_LABELS = {
    MODE_MANUAL: "MANUAL",
    MODE_AUTO_PRIORITY: "AUTO  ·  PRIORITY",
    MODE_AUTO_SEQUENCE: "AUTO  ·  SEQUENCE",
}


try:
    from .avatars import AVATAR_NAMES, AvatarRenderer, draw_debug_anchors
    from .auto_policy import select_auto_priority_skill
    from .combat_presentation import draw_runtime_presentation
    from .combat_rules import (
        BURNING_SOUL,
        FIGHTING_INSTINCT,
        RAGE_ORBS,
        apply_skill_runtime_effects,
        create_runtime_state,
        resolve_post_cast_events,
        resolve_skill_variant,
    )
    from .combat_runtime import CombatRuntimeState
    from .fonts import ui_font
    from .skills import (
        create_effect,
        create_presentation_effect,
        draw_skill_effect,
        loadout_presets,
        loadout_specs_for_avatar,
        prototype_id_for_avatar,
        skill_pool_for_avatar,
    )
    from .vfx import EffectState, cannon_recoil
except ImportError:  # Direct ``py visual_sandbox/main.py`` execution.
    from avatars import AVATAR_NAMES, AvatarRenderer, draw_debug_anchors
    from auto_policy import select_auto_priority_skill
    from combat_presentation import draw_runtime_presentation
    from combat_rules import (
        BURNING_SOUL,
        FIGHTING_INSTINCT,
        RAGE_ORBS,
        apply_skill_runtime_effects,
        create_runtime_state,
        resolve_post_cast_events,
        resolve_skill_variant,
    )
    from combat_runtime import CombatRuntimeState
    from fonts import ui_font
    from skills import (
        create_effect,
        create_presentation_effect,
        draw_skill_effect,
        loadout_presets,
        loadout_specs_for_avatar,
        prototype_id_for_avatar,
        skill_pool_for_avatar,
    )
    from vfx import EffectState, cannon_recoil


class CombatVisualSandbox(QWidget):
    """A resize-aware, vertical combat-screen composition mockup."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MapleIdle - Combat Visual Sandbox")
        self.setMinimumSize(420, 680)
        self.resize(540, 880)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.avatar_index = 0
        self.show_debug_anchors = False
        self.idle_phase = 0.0
        self.current_anchors: dict[str, QPointF] = {}
        self.active_effects: list[EffectState] = []
        self.skill_flash = 0.0
        self.active_skill_slot: int | None = None
        self.active_skill_name = ""
        self.active_skill_variant = ""
        self.control_mode = MODE_MANUAL
        self.auto_action_interval = 0.30
        self.auto_action_remaining = 0.0
        self.current_loadout_preset: dict[str, str] = {
            prototype_id: next(iter(presets))
            for prototype_id, presets in loadout_presets.items()
        }
        self.sequence_cursors: dict[str, int] = {
            prototype_id_for_avatar(avatar_index): 0
            for avatar_index in range(len(AVATAR_NAMES))
        }
        self.runtime_states: dict[str, CombatRuntimeState] = {
            prototype_id_for_avatar(avatar_index): create_runtime_state(prototype_id_for_avatar(avatar_index))
            for avatar_index in range(len(AVATAR_NAMES))
        }
        self.runtime_state = self.runtime_states[prototype_id_for_avatar(self.avatar_index)]
        # Presentation-only cooldowns keyed by stable skill id.  Skill ids
        # are unique across the four prototype pools, so switching avatars
        # naturally preserves each profession's independent state.
        self.cooldowns_remaining: dict[str, float] = {
            spec.skill_id: 0.0
            for avatar_index in range(len(AVATAR_NAMES))
            for spec in skill_pool_for_avatar(avatar_index)
        }

        # This is intentionally only a visual idle pulse, not combat timing.
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self._advance_idle)
        self.idle_timer.start(40)

    @property
    def avatar_name(self) -> str:
        return AVATAR_NAMES[self.avatar_index]

    @property
    def current_loadout_name(self) -> str:
        """Short display name for the active profession's debug build."""
        prototype_id = prototype_id_for_avatar(self.avatar_index)
        return self.current_loadout_preset[prototype_id]

    def _current_loadout_specs(self):
        return loadout_specs_for_avatar(self.avatar_index, self.current_loadout_name)

    def _reset_current_loadout_state(self) -> None:
        """Reset only the currently selected profession after a build swap."""
        prototype_id = prototype_id_for_avatar(self.avatar_index)
        self.active_effects.clear()
        self.current_anchors = {}
        self.skill_flash = 0.0
        self.active_skill_slot = None
        self.active_skill_name = ""
        self.active_skill_variant = ""
        self.auto_action_remaining = 0.0
        self.sequence_cursors[prototype_id] = 0
        for spec in skill_pool_for_avatar(self.avatar_index):
            self.cooldowns_remaining[spec.skill_id] = 0.0
        self.runtime_states[prototype_id] = create_runtime_state(prototype_id)
        self.runtime_state = self.runtime_states[prototype_id]

    def _cycle_loadout_preset(self) -> None:
        """Cycle the active profession's debug preset, if it has alternatives."""
        prototype_id = prototype_id_for_avatar(self.avatar_index)
        preset_names = tuple(loadout_presets[prototype_id])
        if len(preset_names) <= 1:
            return
        current_name = self.current_loadout_preset[prototype_id]
        next_index = (preset_names.index(current_name) + 1) % len(preset_names)
        self.current_loadout_preset[prototype_id] = preset_names[next_index]
        self._reset_current_loadout_state()
        self.update()

    def _advance_idle(self) -> None:
        self.idle_phase = (self.idle_phase + 0.045) % math.tau
        for effect in self.active_effects:
            effect.age += 0.04
        self.active_effects = [effect for effect in self.active_effects if effect.age < effect.duration]
        for skill_id, remaining in self.cooldowns_remaining.items():
            self.cooldowns_remaining[skill_id] = max(0.0, remaining - 0.04)
        self.runtime_state.tick(0.04)
        self.auto_action_remaining = max(0.0, self.auto_action_remaining - 0.04)
        self._run_auto_scheduler()
        self.skill_flash = max(0.0, self.skill_flash - 0.04)
        self.update()

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        key_to_avatar = {
            Qt.Key.Key_1: 0,
            Qt.Key.Key_2: 1,
            Qt.Key.Key_3: 2,
            Qt.Key.Key_4: 3,
        }
        if event.key() in key_to_avatar:
            self.avatar_index = key_to_avatar[event.key()]
            self.active_effects.clear()
            self.current_anchors = {}
            self.skill_flash = 0.0
            self.active_skill_slot = None
            self.active_skill_name = ""
            self.active_skill_variant = ""
            self.auto_action_remaining = 0.0
            self.sequence_cursors[prototype_id_for_avatar(self.avatar_index)] = 0
            self.runtime_state = self.runtime_states[prototype_id_for_avatar(self.avatar_index)]
            self.setWindowTitle(f"MapleIdle - Combat Visual Sandbox - {self.avatar_name}")
            self.update()
            return
        if event.key() == Qt.Key.Key_B:
            self._cycle_loadout_preset()
            return
        if event.key() == Qt.Key.Key_A:
            self.control_mode = MODE_AUTO_PRIORITY
            self.auto_action_remaining = 0.0
            self.skill_flash = 0.0
            self.active_skill_slot = None
            self.active_skill_name = ""
            self.active_skill_variant = ""
            self.update()
            return
        if event.key() == Qt.Key.Key_S:
            self.control_mode = MODE_AUTO_SEQUENCE
            self.auto_action_remaining = 0.0
            self.skill_flash = 0.0
            self.active_skill_slot = None
            self.active_skill_name = ""
            self.active_skill_variant = ""
            self.update()
            return
        if event.key() == Qt.Key.Key_M:
            self.control_mode = MODE_MANUAL
            self.auto_action_remaining = 0.0
            self.skill_flash = 0.0
            self.active_skill_slot = None
            self.active_skill_name = ""
            self.active_skill_variant = ""
            self.update()
            return
        if event.key() == Qt.Key.Key_D:
            self.show_debug_anchors = not self.show_debug_anchors
            self.update()
            return
        slot_keys = {
            Qt.Key.Key_Q: 0,
            Qt.Key.Key_W: 1,
            Qt.Key.Key_E: 2,
            Qt.Key.Key_R: 3,
        }
        if event.key() in slot_keys:
            if self.control_mode == MODE_MANUAL:
                self._trigger_skill(slot_keys[event.key()])
            return
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.control_mode == MODE_MANUAL:
                self._trigger_skill(0)
            return
        super().keyPressEvent(event)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        frame = self.rect().adjusted(16, 16, -16, -16)
        area = QRectF(frame)
        self._draw_background(painter, area)
        self._draw_header(painter, area)
        self._draw_enemy_formation(painter, area)
        self._draw_combat_space(painter, area)
        self._draw_player(painter, area)
        self._draw_active_effects(painter, area)
        self._draw_skill_bar(painter, area)

    def _draw_background(self, painter: QPainter, area: QRectF) -> None:
        gradient = QLinearGradient(area.topLeft(), area.bottomLeft())
        gradient.setColorAt(0.0, QColor("#1a2945"))
        gradient.setColorAt(0.52, QColor("#101a31"))
        gradient.setColorAt(1.0, QColor("#172038"))
        painter.fillRect(area, gradient)

        painter.setPen(QPen(QColor("#5d82b8"), 2))
        painter.drawRoundedRect(area, 18, 18)

    def _draw_header(self, painter: QPainter, area: QRectF) -> None:
        header = QRectF(area.left() + 16, area.top() + 14, area.width() - 32, area.height() * 0.085)
        painter.setBrush(QColor("#263c60"))
        painter.setPen(QPen(QColor("#6d9dde"), 1))
        painter.drawRoundedRect(header, 12, 12)

        content = header.adjusted(12, 0, -12, 0)
        zone_width = content.width() / 3
        left_zone = QRectF(content.left(), content.top(), zone_width, content.height())
        center_zone = QRectF(content.left() + zone_width, content.top(), zone_width, content.height())
        right_zone = QRectF(content.left() + zone_width * 2, content.top(), zone_width, content.height())
        painter.setPen(QColor("#d9ebff"))
        painter.setFont(ui_font(max(9, int(area.width() * 0.023)), bold=True))
        painter.drawText(left_zone, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "MISTY CANYON")
        painter.drawText(center_zone, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter, self.avatar_name.upper())
        painter.setPen(QColor("#9dc1ee"))
        painter.drawText(right_zone, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "BOSS  01:42")

    def _draw_enemy_formation(self, painter: QPainter, area: QRectF) -> None:
        boss_center = self._boss_center(area)
        y = boss_center.y()
        self._draw_enemy(painter, QPointF(area.left() + area.width() * 0.22, y + area.height() * 0.012), 0.065, "MINION")
        self._draw_enemy(painter, boss_center, 0.105, "CANYON KING", boss=True)
        self._draw_enemy(painter, QPointF(area.left() + area.width() * 0.78, y + area.height() * 0.012), 0.065, "MINION")

    @staticmethod
    def _boss_center(area: QRectF) -> QPointF:
        return QPointF(area.center().x(), area.top() + area.height() * 0.25)

    @staticmethod
    def _player_center(area: QRectF) -> QPointF:
        return QPointF(area.center().x(), area.top() + area.height() * 0.68)

    def _draw_enemy(self, painter: QPainter, center: QPointF, scale: float, name: str, boss: bool = False) -> None:
        radius = self.height() * scale
        points = []
        for index in range(6):
            angle = math.radians(-90 + index * 60)
            points.append(QPointF(center.x() + radius * math.cos(angle), center.y() + radius * math.sin(angle)))
        path = QPainterPath()
        path.moveTo(points[0])
        for point in points[1:]:
            path.lineTo(point)
        path.closeSubpath()
        painter.setBrush(QColor("#d35465") if boss else QColor("#a85b8c"))
        painter.setPen(QPen(QColor("#ffd0af") if boss else QColor("#f1b5d6"), 3 if boss else 2))
        painter.drawPath(path)

        bar_width = radius * 1.8
        bar = QRectF(center.x() - bar_width / 2, center.y() + radius + 10, bar_width, 7)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#352438"))
        painter.drawRoundedRect(bar, 3, 3)
        painter.setBrush(QColor("#eb6370"))
        painter.drawRoundedRect(QRectF(bar.left(), bar.top(), bar.width() * (0.72 if boss else 0.56), bar.height()), 3, 3)
        painter.setPen(QColor("#f5dcea"))
        painter.setFont(ui_font(max(8, int(self.width() * 0.018)), bold=True))
        painter.drawText(QRectF(bar.left() - 25, bar.bottom() + 2, bar.width() + 50, 18), Qt.AlignmentFlag.AlignHCenter, name)

    def _draw_combat_space(self, painter: QPainter, area: QRectF) -> None:
        space = QRectF(area.left() + area.width() * 0.12, area.top() + area.height() * 0.39, area.width() * 0.76, area.height() * 0.19)
        painter.setPen(QPen(QColor(104, 151, 216, 85), 1, Qt.PenStyle.DashLine))
        painter.setBrush(QColor(43, 77, 126, 24))
        painter.drawRoundedRect(space, 22, 22)
        painter.setPen(QColor(167, 204, 255, 130))
        painter.setFont(ui_font(max(9, int(area.width() * 0.022))))
        painter.drawText(space, Qt.AlignmentFlag.AlignCenter, "COMBAT  /  VFX  SPACE")

    def _draw_player(self, painter: QPainter, area: QRectF) -> None:
        center = self._player_center(area)
        prototype_id = prototype_id_for_avatar(self.avatar_index)
        draw_runtime_presentation(
            painter,
            prototype_id,
            self.runtime_state,
            center,
            area,
            self.idle_phase,
            layer="before_avatar",
        )
        renderer = AvatarRenderer(self.idle_phase, cannon_recoil(self.active_effects, area))
        anchors = renderer.draw(painter, self.avatar_index, center, area)
        self.current_anchors = anchors

        draw_runtime_presentation(
            painter,
            prototype_id,
            self.runtime_state,
            center,
            area,
            self.idle_phase,
            layer="after_avatar",
        )

        if self.show_debug_anchors:
            draw_debug_anchors(painter, anchors)

        size = area.width() * (0.15 if self.avatar_index == 2 else 0.10)
        hp = QRectF(center.x() - area.width() * 0.18, center.y() + size * 0.90, area.width() * 0.36, 11)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#26313e"))
        painter.drawRoundedRect(hp, 5, 5)
        painter.setBrush(QColor("#55d894"))
        painter.drawRoundedRect(QRectF(hp.left(), hp.top(), hp.width() * 0.82, hp.height()), 5, 5)
        painter.setPen(QColor("#d8f7e7"))
        painter.setFont(ui_font(max(9, int(area.width() * 0.021)), bold=True))
        player_label = f"{self.avatar_name.upper()}  ·  {self.current_loadout_name}"
        painter.drawText(QRectF(hp.left(), hp.bottom() + 4, hp.width(), 18), Qt.AlignmentFlag.AlignHCenter, player_label)

        if self.avatar_index == 0:
            resource_y = hp.bottom() + 22
            rage_orbs = max(0, min(5, int(self.runtime_state.get(RAGE_ORBS, 0))))
            painter.setPen(QColor("#ffd98a"))
            painter.setFont(ui_font(max(8, int(area.width() * 0.019)), bold=True))
            painter.drawText(
                QRectF(hp.left(), resource_y, hp.width(), 16),
                Qt.AlignmentFlag.AlignHCenter,
                f"鬥氣：{'●' * rage_orbs}{'○' * (5 - rage_orbs)}",
            )

            active_states = []
            if self.runtime_state.is_active(BURNING_SOUL):
                active_states.append(f"SOUL {self.runtime_state.remaining(BURNING_SOUL):.1f}")
            if self.runtime_state.is_active(FIGHTING_INSTINCT):
                active_states.append(f"INSTINCT {self.runtime_state.remaining(FIGHTING_INSTINCT):.1f}")
            if active_states:
                painter.setPen(QColor("#b9e8ff"))
                painter.drawText(
                    QRectF(hp.left(), resource_y + 17, hp.width(), 16),
                    Qt.AlignmentFlag.AlignHCenter,
                    "  ".join(active_states),
                )

    def _trigger_skill(self, slot_index: int = 0) -> bool:
        area = QRectF(self.rect().adjusted(16, 16, -16, -16))
        target = self._boss_center(area)
        target_ground = QPointF(target.x(), target.y() + self.height() * 0.105 + 10)
        player_center = self._player_center(area)
        skill_spec = self._current_loadout_specs()[slot_index]
        skill_id = skill_spec.skill_id
        if self.auto_action_remaining > 0.0:
            # One shared presentation cast lock applies to both MANUAL and
            # AUTO input; effect lifetime is deliberately not part of it.
            return False
        if self.cooldowns_remaining[skill_id] > 0.0:
            # A cooldown press is intentionally silent: no new VFX, flash, or
            # effect replacement is created while the skill is unavailable.
            return False
        prototype_id = prototype_id_for_avatar(self.avatar_index)
        variant = resolve_skill_variant(prototype_id, skill_id, self.runtime_state)
        effect = create_effect(skill_id, self.current_anchors, player_center, target, target_ground, variant)
        self.active_effects.append(effect)
        self.cooldowns_remaining[skill_id] = skill_spec.cooldown
        self.auto_action_remaining = self.auto_action_interval
        apply_skill_runtime_effects(prototype_id, skill_id, self.runtime_state)
        for event_id in resolve_post_cast_events(prototype_id, skill_id, self.runtime_state):
            self.active_effects.append(
                create_presentation_effect(
                    event_id,
                    player_center,
                    target,
                    target_ground,
                    area,
                )
            )
        self.active_skill_slot = slot_index
        self.active_skill_name = skill_spec.display_name
        self.active_skill_variant = variant
        self.skill_flash = 0.46
        self.update()
        return True

    def _run_auto_scheduler(self) -> None:
        """Pick one ready skill for the active avatar at a gentle UI cadence."""
        if self.control_mode == MODE_MANUAL or self.auto_action_remaining > 0.0:
            return

        prototype_id = prototype_id_for_avatar(self.avatar_index)
        pool = self._current_loadout_specs()
        if self.control_mode == MODE_AUTO_SEQUENCE:
            cursor = self.sequence_cursors[prototype_id] % len(pool)
            self.sequence_cursors[prototype_id] = cursor
            skill_id = pool[cursor].skill_id
            if self.cooldowns_remaining.get(skill_id, 0.0) <= 0.0 and self._trigger_skill(cursor):
                self.sequence_cursors[prototype_id] = (cursor + 1) % len(pool)
            return

        equipped_skill_ids = tuple(spec.skill_id for spec in pool)
        skill_id = select_auto_priority_skill(
            prototype_id,
            self.current_loadout_name,
            equipped_skill_ids,
            self.runtime_state,
            self.cooldowns_remaining,
        )
        if skill_id is None:
            return
        slot_by_id = {spec.skill_id: index for index, spec in enumerate(pool)}
        slot_index = slot_by_id.get(skill_id)
        if slot_index is not None:
            self._trigger_skill(slot_index)

    def _draw_active_effects(self, painter: QPainter, area: QRectF) -> None:
        for effect in self.active_effects:
            draw_skill_effect(painter, effect, area)

    def _draw_skill_bar(self, painter: QPainter, area: QRectF) -> None:
        y = area.top() + area.height() * 0.84
        available_width = area.width() * 0.88
        gap = min(12.0, max(6.0, area.width() * 0.018))
        raw_slot_width = (available_width - gap * 3) / 4
        slot_width = min(74.0, max(40.0, raw_slot_width))
        # Keep the minimum size helpful at normal window sizes, while never
        # allowing the row to exceed the available Arena width.
        if slot_width * 4 + gap * 3 > available_width:
            slot_width = max(1.0, raw_slot_width)
        total_width = slot_width * 4 + gap * 3
        start_x = area.center().x() - total_width / 2
        colors = ("#5279d6", "#8a61c8", "#3c9b9c", "#c47a45")
        key_labels = ("Q", "W", "E", "R")
        skill_specs = self._current_loadout_specs()

        if self.control_mode:
            name_rect = QRectF(
                area.center().x() - area.width() * 0.28,
                y - area.height() * 0.055,
                area.width() * 0.56,
                area.height() * 0.040,
            )
            painter.setBrush(QColor(20, 31, 54, 225))
            painter.setPen(QPen(QColor("#85b8e8"), 1))
            painter.drawRoundedRect(name_rect, 7, 7)
            painter.setPen(QColor("#f0f6ff"))
            painter.setFont(ui_font(max(8, int(area.width() * 0.020)), bold=True))
            status_text = MODE_LABELS[self.control_mode]
            if self.skill_flash > 0.0 and self.active_skill_name:
                skill_display = self.active_skill_name
                if self.avatar_index == 0 and self.active_skill_variant:
                    skill_display = f"{skill_display}  ·  {self.active_skill_variant.upper()}"
                status_text = f"{MODE_LABELS[self.control_mode]}  ·  {skill_display}"
            painter.drawText(name_rect, Qt.AlignmentFlag.AlignCenter, status_text)

        for index, (color, key_label, spec) in enumerate(zip(colors, key_labels, skill_specs)):
            slot = QRectF(start_x + index * (slot_width + gap), y, slot_width, slot_width)
            painter.setBrush(QColor("#202e49"))
            painter.setPen(QPen(QColor(color), 2))
            painter.drawRoundedRect(slot, 12, 12)
            if index == self.active_skill_slot and self.skill_flash > 0.0:
                flash_alpha = int(105 * min(1.0, self.skill_flash / 0.20))
                painter.setBrush(QColor(235, 249, 255, flash_alpha))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(slot.adjusted(3, 3, -3, -3), 9, 9)
            painter.setPen(QColor("#dbeaff"))
            painter.setFont(ui_font(max(8, int(slot_width * 0.15)), bold=True))
            painter.drawText(slot.adjusted(6, 4, -6, -slot_width * 0.72), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, key_label)
            self._draw_skill_icon(painter, slot, index, color)

            remaining = max(0.0, self.cooldowns_remaining.get(spec.skill_id, 0.0))
            if remaining > 0.0:
                painter.setBrush(QColor(7, 13, 25, 178))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(slot.adjusted(3, 3, -3, -3), 9, 9)
                painter.setPen(QColor("#f1f5ff"))
                painter.setFont(ui_font(max(9, int(slot_width * 0.22)), bold=True))
                painter.drawText(
                    slot.adjusted(2, slot_width * 0.30, -2, -slot_width * 0.27),
                    Qt.AlignmentFlag.AlignCenter,
                    f"{max(0.1, remaining):.1f}",
                )

    @staticmethod
    def _draw_skill_icon(painter: QPainter, slot: QRectF, icon_index: int, color: str) -> None:
        """Draw a tiny procedural mark; slot labels carry the interaction mapping."""
        center = slot.center() + QPointF(0, slot.height() * 0.08)
        radius = slot.width() * 0.22
        pen = QPen(QColor(color), max(1.5, slot.width() * 0.035), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)

        painter.save()
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if icon_index == 0:  # blade / slash
            painter.drawLine(center + QPointF(-radius * 0.8, radius * 0.8), center + QPointF(radius * 0.8, -radius * 0.8))
            painter.drawLine(center + QPointF(-radius * 0.55, radius * 0.8), center + QPointF(-radius * 0.8, radius * 0.55))
        elif icon_index == 1:  # illusion / mirrored focus
            painter.drawEllipse(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2))
            painter.drawLine(center + QPointF(-radius * 1.35, 0), center + QPointF(radius * 1.35, 0))
            painter.drawLine(center + QPointF(0, -radius * 1.35), center + QPointF(0, radius * 1.35))
        elif icon_index == 2:  # energy / twin streaks
            painter.drawLine(center + QPointF(-radius * 0.95, radius * 0.55), center + QPointF(radius * 0.55, -radius * 0.95))
            painter.drawLine(center + QPointF(-radius * 0.35, radius * 0.95), center + QPointF(radius * 0.95, -radius * 0.35))
        elif icon_index == 3:  # spatial focus
            painter.drawEllipse(QRectF(center.x() - radius * 0.9, center.y() - radius * 0.9, radius * 1.8, radius * 1.8))
            painter.setBrush(QColor(color))
            painter.drawEllipse(QRectF(center.x() - radius * 0.24, center.y() - radius * 0.24, radius * 0.48, radius * 0.48))
        elif icon_index == 4:  # burst / lightning
            path = QPainterPath(center + QPointF(-radius * 0.15, -radius * 1.2))
            path.lineTo(center + QPointF(-radius * 0.85, radius * 0.05))
            path.lineTo(center + QPointF(-radius * 0.08, -radius * 0.05))
            path.lineTo(center + QPointF(radius * 0.22, radius * 1.2))
            path.lineTo(center + QPointF(radius * 0.85, -radius * 0.15))
            path.lineTo(center + QPointF(radius * 0.08, radius * 0.02))
            path.closeSubpath()
            painter.drawPath(path)
        else:  # holy / support focus
            painter.drawEllipse(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2))
            painter.drawLine(center + QPointF(-radius * 1.2, 0), center + QPointF(radius * 1.2, 0))
            painter.drawLine(center + QPointF(0, -radius * 1.2), center + QPointF(0, radius * 1.2))
        painter.restore()
