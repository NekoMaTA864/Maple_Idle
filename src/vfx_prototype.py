"""Small, data-driven VFX primitives for the vertical battle prototype.

These effects are presentation-only.  They carry no damage, cooldown, hit
count, progression, or combat decision state, and their visual variation is
derived from a local deterministic seed rather than the gameplay RNG.
"""

from dataclasses import dataclass, field
import math
import random
from typing import Mapping

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QBrush, QLinearGradient, QPainterPath, QPen, QRadialGradient

from vfx_core import (
    _draw_bloom_line,
    _draw_crackling_lightning,
    _draw_expanding_shockwave,
    _draw_ribbon_slash,
    _draw_shuriken,
)


Point = tuple[float, float]
Color = tuple[int, int, int]


def _point(value) -> Point:
    if isinstance(value, QPointF):
        return float(value.x()), float(value.y())
    return float(value[0]), float(value[1])


def _lerp(start: Point, end: Point, ratio: float) -> Point:
    ratio = max(0.0, min(1.0, float(ratio)))
    return (
        start[0] + (end[0] - start[0]) * ratio,
        start[1] + (end[1] - start[1]) * ratio,
    )


def _clamp_color(color) -> Color:
    return tuple(max(0, min(255, int(channel))) for channel in color[:3])


def _color(color: Color, alpha: int) -> QColor:
    r, g, b = _clamp_color(color)
    return QColor(r, g, b, max(0, min(255, int(alpha))))


def _draw_angular_wind_streaks(painter, position, nx, ny, px, py, size, color, alpha, count):
    """Draw short, non-circular wind cuts around a moving projectile."""
    painter.save()
    painter.setPen(QPen(_color(color, int(alpha * 0.62)), max(1.0, size * 0.055)))
    for index in range(max(0, int(count))):
        side = -1.0 if index % 2 == 0 else 1.0
        offset = size * (0.42 + index * 0.12)
        center = (
            position[0] - nx * size * 0.18 + px * offset * side,
            position[1] - ny * size * 0.18 + py * offset * side,
        )
        start = (
            center[0] - nx * size * 0.34 - px * size * 0.18 * side,
            center[1] - ny * size * 0.34 - py * size * 0.18 * side,
        )
        end = (
            center[0] + nx * size * 0.50 + px * size * 0.22 * side,
            center[1] + ny * size * 0.50 + py * size * 0.22 * side,
        )
        painter.drawLine(QPointF(*start), QPointF(*end))
    painter.restore()


class PrototypeEffect:
    """Common lifecycle contract accepted by ``VisualEffectManager``."""

    layer = "effects"
    primitive = "prototype"

    def __init__(self, source, target=None, lifetime=0.5, color=(255, 255, 255), seed=0,
                 delay=0.0):
        self.kind = self.primitive
        self.source = _point(source)
        self.target = _point(target if target is not None else source)
        self.x, self.y = self.source
        self.target_x, self.target_y = self.target
        self.color = _clamp_color(color)
        self.duration = max(0.001, float(lifetime))
        self.delay = max(0.0, float(delay))
        self.timer = self.duration + self.delay
        self.seed = int(seed)
        self.presentation_rng = random.Random(self.seed)

    @property
    def progress(self) -> float:
        if self.timer > self.duration:
            return 0.0
        return max(0.0, min(1.0, 1.0 - self.timer / self.duration))

    @property
    def has_started(self) -> bool:
        return self.timer <= self.duration

    @property
    def is_alive(self) -> bool:
        return self.timer > 0.0

    def update(self, dt: float) -> None:
        self.timer = max(0.0, self.timer - max(0.0, float(dt)))

    def set_progress(self, progress: float) -> None:
        progress = max(0.0, min(1.0, float(progress)))
        self.timer = self.duration * (1.0 - progress)

    def draw(self, painter) -> None:
        raise NotImplementedError


class SlashEffect(PrototypeEffect):
    """A directional ribbon slash that can travel between any two points."""

    primitive = "slash"

    def __init__(self, source, target=None, size=84.0, lifetime=0.55, arc=115.0,
                 angle=None, fade=True, color=(255, 220, 120), seed=101, delay=0.0,
                 style="ribbon", variant="normal", alpha_scale=1.0,
                 offset=(0.0, 0.0)):
        super().__init__(source, target, lifetime=lifetime, color=color, seed=seed, delay=delay)
        self.size = float(size)
        self.arc = float(arc)
        self.angle = None if angle is None else float(angle)
        self.fade = bool(fade)
        self.style = str(style)
        self.variant = str(variant)
        self.alpha_scale = max(0.0, float(alpha_scale))
        self.offset = _point(offset)

    def draw(self, painter) -> None:
        if not self.has_started:
            return
        if self.style == "rift":
            self._draw_rift(painter)
            return
        if self.style == "phantom":
            self._draw_phantom(painter)
            return
        progress = self.progress
        center = _lerp(self.source, self.target, min(1.0, progress * 1.2))
        dx = self.target[0] - self.source[0]
        dy = self.target[1] - self.source[1]
        direction = self.angle if self.angle is not None else math.degrees(math.atan2(dy, dx))
        sweep = self.arc * min(1.0, 0.30 + progress * 1.05)
        radius = self.size * (0.66 + 0.18 * math.sin(progress * math.pi))
        alpha = int(255 * ((1.0 - progress) if self.fade else 1.0) * self.alpha_scale)

        # A short trailing ribbon gives the strike a direction instead of a
        # static fan silhouette.
        trail_center = _lerp(self.source, self.target, max(0.0, progress * 1.15 - 0.12))
        _draw_ribbon_slash(
            painter,
            trail_center[0], trail_center[1],
            direction - sweep * 0.42, sweep * 0.62,
            radius * 0.16, radius * 0.78,
            self.color, int(alpha * 0.30), core_white=False,
        )
        _draw_ribbon_slash(
            painter,
            center[0], center[1],
            direction - sweep / 2.0, sweep,
            radius * 0.28, radius,
            self.color, alpha,
        )
        painter.save()
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(_color(self.color, int(alpha * 0.90)), max(1.2, self.size * 0.018)))
        painter.translate(center[0], center[1])
        painter.rotate(direction)
        painter.drawArc(QRectF(-radius, -radius * 0.50, radius * 2.0, radius), 196 * 16, int(sweep * 0.78) * 16)
        painter.restore()
        if progress > 0.60:
            _draw_expanding_shockwave(
                painter, self.target[0], self.target[1],
                self.size * 0.58, (progress - 0.60) / 0.40,
                self.color, alpha, aspect=0.30, rings=1,
            )

    def _draw_phantom(self, painter) -> None:
        """Draw a detached, translucent blade afterimage.

        ``offset`` is a presentation-space displacement from the primary
        slash pose. It keeps delayed illusion copies visually separated while
        preserving the shared SlashEffect lifecycle and API.
        """
        progress = self.progress
        center = _lerp(self.source, self.target, 0.36 + min(0.64, progress * 0.82))
        dx = self.target[0] - self.source[0]
        dy = self.target[1] - self.source[1]
        direction = self.angle if self.angle is not None else math.degrees(math.atan2(dy, dx))
        radians = math.radians(direction)
        normal = (-math.sin(radians), math.cos(radians))
        lateral_offset = math.sin(self.seed * 0.17) * self.size * 0.05
        cx = center[0] + normal[0] * lateral_offset + self.offset[0]
        cy = center[1] + normal[1] * lateral_offset + self.offset[1]
        direction_vec = (math.cos(radians), math.sin(radians))
        length = self.size * (0.52 + 0.10 * math.sin(progress * math.pi))
        width = self.size * (0.15 + 0.025 * math.sin(progress * math.pi))
        front = (
            cx + direction_vec[0] * length * 0.56,
            cy + direction_vec[1] * length * 0.56,
        )
        shoulder = (
            cx - direction_vec[0] * length * 0.08,
            cy - direction_vec[1] * length * 0.08,
        )
        tail = (
            cx - direction_vec[0] * length * 0.50,
            cy - direction_vec[1] * length * 0.50,
        )
        front_left = (front[0] + normal[0] * width * 0.22, front[1] + normal[1] * width * 0.22)
        front_right = (front[0] - normal[0] * width * 0.22, front[1] - normal[1] * width * 0.22)
        shoulder_left = (shoulder[0] + normal[0] * width, shoulder[1] + normal[1] * width)
        shoulder_right = (shoulder[0] - normal[0] * width, shoulder[1] - normal[1] * width)
        tail_left = (tail[0] + normal[0] * width * 0.28, tail[1] + normal[1] * width * 0.28)
        tail_right = (tail[0] - normal[0] * width * 0.28, tail[1] - normal[1] * width * 0.28)
        alpha = int(175 * (1.0 - progress) * self.alpha_scale)
        if alpha <= 0:
            return

        blade = QPainterPath(QPointF(*front))
        blade.lineTo(QPointF(*front_left))
        blade.lineTo(QPointF(*shoulder_left))
        blade.lineTo(QPointF(*tail_left))
        blade.lineTo(QPointF(*tail_right))
        blade.lineTo(QPointF(*shoulder_right))
        blade.lineTo(QPointF(*front_right))
        blade.closeSubpath()
        gradient = QLinearGradient(QPointF(*tail), QPointF(*front))
        gradient.setColorAt(0.0, _color(self.color, int(alpha * 0.08)))
        gradient.setColorAt(0.52, _color(self.color, int(alpha * 0.34)))
        gradient.setColorAt(1.0, QColor(245, 250, 255, int(alpha * 0.72)))
        painter.save()
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(_color(self.color, int(alpha * 0.78)), max(1.0, self.size * 0.018)))
        painter.drawPath(blade)
        painter.setPen(QPen(QColor(255, 255, 255, int(alpha * 0.78)), max(1.0, self.size * 0.012)))
        painter.drawLine(QPointF(*tail), QPointF(*front))
        painter.restore()

    def _draw_rift(self, painter) -> None:
        """Draw the sandbox-proven spatial slash geometry as a slash style.

        This remains a reusable SlashEffect variant: it does not know about
        Hero resources or any skill/runtime state.
        """
        progress = self.progress
        settings = {
            "normal": (0.88, 1, 105, 1.0),
            "empowered": (1.08, 2, 145, 1.12),
            "maximum": (1.34, 2, 195, 1.28),
        }
        scale, layer_count, base_alpha, width_scale = settings.get(
            self.variant, settings["normal"]
        )
        fade = min(1.0, progress / 0.12) * min(1.0, (1.0 - progress) / 0.22)
        fade *= self.alpha_scale
        center = self.target
        painter.save()
        for layer in range(layer_count):
            offset = (layer - (layer_count - 1) / 2.0) * self.size * 0.10
            radius_x = self.size * 0.92 * scale
            radius_y = self.size * 0.22 * scale
            path = QPainterPath(QPointF(center[0] - radius_x, center[1] + radius_y + offset))
            path.lineTo(QPointF(center[0] - radius_x * 0.36, center[1] - radius_y * 0.35 + offset))
            path.lineTo(QPointF(center[0] + radius_x * 0.10, center[1] + radius_y * 0.22 + offset))
            path.lineTo(QPointF(center[0] + radius_x, center[1] - radius_y - offset))
            painter.setPen(QPen(
                _color(self.color, int(base_alpha * fade)),
                max(4.0, self.size * 0.058 * width_scale),
            ))
            painter.drawPath(path)
            painter.setPen(QPen(
                QColor(218, 249, 255, int(230 * fade)),
                max(1.5, self.size * 0.020),
            ))
            painter.drawPath(path)
        painter.restore()


class ProjectileEffect(PrototypeEffect):
    """A source-to-target projectile with optional trail and homing target."""

    primitive = "projectile"

    def __init__(self, source, target, speed=420.0, size=14.0, lifetime=None,
                 trail=False, homing=False, color=(160, 220, 255), seed=202,
                 shape="default", trail_length=0.12, delay=0.0, variant="normal",
                 alpha_scale=1.0, spin_rate=980.0, wind_streaks=0,
                 trail_width_scale=None, style="default", visual_shots=1,
                 shot_spacing=0.0, shot_travel=0.80, recoil_scale=0.0,
                 muzzle_flash=False, landing_spread=0.0, assist_delay=0.0,
                 assist_travel=0.62, companion_offset=(0.0, 0.0),
                 assist_impact_window=0.72):
        source_point = _point(source)
        target_point = _point(target)
        distance = math.hypot(target_point[0] - source_point[0], target_point[1] - source_point[1])
        calculated_lifetime = distance / max(1.0, float(speed))
        super().__init__(
            source_point,
            target_point,
            lifetime=max(0.08, calculated_lifetime) if lifetime is None else lifetime,
            color=color,
            seed=seed,
            delay=delay,
        )
        self.speed = max(0.0, float(speed))
        self.size = max(1.0, float(size))
        self.trail = bool(trail)
        self.homing = bool(homing)
        self.shape = str(shape)
        self.trail_length = max(0.02, float(trail_length))
        self.variant = str(variant)
        self.alpha_scale = max(0.0, float(alpha_scale))
        self.spin_rate = float(spin_rate)
        self.wind_streaks = max(0, int(wind_streaks))
        self.trail_width_scale = (
            None if trail_width_scale is None else max(0.0, float(trail_width_scale))
        )
        self.style = str(style)
        # These fields describe one presentation sequence only. They are
        # deliberately not hit_count, damage, or any other gameplay state.
        self.visual_shots = max(1, int(visual_shots))
        self.shot_spacing = max(0.0, float(shot_spacing))
        self.shot_travel = max(0.08, float(shot_travel))
        self.recoil_scale = max(0.0, float(recoil_scale))
        self.muzzle_flash = bool(muzzle_flash)
        self.landing_spread = max(0.0, float(landing_spread))
        self.assist_delay = max(0.0, float(assist_delay))
        self.assist_travel = max(0.08, float(assist_travel))
        self.companion_offset = _point(companion_offset)
        self.assist_impact_window = max(0.08, float(assist_impact_window))

    @property
    def position(self) -> Point:
        return _lerp(self.source, self.target, self.progress)

    def set_target(self, target) -> None:
        self.target = _point(target)
        self.target_x, self.target_y = self.target

    def update(self, dt: float, target=None) -> None:
        if self.homing and target is not None:
            self.set_target(target)
        super().update(dt)

    def draw(self, painter) -> None:
        if not self.has_started:
            return
        if self.style == "monkey_assist":
            self._draw_monkey_assist(painter)
            return
        position = self.position
        alpha = int(255 * (1.0 - self.progress) * self.alpha_scale)
        if self.shape == "cannonball" and self.style == "cannon_combo":
            self._draw_cannon_combo(painter)
            return
        if self.trail and self.style not in ("heavy_shuriken", "secret_route"):
            trail_start = _lerp(self.source, position, max(0.0, self.progress - self.trail_length))
            default_width = 0.25 if self.shape == "shuriken" else 0.38
            trail_width = self.size * (
                default_width if self.trail_width_scale is None else self.trail_width_scale
            )
            _draw_bloom_line(painter, trail_start, position, trail_width, self.color, int(alpha * 0.75))

        dx = self.target[0] - self.source[0]
        dy = self.target[1] - self.source[1]
        length = max(1.0, math.hypot(dx, dy))
        nx, ny = dx / length, dy / length
        px, py = -ny, nx
        if self.wind_streaks and self.style not in ("heavy_shuriken", "secret_route"):
            _draw_angular_wind_streaks(
                painter, position, nx, ny, px, py,
                self.size, self.color, alpha, self.wind_streaks,
            )
        tip = (position[0] + nx * self.size * 0.85, position[1] + ny * self.size * 0.85)
        left = (position[0] - nx * self.size * 0.7 + px * self.size * 0.62,
                position[1] - ny * self.size * 0.7 + py * self.size * 0.62)
        right = (position[0] - nx * self.size * 0.7 - px * self.size * 0.62,
                 position[1] - ny * self.size * 0.7 - py * self.size * 0.62)
        if self.shape == "shuriken":
            if self.style == "heavy_shuriken":
                self._draw_heavy_shuriken(painter, position, alpha, nx, ny, px, py)
                return
            if self.style == "secret_route":
                self._draw_secret_route(painter, position, alpha, nx, ny, px, py)
                return
            _draw_shuriken(
                painter, position[0], position[1],
                self.progress * self.spin_rate + self.seed,
                self.size * 0.72,
                _color(self.color, alpha),
                core_white=True,
            )
            return

        if self.shape == "cannonball":
            self._draw_cannonball(painter, position, alpha)
            return

        if self.shape == "sword":
            self._draw_sword(painter, position, alpha, nx, ny, px, py)
            return

        path = QPainterPath()
        path.moveTo(QPointF(*tip))
        path.lineTo(QPointF(*left))
        path.lineTo(QPointF(*right))
        path.closeSubpath()
        painter.save()
        painter.setPen(QPen(_color(self.color, alpha), 1.2))
        painter.setBrush(QBrush(_color(self.color, alpha)))
        painter.drawPath(path)
        painter.setBrush(QBrush(QColor(255, 255, 255, alpha)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(*position), self.size * 0.30, self.size * 0.30)
        painter.restore()

    def assist_shot_phase(self, elapsed=None):
        """Return the deterministic assist-shot phase for presentation use."""
        if elapsed is None:
            elapsed = self.duration * self.progress
        return (max(0.0, float(elapsed)) - self.assist_delay) / self.assist_travel

    def companion_position(self, elapsed=None):
        """Return the deterministic companion pose near the firing anchor."""
        if elapsed is None:
            elapsed = self.duration * self.progress
        elapsed = max(0.0, float(elapsed))
        dx = self.target[0] - self.source[0]
        dy = self.target[1] - self.source[1]
        distance = max(1.0, math.hypot(dx, dy))
        nx, ny = dx / distance, dy / distance
        shot_phase = self.assist_shot_phase(elapsed)
        recoil = 0.0
        if 0.0 <= shot_phase < 0.24:
            recoil = self.size * 0.18 * (1.0 - shot_phase / 0.24)
        bob = math.sin(elapsed * 7.0) * self.size * 0.06
        return (
            self.source[0] + self.companion_offset[0] - nx * recoil,
            self.source[1] + self.companion_offset[1] + bob - ny * recoil,
        )

    def assist_shot_position(self, elapsed=None):
        """Return the companion's assist projectile position, if launched."""
        phase = self.assist_shot_phase(elapsed)
        if phase <= 0.0:
            return None
        ratio = 1.0 - (1.0 - min(1.0, phase)) ** 1.05
        origin = self.companion_position(self.assist_delay)
        return _lerp(origin, self.target, ratio)

    def monkey_assist_alpha(self, elapsed=None):
        """Return the visible alpha, including explicit entry/exit boundary states."""
        if elapsed is None:
            elapsed = self.duration * self.progress
        elapsed = max(0.0, float(elapsed))
        entry_fade = 0.24 + 0.76 * min(1.0, elapsed / 0.16)
        exit_fade = min(1.0, max(0.0, (self.duration - elapsed) / 0.24))
        return int(238 * self.alpha_scale * min(entry_fade, exit_fade))

    def monkey_assist_impact_fade(self, elapsed=None):
        """Return the short deterministic impact fade after the assist shot."""
        phase = self.assist_shot_phase(elapsed)
        if phase <= 1.0:
            return 0.0
        return max(0.0, 1.0 - (phase - 1.0) / self.assist_impact_window)

    def _draw_monkey_assist(self, painter):
        elapsed = self.duration * self.progress
        phase = self.assist_shot_phase(elapsed)
        alpha = self.monkey_assist_alpha(elapsed)
        if alpha <= 0:
            return

        companion = self.companion_position(elapsed)
        if phase <= 0.0:
            dx = self.target[0] - companion[0]
            dy = self.target[1] - companion[1]
            distance = max(1.0, math.hypot(dx, dy))
            sight_end = (
                companion[0] + dx / distance * distance * 0.72,
                companion[1] + dy / distance * distance * 0.72,
            )
            painter.save()
            painter.setPen(QPen(
                QColor(255, 220, 128, int(alpha * 0.52)),
                max(1.0, self.size * 0.045),
                Qt.DashLine,
            ))
            painter.drawLine(QPointF(*companion), QPointF(*sight_end))
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(
                QColor(255, 236, 172, int(alpha * 0.72)),
                max(1.0, self.size * 0.055),
            ))
            painter.drawEllipse(
                QPointF(*self.target), self.size * 0.34, self.size * 0.24,
            )
            painter.restore()

        self._draw_monkey_companion(painter, companion, alpha, phase)

        if 0.0 < phase <= 1.0:
            shot_position = self.assist_shot_position(elapsed)
            origin = self.companion_position(self.assist_delay)
            shot_ratio = 1.0 - (1.0 - phase) ** 1.05
            trail_start = _lerp(origin, shot_position, max(0.0, shot_ratio - 0.24))
            _draw_bloom_line(
                painter,
                trail_start,
                shot_position,
                max(1.8, self.size * 0.12),
                self.color,
                int(alpha * 0.76),
                core_white=True,
            )
            painter.save()
            orb_radius = self.size * 0.22
            glow = QRadialGradient(
                QPointF(*shot_position), orb_radius * 2.5,
            )
            glow.setColorAt(0.0, QColor(255, 250, 206, alpha))
            glow.setColorAt(0.45, _color(self.color, int(alpha * 0.86)))
            glow.setColorAt(1.0, _color(self.color, 0))
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(*shot_position), orb_radius * 1.8, orb_radius * 1.8)
            painter.setBrush(QColor(255, 245, 190, alpha))
            painter.setPen(QPen(QColor(255, 214, 120, alpha), max(1.0, self.size * 0.045)))
            painter.drawEllipse(QPointF(*shot_position), orb_radius, orb_radius * 0.72)
            painter.restore()
        elif phase > 1.0:
            impact_fade = self.monkey_assist_impact_fade(elapsed)
            if impact_fade > 0.0:
                self._draw_monkey_assist_impact(painter, alpha, impact_fade)

    def _draw_monkey_companion(self, painter, position, alpha, phase):
        x, y = position
        painter.save()

        glow = QRadialGradient(QPointF(x, y), self.size * 1.35)
        glow.setColorAt(0.0, QColor(255, 204, 112, int(alpha * 0.28)))
        glow.setColorAt(1.0, QColor(255, 145, 70, 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(x, y), self.size * 1.15, self.size * 0.82)

        body_color = QColor(99, 62, 46, alpha)
        outline = QColor(255, 210, 132, int(alpha * 0.92))
        painter.setBrush(QBrush(body_color))
        painter.setPen(QPen(outline, max(1.0, self.size * 0.055)))
        painter.drawEllipse(QPointF(x, y + self.size * 0.24), self.size * 0.34, self.size * 0.42)
        painter.drawEllipse(QPointF(x, y - self.size * 0.28), self.size * 0.29, self.size * 0.27)
        painter.drawEllipse(QPointF(x - self.size * 0.28, y - self.size * 0.36), self.size * 0.12, self.size * 0.15)
        painter.drawEllipse(QPointF(x + self.size * 0.28, y - self.size * 0.36), self.size * 0.12, self.size * 0.15)

        painter.setPen(QPen(outline, max(1.0, self.size * 0.07), Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(
            QPointF(x - self.size * 0.20, y + self.size * 0.12),
            QPointF(x - self.size * 0.58, y - self.size * 0.02),
        )
        painter.drawLine(
            QPointF(x + self.size * 0.20, y + self.size * 0.12),
            QPointF(x + self.size * 0.52, y - self.size * 0.06),
        )
        painter.drawLine(
            QPointF(x - self.size * 0.16, y + self.size * 0.56),
            QPointF(x - self.size * 0.34, y + self.size * 0.80),
        )
        painter.drawLine(
            QPointF(x + self.size * 0.16, y + self.size * 0.56),
            QPointF(x + self.size * 0.34, y + self.size * 0.80),
        )

        tail = QPainterPath(QPointF(x + self.size * 0.27, y + self.size * 0.34))
        tail.cubicTo(
            x + self.size * 0.76, y + self.size * 0.52,
            x + self.size * 0.86, y - self.size * 0.14,
            x + self.size * 0.50, y - self.size * 0.30,
        )
        painter.setPen(QPen(outline, max(1.0, self.size * 0.075), Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(tail)

        eye_color = QColor(255, 246, 190, int(alpha * (0.72 + 0.28 * min(1.0, max(0.0, phase + 0.2)))))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(eye_color))
        painter.drawEllipse(QPointF(x - self.size * 0.10, y - self.size * 0.31), self.size * 0.035, self.size * 0.035)
        painter.drawEllipse(QPointF(x + self.size * 0.10, y - self.size * 0.31), self.size * 0.035, self.size * 0.035)
        painter.restore()

    def _draw_monkey_assist_impact(self, painter, alpha, fade):
        dx = self.target[0] - self.source[0]
        dy = self.target[1] - self.source[1]
        distance = max(1.0, math.hypot(dx, dy))
        nx, ny = dx / distance, dy / distance
        px, py = -ny, nx
        radius = self.size * (0.42 + 0.28 * (1.0 - fade))
        impact_alpha = int(alpha * fade * 0.78)
        painter.save()
        painter.setPen(QPen(
            QColor(255, 219, 133, impact_alpha),
            max(1.2, self.size * 0.06 * fade),
            Qt.SolidLine,
            Qt.RoundCap,
        ))
        for side in (-1.0, 1.0):
            painter.drawLine(
                QPointF(self.target[0] - nx * radius + px * side * self.size * 0.24,
                        self.target[1] - ny * radius + py * side * self.size * 0.24),
                QPointF(self.target[0] + nx * radius * 0.82 + px * side * self.size * 0.42,
                        self.target[1] + ny * radius * 0.82 + py * side * self.size * 0.42),
            )
        painter.restore()

    def _draw_cannon_combo(self, painter):
        """Draw a slow, weighty cannonade as one presentation lifecycle.

        The sequence is intentionally visual-only: each shell is a timed
        presentation pass inside one manager effect. The existing Gallery
        may add one shared impact effect at the end without creating a
        gameplay hit queue or a second renderer.
        """
        dx = self.target[0] - self.source[0]
        dy = self.target[1] - self.source[1]
        distance = max(1.0, math.hypot(dx, dy))
        nx, ny = dx / distance, dy / distance
        px, py = -ny, nx
        elapsed = self.duration * self.progress
        sequence_fade = 1.0 - max(0.0, self.progress - 0.76) / 0.24
        base_alpha = int(245 * self.alpha_scale * max(0.0, min(1.0, sequence_fade)))
        if base_alpha <= 0:
            return

        for shot_index in range(self.visual_shots):
            launch_time = shot_index * self.shot_spacing
            shot_elapsed = elapsed - launch_time
            if shot_elapsed < 0.0:
                continue
            shot_progress = shot_elapsed / self.shot_travel

            if shot_progress <= 1.0:
                # Ease-in keeps the projectile on screen long enough to read
                # as mass, while the final approach still lands decisively.
                travel_ratio = 1.0 - (1.0 - max(0.0, shot_progress)) ** 1.18
                position = _lerp(self.source, self.target, travel_ratio)
                # Keep the opening on one heavy firing line, then fan the
                # shells into deterministic landing lanes only near the Boss.
                # This preserves the cannonade read without stacking every
                # shell on the same final pixel.
                lane_blend = min(1.0, max(0.0, (shot_progress - 0.46) / 0.42))
                landing_point = self.cannon_landing_point(shot_index)
                position = _lerp(position, landing_point, lane_blend)
                trail_ratio = max(0.0, travel_ratio - 0.24)
                trail_start = _lerp(self.source, position, trail_ratio)
                trail_alpha = int(base_alpha * (0.68 + 0.20 * (1.0 - shot_progress)))
                _draw_bloom_line(
                    painter,
                    trail_start,
                    position,
                    max(4.0, self.size * 0.28),
                    self.color,
                    trail_alpha,
                )
                _draw_bloom_line(
                    painter,
                    _lerp(trail_start, position, 0.30),
                    position,
                    max(1.8, self.size * 0.09),
                    (255, 224, 158),
                    int(trail_alpha * 0.78),
                    core_white=True,
                )

                if self.muzzle_flash and shot_progress < 0.18:
                    muzzle_progress = shot_progress / 0.18
                    self._draw_cannon_muzzle(
                        painter,
                        nx,
                        ny,
                        px,
                        py,
                        1.0 - muzzle_progress,
                        int(base_alpha * (1.0 - muzzle_progress * 0.35)),
                    )
                self._draw_cannonball(painter, position, int(base_alpha * 0.96))
                continue

            # Completed shells leave compact pressure echoes. They are open
            # directional marks, not extra rings or a generic circular blast.
            echo_progress = min(1.0, (shot_progress - 1.0) / 0.30)
            echo_alpha = int(base_alpha * 0.58 * (1.0 - echo_progress))
            if echo_alpha <= 0:
                continue
            span = self.size * (0.44 + 0.28 * echo_progress)
            center = self.cannon_landing_point(shot_index)
            painter.save()
            painter.setPen(QPen(
                QColor(255, 229, 169, echo_alpha),
                max(1.5, self.size * 0.055 * (1.0 - echo_progress * 0.35)),
                Qt.SolidLine,
                Qt.RoundCap,
            ))
            for side in (-1.0, 1.0):
                painter.drawLine(
                    QPointF(center[0] - nx * span * 0.72 + px * side * self.size * 0.18,
                            center[1] - ny * span * 0.72 + py * side * self.size * 0.18),
                    QPointF(center[0] + nx * span + px * side * self.size * 0.42,
                            center[1] + ny * span + py * side * self.size * 0.42),
                )
            painter.restore()

    def cannon_landing_point(self, shot_index):
        """Return a deterministic late-stage landing lane for a shell.

        The lane is presentation geometry only. It stays perpendicular to
        the source-to-target line and is intentionally small enough to read
        as a heavy cannonade rather than a spread projectile attack.
        """
        if self.visual_shots <= 1 or self.landing_spread <= 0.0:
            return self.target
        dx = self.target[0] - self.source[0]
        dy = self.target[1] - self.source[1]
        distance = max(1.0, math.hypot(dx, dy))
        px, py = -dy / distance, dx / distance
        lane_factor = (shot_index / (self.visual_shots - 1)) * 2.0 - 1.0
        offset = lane_factor * self.size * self.landing_spread
        return (
            self.target[0] + px * offset,
            self.target[1] + py * offset,
        )

    def _draw_cannon_muzzle(self, painter, nx, ny, px, py, pulse, alpha):
        """Show pressure, flame, and rearward recoil at the cannon muzzle."""
        if alpha <= 0 or self.recoil_scale <= 0.0:
            return
        source = self.source
        recoil = self.size * self.recoil_scale * (0.48 + 0.34 * pulse)
        cone_length = self.size * (0.72 + 0.25 * pulse)
        cone_width = self.size * (0.34 + 0.16 * pulse)
        painter.save()

        smoke = QRadialGradient(
            QPointF(source[0] - nx * self.size * 0.16, source[1] - ny * self.size * 0.16),
            self.size * 0.72,
        )
        smoke.setColorAt(0.0, QColor(255, 241, 190, int(alpha * 0.72)))
        smoke.setColorAt(0.45, QColor(255, 132, 54, int(alpha * 0.42)))
        smoke.setColorAt(1.0, QColor(104, 61, 53, 0))
        painter.setBrush(QBrush(smoke))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            QPointF(source[0] + nx * self.size * 0.18, source[1] + ny * self.size * 0.18),
            self.size * 0.72,
            self.size * 0.48,
        )

        cone = QPainterPath(QPointF(
            source[0] + nx * self.size * 0.05,
            source[1] + ny * self.size * 0.05,
        ))
        cone.lineTo(QPointF(
            source[0] + nx * cone_length + px * cone_width,
            source[1] + ny * cone_length + py * cone_width,
        ))
        cone.lineTo(QPointF(
            source[0] + nx * cone_length - px * cone_width,
            source[1] + ny * cone_length - py * cone_width,
        ))
        cone.closeSubpath()
        painter.setBrush(QBrush(QColor(255, 138, 48, int(alpha * 0.60))))
        painter.setPen(QPen(QColor(255, 238, 174, int(alpha * 0.86)), max(1.2, self.size * 0.035)))
        painter.drawPath(cone)

        painter.setPen(QPen(
            QColor(255, 226, 161, int(alpha * 0.72)),
            max(2.0, self.size * 0.065),
            Qt.SolidLine,
            Qt.RoundCap,
        ))
        for side in (-1.0, 1.0):
            painter.drawLine(
                QPointF(source[0] - nx * recoil + px * side * self.size * 0.18,
                        source[1] - ny * recoil + py * side * self.size * 0.18),
                QPointF(source[0] + nx * self.size * 0.10 + px * side * self.size * 0.12,
                        source[1] + ny * self.size * 0.10 + py * side * self.size * 0.12),
            )
        painter.restore()

    def _draw_heavy_shuriken(self, painter, position, alpha, nx, ny, px, py):
        """Draw the single heavy Fuma silhouette without a circular wave."""
        progress = self.progress
        charge = min(1.0, progress / 0.18)
        gather = max(0.0, 1.0 - progress / 0.18)
        body_size = self.size * (0.72 + 0.28 * charge)

        trail_start = _lerp(self.source, position, max(0.0, progress - self.trail_length))
        _draw_bloom_line(
            painter,
            trail_start,
            position,
            self.size * 0.22,
            self.color,
            int(alpha * 0.42),
        )
        _draw_bloom_line(
            painter,
            _lerp(trail_start, position, 0.20),
            position,
            self.size * 0.075,
            (238, 220, 255),
            int(alpha * 0.58),
        )
        if progress > 0.16:
            _draw_angular_wind_streaks(
                painter, position, nx, ny, px, py,
                self.size, self.color, alpha, min(1, self.wind_streaks),
            )

        if gather > 0.0:
            painter.save()
            painter.setPen(QPen(QColor(184, 143, 250, int(alpha * 0.52 * gather)), max(1.0, self.size * 0.032)))
            for angle in (28.0, 118.0, 208.0, 298.0):
                radians = math.radians(angle)
                outer = self.size * (1.05 + 0.30 * gather)
                inner = self.size * (0.42 + 0.15 * gather)
                painter.drawLine(
                    QPointF(position[0] + math.cos(radians) * outer, position[1] + math.sin(radians) * outer),
                    QPointF(position[0] + math.cos(radians) * inner, position[1] + math.sin(radians) * inner),
                )
            painter.restore()

        spin_angle = progress * self.spin_rate + self.seed
        painter.save()
        painter.translate(position[0], position[1])
        painter.rotate(spin_angle)
        s = body_size
        heavy_path = QPainterPath()
        heavy_path.moveTo(0, -s * 1.22)
        heavy_path.lineTo(s * 0.26, -s * 0.38)
        heavy_path.lineTo(s * 0.76, -s * 0.18)
        heavy_path.lineTo(s * 1.18, 0)
        heavy_path.lineTo(s * 0.76, s * 0.18)
        heavy_path.lineTo(s * 0.26, s * 0.38)
        heavy_path.lineTo(0, s * 1.22)
        heavy_path.lineTo(-s * 0.26, s * 0.38)
        heavy_path.lineTo(-s * 0.76, s * 0.18)
        heavy_path.lineTo(-s * 1.18, 0)
        heavy_path.lineTo(-s * 0.76, -s * 0.18)
        heavy_path.lineTo(-s * 0.26, -s * 0.38)
        heavy_path.closeSubpath()

        gradient = QLinearGradient(-s, -s, s, s)
        gradient.setColorAt(0.0, QColor(247, 228, 255, alpha))
        gradient.setColorAt(0.28, _color(self.color, int(alpha * 0.94)))
        gradient.setColorAt(0.72, _color((105, 65, 168), int(alpha * 0.96)))
        gradient.setColorAt(1.0, QColor(24, 12, 46, int(alpha * 0.92)))
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(244, 224, 255, alpha), max(1.5, self.size * 0.055)))
        painter.drawPath(heavy_path)

        core = QPainterPath()
        core.moveTo(0, -s * 0.25)
        core.lineTo(s * 0.25, 0)
        core.lineTo(0, s * 0.25)
        core.lineTo(-s * 0.25, 0)
        core.closeSubpath()
        painter.setBrush(QBrush(QColor(17, 8, 35, int(alpha * 0.92))))
        painter.setPen(QPen(QColor(255, 246, 218, int(alpha * 0.92)), max(1.0, self.size * 0.032)))
        painter.drawPath(core)

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 238, 192, int(alpha * 0.74)), max(1.0, self.size * 0.026)))
        for blade_offset in (0.0, 90.0, 180.0, 270.0):
            radians = math.radians(blade_offset)
            painter.drawLine(
                QPointF(math.cos(radians) * s * 0.17, math.sin(radians) * s * 0.17),
                QPointF(math.cos(radians) * s * 0.94, math.sin(radians) * s * 0.94),
            )
        painter.restore()

        impact_phase = min(1.0, max(0.0, (progress - 0.72) / 0.28))
        if impact_phase > 0.0:
            painter.save()
            painter.setPen(QPen(QColor(242, 226, 255, int(alpha * 0.65 * impact_phase)), max(1.0, self.size * 0.035)))
            for side in (-1.0, 1.0):
                painter.drawLine(
                    QPointF(position[0] + px * self.size * 0.16, position[1] + py * self.size * 0.16),
                    QPointF(position[0] + nx * self.size * 0.60 + side * px * self.size * 0.48,
                            position[1] + ny * self.size * 0.60 + side * py * self.size * 0.48),
                )
            painter.restore()

    def _draw_secret_route(self, painter, position, alpha, nx, ny, px, py):
        """Draw a thin, offset ninjutsu route instead of a standard shuriken."""
        progress = self.progress
        activation = min(1.0, progress / 0.18)
        direction_angle = math.degrees(math.atan2(ny, nx))
        trail_start = _lerp(self.source, position, max(0.0, progress - self.trail_length))

        for offset, alpha_scale in ((-0.16, 0.52), (0.18, 0.34)):
            start = (
                trail_start[0] + px * self.size * offset,
                trail_start[1] + py * self.size * offset,
            )
            end = (
                position[0] + px * self.size * offset,
                position[1] + py * self.size * offset,
            )
            _draw_bloom_line(
                painter,
                start,
                end,
                self.size * 0.085,
                self.color,
                int(alpha * alpha_scale),
            )

        if progress < 0.22:
            painter.save()
            painter.setPen(QPen(QColor(191, 151, 240, int(alpha * 0.44 * (1.0 - progress / 0.22))), max(1.0, self.size * 0.030)))
            for angle in (-42.0, 38.0, 132.0):
                radians = math.radians(angle)
                outer = self.size * (0.78 + 0.34 * (1.0 - activation))
                inner = self.size * (0.18 + 0.18 * activation)
                painter.drawLine(
                    QPointF(position[0] + math.cos(radians) * outer, position[1] + math.sin(radians) * outer),
                    QPointF(position[0] + math.cos(radians) * inner, position[1] + math.sin(radians) * inner),
                )
            painter.restore()

        ghost_position = _lerp(self.source, position, max(0.0, progress - 0.13))
        painter.save()
        painter.translate(ghost_position[0], ghost_position[1])
        painter.rotate(direction_angle + progress * self.spin_rate * 0.05 - 12.0)
        ghost_length = self.size * 0.82
        painter.setPen(QPen(QColor(153, 117, 218, int(alpha * 0.26)), max(1.0, self.size * 0.030)))
        painter.drawLine(QPointF(-ghost_length * 0.62, 0), QPointF(ghost_length * 0.62, 0))
        painter.restore()

        painter.save()
        painter.translate(position[0], position[1])
        painter.rotate(direction_angle + progress * self.spin_rate * 0.10 - 8.0)
        length = self.size * (1.05 + 0.28 * activation)
        width = self.size * 0.18
        blade = QPainterPath()
        blade.moveTo(length, 0)
        blade.lineTo(length * 0.28, -width)
        blade.lineTo(-length * 0.70, -width * 0.42)
        blade.lineTo(-length * 0.92, 0)
        blade.lineTo(-length * 0.70, width * 0.42)
        blade.lineTo(length * 0.28, width)
        blade.closeSubpath()
        painter.setBrush(QBrush(QColor(80, 48, 136, int(alpha * 0.78))))
        painter.setPen(QPen(QColor(239, 219, 255, int(alpha * 0.86)), max(1.0, self.size * 0.035)))
        painter.drawPath(blade)
        painter.setPen(QPen(QColor(255, 244, 205, int(alpha * 0.78)), max(1.0, self.size * 0.025)))
        painter.drawLine(QPointF(-length * 0.62, 0), QPointF(length * 0.76, 0))
        painter.restore()

    def _draw_cannonball(self, painter, position, alpha):
        radius = self.size * 0.50
        gradient = QRadialGradient(
            position[0] - radius * 0.35,
            position[1] - radius * 0.42,
            radius * 1.7,
        )
        gradient.setColorAt(0.0, QColor(255, 245, 210, alpha))
        gradient.setColorAt(0.30, _color(self.color, alpha))
        gradient.setColorAt(0.88, _color((92, 52, 54), int(alpha * 0.95)))
        gradient.setColorAt(1.0, QColor(24, 24, 34, int(alpha * 0.85)))
        painter.save()
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(255, 204, 125, alpha), max(1.2, radius * 0.09)))
        painter.drawEllipse(QPointF(*position), radius, radius)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 234, 170, int(alpha * 0.55)), max(1.0, radius * 0.08)))
        painter.drawEllipse(QPointF(*position), radius * 0.72, radius * 0.72)
        painter.restore()

    def _draw_sword(self, painter, position, alpha, nx, ny, px, py):
        """Draw a reusable descending blade projectile with a guard."""
        variant_scale = {
            "normal": 0.86,
            "stronger": 1.08,
            "maximum": 1.24,
            "max_rage": 1.08,
            "instinct": 1.24,
        }.get(getattr(self, "variant", "normal"), 0.86)
        blade_length = self.size * 3.0 * variant_scale
        blade_width = self.size * 0.52 * variant_scale
        base = (
            position[0] - nx * blade_length,
            position[1] - ny * blade_length,
        )
        guard = (
            position[0] - nx * blade_length * 0.78,
            position[1] - ny * blade_length * 0.78,
        )
        tip = (position[0] + nx * self.size * 0.12, position[1] + ny * self.size * 0.12)
        blade = QPainterPath(QPointF(base[0] + px * blade_width, base[1] + py * blade_width))
        blade.lineTo(QPointF(base[0] - px * blade_width, base[1] - py * blade_width))
        blade.lineTo(QPointF(tip[0], tip[1]))
        blade.closeSubpath()

        painter.save()
        _draw_bloom_line(
            painter,
            base,
            tip,
            self.size * 0.56 * variant_scale,
            self.color,
            int(alpha * 0.70),
        )
        painter.setBrush(QBrush(_color(self.color, alpha)))
        painter.setPen(QPen(QColor(255, 255, 225, alpha), max(1.2, self.size * 0.055)))
        painter.drawPath(blade)
        painter.setPen(QPen(QColor(255, 210, 115, alpha), max(2.0, self.size * 0.16)))
        painter.drawLine(
            QPointF(guard[0] - px * self.size * 1.35, guard[1] - py * self.size * 1.35),
            QPointF(guard[0] + px * self.size * 1.35, guard[1] + py * self.size * 1.35),
        )
        painter.restore()


class SpreadProjectileEffect(PrototypeEffect):
    """A reusable fan of projectiles sharing one presentation lifecycle.

    The fan is a visual composition only.  Each shard follows a deterministic
    source-to-offset-target path, while the effect remains one manager item and
    never exposes hit-count or gameplay semantics.
    """

    primitive = "spread_projectile"

    def __init__(self, source, target, projectile_count=5, spread_angle=68.0,
                 fan_radius=34.0, speed=520.0, size=11.0, lifetime=None,
                 trail=True, trail_length=0.14, color=(176, 132, 255), seed=707,
                 delay=0.0, shape="shuriken", alpha_scale=1.0, style="default"):
        source_point = _point(source)
        target_point = _point(target)
        distance = math.hypot(
            target_point[0] - source_point[0],
            target_point[1] - source_point[1],
        )
        calculated_lifetime = distance / max(1.0, float(speed))
        super().__init__(
            source_point,
            target_point,
            lifetime=max(0.08, calculated_lifetime) if lifetime is None else lifetime,
            color=color,
            seed=seed,
            delay=delay,
        )
        self.projectile_count = max(2, int(projectile_count))
        self.spread_angle = float(spread_angle)
        self.fan_radius = max(0.0, float(fan_radius))
        self.speed = max(0.0, float(speed))
        self.size = max(1.0, float(size))
        self.trail = bool(trail)
        self.trail_length = max(0.02, float(trail_length))
        self.shape = str(shape)
        self.alpha_scale = max(0.0, float(alpha_scale))
        self.style = str(style or "default").strip().lower()
        self._base_angle = math.atan2(
            target_point[1] - source_point[1],
            target_point[0] - source_point[0],
        )
        self._fan_angles = tuple(
            math.radians(offset)
            for offset in self._build_fan_offsets()
        )

    def _build_fan_offsets(self):
        half_angle = self.spread_angle * 0.5
        step = self.spread_angle / max(1, self.projectile_count - 1)
        return tuple(-half_angle + step * index for index in range(self.projectile_count))

    @property
    def projectile_targets(self) -> tuple[Point, ...]:
        return tuple(
            (
                self.target[0] + math.cos(self._base_angle + angle) * self.fan_radius,
                self.target[1] + math.sin(self._base_angle + angle) * self.fan_radius,
            )
            for angle in self._fan_angles
        )

    @property
    def projectile_positions(self) -> tuple[Point, ...]:
        return tuple(_lerp(self.source, endpoint, self.progress) for endpoint in self.projectile_targets)

    def draw(self, painter) -> None:
        if not self.has_started:
            return
        progress = self.progress
        alpha = int(255 * (1.0 - progress) * self.alpha_scale)
        if alpha <= 0:
            return

        if self.style == "fan_burst":
            self._draw_fan_burst(painter)
            return

        for index, endpoint in enumerate(self.projectile_targets):
            position = _lerp(self.source, endpoint, progress)
            if self.trail:
                trail_progress = max(0.0, progress - self.trail_length)
                trail_start = _lerp(self.source, endpoint, trail_progress)
                _draw_bloom_line(
                    painter,
                    trail_start,
                    position,
                    self.size * 0.24,
                    self.color,
                    int(alpha * 0.72),
                )

            angle = math.degrees(self._base_angle + self._fan_angles[index])
            angle += progress * 900.0 + index * 19.0
            if self.shape == "shuriken":
                _draw_shuriken(
                    painter,
                    position[0],
                    position[1],
                    angle,
                    self.size * 0.72,
                    _color(self.color, alpha),
                    core_white=True,
                )
            else:
                painter.save()
                painter.setPen(QPen(_color(self.color, alpha), 1.2))
                painter.setBrush(QBrush(_color(self.color, alpha)))
                painter.drawEllipse(QPointF(*position), self.size * 0.55, self.size * 0.55)
                painter.restore()

    def _draw_fan_burst(self, painter) -> None:
        """Draw a compact simultaneous fan, without turning it into a ring."""
        progress = self.progress
        alpha = int(255 * (1.0 - progress) * self.alpha_scale)
        if alpha <= 0:
            return

        if progress < 0.24:
            gather = min(1.0, progress / 0.24)
            center = _lerp(self.source, self.target, gather * 0.12)
            painter.save()
            painter.setPen(QPen(_color(self.color, int(alpha * 0.50)), max(1.0, self.size * 0.12)))
            for index in range(5):
                angle = self._base_angle + math.radians(-38.0 + index * 19.0)
                inner = self.size * (0.18 + gather * 0.16)
                outer = self.size * (0.78 - gather * 0.20)
                painter.drawLine(
                    QPointF(center[0] - math.cos(angle) * inner, center[1] - math.sin(angle) * inner),
                    QPointF(center[0] - math.cos(angle) * outer, center[1] - math.sin(angle) * outer),
                )
            painter.restore()

        for index, endpoint in enumerate(self.projectile_targets):
            position = _lerp(self.source, endpoint, progress)
            trail_progress = max(0.0, progress - self.trail_length)
            trail_start = _lerp(self.source, endpoint, trail_progress)
            if self.trail:
                _draw_bloom_line(
                    painter,
                    trail_start,
                    position,
                    self.size * 0.10,
                    self.color,
                    int(alpha * 0.54),
                )
            angle = math.degrees(self._base_angle + self._fan_angles[index])
            angle += progress * 720.0 + index * 11.0
            if self.shape == "shuriken":
                _draw_shuriken(
                    painter,
                    position[0],
                    position[1],
                    angle,
                    self.size * 0.52,
                    _color(self.color, int(alpha * 0.94)),
                    core_white=False,
                )
            else:
                painter.save()
                painter.setPen(QPen(_color(self.color, int(alpha * 0.90)), 1.0))
                painter.drawPoint(QPointF(*position))
                painter.restore()


class MarkDetonationEffect(PrototypeEffect):
    """Reusable mark presentation with an optional delayed detonation."""

    primitive = "mark_detonation"
    layer = "impact"

    def __init__(self, position, source=None, size=38.0, mark_lifetime=0.72,
                 detonation_delay=0.34, detonation_lifetime=0.42,
                 detonation=True, color=(191, 128, 255), seed=808, delay=0.0,
                 style="contract"):
        self.position = _point(position)
        self.source = _point(source if source is not None else position)
        self.size = max(1.0, float(size))
        self.mark_lifetime = max(0.05, float(mark_lifetime))
        self.detonation_delay = max(0.0, float(detonation_delay)) if detonation else 0.0
        self.detonation_lifetime = max(0.05, float(detonation_lifetime)) if detonation else 0.0
        self.detonation = bool(detonation)
        self.style = str(style or "contract").strip().lower()
        total_lifetime = self.mark_lifetime + self.detonation_delay + self.detonation_lifetime
        super().__init__(
            self.source,
            self.position,
            lifetime=total_lifetime,
            color=color,
            seed=seed,
            delay=delay,
        )

    @property
    def detonation_started(self) -> bool:
        if not self.detonation or not self.has_started:
            return False
        return self.duration * self.progress >= self.mark_lifetime + self.detonation_delay

    def draw(self, painter) -> None:
        if not self.has_started:
            return
        elapsed = self.duration * self.progress
        detonation_start = self.mark_lifetime + self.detonation_delay
        if not self.detonation or elapsed < detonation_start:
            mark_fade = 1.0
            if self.detonation:
                mark_fade = min(1.0, max(0.0, (detonation_start - elapsed) / 0.10))
                mark_fade = max(0.55, mark_fade)
            self._draw_mark(painter, mark_fade)
            return

        detonation_progress = max(
            0.0,
            min(1.0, (elapsed - detonation_start) / self.detonation_lifetime),
        )
        fade = 1.0 - detonation_progress
        if self.style == "talisman":
            self._draw_talisman_detonation(painter, detonation_progress)
            return
        x, y = self.position
        if detonation_progress < 0.22:
            flash_alpha = int(220 * (1.0 - detonation_progress / 0.22))
            painter.setBrush(QBrush(QColor(255, 255, 245, flash_alpha)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(x, y), self.size * 0.72, self.size * 0.48)
        _draw_expanding_shockwave(
            painter,
            x,
            y,
            self.size * 1.9,
            detonation_progress,
            self.color,
            int(240 * fade),
            aspect=0.56,
            rings=2,
        )
        rnd = random.Random(self.seed)
        painter.save()
        painter.setPen(QPen(QColor(244, 226, 255, int(220 * fade)), max(1.0, self.size * 0.045)))
        for index in range(8):
            angle = index * math.pi / 4.0 + rnd.uniform(-0.12, 0.12)
            inner = self.size * (0.38 + detonation_progress * 0.22)
            outer = self.size * (0.92 + detonation_progress * 0.90)
            painter.drawLine(
                QPointF(x + math.cos(angle) * inner, y + math.sin(angle) * inner),
                QPointF(x + math.cos(angle) * outer, y + math.sin(angle) * outer),
            )
        painter.restore()

    def _draw_mark(self, painter, fade) -> None:
        if self.style == "talisman":
            self._draw_talismans(painter, fade)
            return
        self._draw_contract_mark(painter, fade)

    def _draw_contract_mark(self, painter, fade) -> None:
        x, y = self.position
        progress = min(1.0, max(0.0, self.progress))
        clamp = lambda value: min(1.0, max(0.0, value))
        outer_generation = clamp(progress / 0.18)
        inner_generation = clamp((progress - 0.08) / 0.14)
        frame_presence = clamp((0.34 - progress) / 0.12)
        core_generation = clamp((progress - 0.10) / 0.13)
        lock_in = clamp((progress - 0.14) / 0.12)
        peak_flash = max(0.0, 1.0 - abs(progress - 0.22) / 0.065)
        residual = clamp((progress - 0.34) / 0.12)
        late_fade = clamp((progress - 0.38) / 0.40)
        pulse = 0.985 + 0.015 * math.sin(progress * math.pi * 4.0)
        scale = (0.90 + 0.10 * outer_generation) * pulse
        width = self.size * 0.84 * scale
        height = self.size * 0.61 * scale
        alpha = int(244 * max(0.0, min(1.0, fade)))

        def draw_progressive_segments(points, ratio):
            ratio = clamp(ratio)
            segment_count = len(points)
            for index in range(segment_count):
                segment_progress = ratio * segment_count - index
                if segment_progress <= 0.0:
                    break
                start = points[index]
                end = points[(index + 1) % segment_count]
                portion = min(1.0, segment_progress)
                partial_end = QPointF(
                    start.x() + (end.x() - start.x()) * portion,
                    start.y() + (end.y() - start.y()) * portion,
                )
                painter.drawLine(start, partial_end)

        painter.save()
        painter.setBrush(Qt.NoBrush)
        outer_points = (
            QPointF(x, y - height),
            QPointF(x + width * 0.72, y - height * 0.34),
            QPointF(x + width, y),
            QPointF(x + width * 0.72, y + height * 0.34),
            QPointF(x, y + height),
            QPointF(x - width * 0.72, y + height * 0.34),
            QPointF(x - width, y),
            QPointF(x - width * 0.72, y - height * 0.34),
        )
        painter.setPen(QPen(_color(self.color, int(alpha * 0.92 * frame_presence)), max(1.7, self.size * 0.060)))
        draw_progressive_segments(outer_points, outer_generation * frame_presence)

        inner_width = width * 0.54
        inner_height = height * 0.54
        inner_points = (
            QPointF(x, y - inner_height),
            QPointF(x + inner_width * 0.72, y - inner_height * 0.34),
            QPointF(x + inner_width, y),
            QPointF(x + inner_width * 0.72, y + inner_height * 0.34),
            QPointF(x, y + inner_height),
            QPointF(x - inner_width * 0.72, y + inner_height * 0.34),
            QPointF(x - inner_width, y),
            QPointF(x - inner_width * 0.72, y - inner_height * 0.34),
        )
        painter.setPen(QPen(QColor(255, 244, 210, int(alpha * 0.98 * frame_presence)), max(1.1, self.size * 0.036)))
        draw_progressive_segments(inner_points, inner_generation * frame_presence)

        painter.setPen(QPen(QColor(232, 190, 255, int(alpha * (0.45 + 0.55 * lock_in) * frame_presence)), max(1.0, self.size * 0.026)))
        for angle in (45.0, 135.0, 225.0, 315.0):
            radians = math.radians(angle)
            outer_radius = self.size * (1.24 - 0.14 * outer_generation)
            inner_radius = self.size * (0.68 + 0.10 * lock_in)
            painter.drawLine(
                QPointF(x + math.cos(radians) * outer_radius, y + math.sin(radians) * outer_radius),
                QPointF(x + math.cos(radians) * inner_radius, y + math.sin(radians) * inner_radius),
            )

        rune_starts = (0.12, 0.15, 0.13, 0.10)
        rune_scales = (0.82, 1.00, 0.68, 0.90)
        for index, angle in enumerate((0.0, 90.0, 180.0, 270.0)):
            rune_progress = clamp((progress - rune_starts[index]) / 0.10) * frame_presence
            if rune_progress <= 0.0:
                continue
            radians = math.radians(angle)
            rune_radius = self.size * (0.90 + 0.08 * rune_scales[index])
            rune_x = x + math.cos(radians) * rune_radius
            rune_y = y + math.sin(radians) * rune_radius
            painter.save()
            painter.translate(rune_x, rune_y)
            painter.rotate(angle + (index - 1.5) * 2.0)
            rune_width = self.size * 0.16 * rune_scales[index]
            rune_height = self.size * 0.13 * rune_scales[index]
            rune_alpha = int(alpha * rune_progress * (0.64 + 0.30 * (index % 2)))
            painter.setPen(QPen(QColor(191, 151, 240, rune_alpha), max(1.1, self.size * 0.029)))
            draw_progressive_segments(
                (
                    QPointF(-rune_width, -rune_height),
                    QPointF(rune_width * 0.25, -rune_height),
                    QPointF(rune_width * 0.45, -rune_height * 0.7),
                    QPointF(rune_width * 0.45, rune_height * 0.7),
                    QPointF(rune_width * 0.25, rune_height),
                    QPointF(-rune_width, rune_height),
                    QPointF(-rune_width, -rune_height),
                ),
                rune_progress,
            )
            painter.restore()

        if core_generation > 0.0 or residual > 0.0:
            core_strength = max(core_generation, residual * 0.64)
            core_scale = (0.22 + 0.07 * core_generation) * (1.0 - residual * 0.18)
            core_radius = self.size * core_scale
            core = QPainterPath()
            core_offsets = (1.00, 0.92, 1.08, 0.95, 1.04, 0.88)
            for index in range(6):
                angle = math.radians(index * 60.0 - 30.0)
                point = QPointF(
                    x + math.cos(angle) * core_radius * core_offsets[index],
                    y + math.sin(angle) * core_radius * core_offsets[index],
                )
                if index == 0:
                    core.moveTo(point)
                else:
                    core.lineTo(point)
            core.closeSubpath()
            core_alpha = int(alpha * core_strength * (0.62 + 0.38 * (1.0 - late_fade)))
            painter.setBrush(QBrush(QColor(18, 8, 33, int(core_alpha * 0.92))))
            painter.setPen(QPen(QColor(255, 239, 192, core_alpha), max(1.0, self.size * 0.032)))
            painter.drawPath(core)
            painter.setPen(QPen(QColor(110, 70, 157, int(core_alpha * 0.82)), max(1.0, self.size * 0.020)))
            painter.drawLine(QPointF(x - core_radius * 0.42, y + core_radius * 0.16), QPointF(x + core_radius * 0.28, y - core_radius * 0.30))
            painter.drawLine(QPointF(x - core_radius * 0.16, y + core_radius * 0.38), QPointF(x + core_radius * 0.38, y + core_radius * 0.08))

        if residual > 0.0:
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(126, 92, 170, int(alpha * 0.28 * residual)), max(1.0, self.size * 0.018)))
            painter.drawLine(QPointF(x - self.size * 0.36, y + self.size * 0.30), QPointF(x - self.size * 0.20, y + self.size * 0.14))
            painter.drawLine(QPointF(x + self.size * 0.25, y - self.size * 0.31), QPointF(x + self.size * 0.40, y - self.size * 0.18))

        if peak_flash > 0.0:
            flash = QPainterPath()
            for index in range(8):
                angle = math.radians(index * 45.0 - 22.5)
                radius = self.size * (0.42 if index % 2 == 0 else 0.19)
                point = QPointF(x + math.cos(angle) * radius, y + math.sin(angle) * radius)
                if index == 0:
                    flash.moveTo(point)
                else:
                    flash.lineTo(point)
            flash.closeSubpath()
            painter.setBrush(QBrush(QColor(238, 218, 255, int(190 * peak_flash))))
            painter.setPen(Qt.NoPen)
            painter.drawPath(flash)
        painter.restore()

    def _draw_talismans(self, painter, fade) -> None:
        x, y = self.position
        elapsed = self.duration * self.progress
        arrival = min(1.0, max(0.0, elapsed / self.mark_lifetime))
        alpha = int(235 * max(0.0, min(1.0, fade)) * (0.55 + arrival * 0.45))
        paper_layout = (
            (-0.46, -0.12, -16.0, 0.82),
            (0.0, 0.0, 4.0, 1.0),
            (0.46, 0.12, 18.0, 0.82),
        )
        for offset_x, offset_y, angle, scale in paper_layout:
            launch_offset = (offset_x * self.size * 0.10, offset_y * self.size * 0.10)
            destination = (
                x + offset_x * self.size * 1.35,
                y + offset_y * self.size,
            )
            launch = (
                self.source[0] + launch_offset[0],
                self.source[1] + launch_offset[1],
            )
            paper_position = _lerp(launch, destination, arrival)
            drift_x = (1.0 - arrival) * self.size * (-0.42 if offset_x < 0 else 0.42)
            drift_y = (1.0 - arrival) * self.size * (-0.18 if offset_y <= 0 else 0.18)
            if arrival < 0.96:
                _draw_bloom_line(
                    painter,
                    launch,
                    paper_position,
                    self.size * 0.055,
                    self.color,
                    int(alpha * 0.30),
                )
            painter.save()
            painter.translate(paper_position[0] + drift_x, paper_position[1] + drift_y)
            painter.rotate(angle + (1.0 - arrival) * (8.0 if angle < 0 else -8.0))
            width = self.size * 0.34 * scale
            height = self.size * 0.72 * scale
            paper = QPainterPath()
            paper.moveTo(-width * 0.5, -height * 0.5)
            paper.lineTo(width * 0.24, -height * 0.5)
            paper.lineTo(width * 0.5, -height * 0.24)
            paper.lineTo(width * 0.5, height * 0.5)
            paper.lineTo(-width * 0.5, height * 0.5)
            paper.closeSubpath()
            painter.setBrush(QBrush(QColor(248, 225, 174, int(alpha * 0.82))))
            painter.setPen(QPen(QColor(255, 245, 205, alpha), max(1.0, self.size * 0.025)))
            painter.drawPath(paper)
            painter.setPen(QPen(QColor(122, 70, 176, int(alpha * 0.9)), max(1.0, self.size * 0.022)))
            painter.drawLine(QPointF(-width * 0.23, -height * 0.25), QPointF(width * 0.22, -height * 0.25))
            painter.drawLine(QPointF(-width * 0.23, 0), QPointF(width * 0.22, 0))
            painter.drawLine(QPointF(-width * 0.14, height * 0.25), QPointF(width * 0.14, height * 0.25))
            painter.restore()

        if self.detonation and self.progress > 0.22:
            prep_alpha = int(190 * max(0.0, min(1.0, (self.progress - 0.22) / 0.16)))
            painter.save()
            painter.setPen(QPen(QColor(255, 250, 220, prep_alpha), max(1.0, self.size * 0.035)))
            painter.drawLine(QPointF(x - self.size * 0.26, y), QPointF(x + self.size * 0.26, y))
            painter.drawLine(QPointF(x, y - self.size * 0.34), QPointF(x, y + self.size * 0.34))
            painter.restore()

    def _draw_talisman_detonation(self, painter, detonation_progress) -> None:
        x, y = self.position
        fade = 1.0 - detonation_progress
        painter.save()
        flash = QPainterPath()
        flash.moveTo(x, y - self.size * 0.72)
        flash.lineTo(x + self.size * 0.12, y - self.size * 0.15)
        flash.lineTo(x + self.size * 0.70, y)
        flash.lineTo(x + self.size * 0.13, y + self.size * 0.14)
        flash.lineTo(x, y + self.size * 0.72)
        flash.lineTo(x - self.size * 0.13, y + self.size * 0.14)
        flash.lineTo(x - self.size * 0.70, y)
        flash.lineTo(x - self.size * 0.12, y - self.size * 0.15)
        flash.closeSubpath()
        painter.setBrush(QBrush(QColor(255, 249, 221, int(220 * fade))))
        painter.setPen(Qt.NoPen)
        painter.drawPath(flash)

        rnd = random.Random(self.seed)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(244, 226, 255, int(230 * fade)), max(1.0, self.size * 0.045)))
        for index in range(8):
            angle = index * math.pi / 4.0 + rnd.uniform(-0.13, 0.13)
            inner = self.size * (0.16 + detonation_progress * 0.12)
            outer = self.size * (0.48 + detonation_progress * 0.62)
            painter.drawLine(
                QPointF(x + math.cos(angle) * inner, y + math.sin(angle) * inner),
                QPointF(x + math.cos(angle) * outer, y + math.sin(angle) * outer),
            )
        for index in range(3):
            angle = index * math.pi * 0.82 + 0.3
            distance = self.size * (0.48 + detonation_progress * 0.34)
            painter.save()
            painter.translate(x + math.cos(angle) * distance, y + math.sin(angle) * distance)
            painter.rotate(math.degrees(angle) + 28.0)
            shard = QPainterPath()
            shard.moveTo(-self.size * 0.10, -self.size * 0.04)
            shard.lineTo(self.size * 0.13, -self.size * 0.06)
            shard.lineTo(self.size * 0.05, self.size * 0.07)
            shard.lineTo(-self.size * 0.14, self.size * 0.05)
            shard.closeSubpath()
            painter.setBrush(QBrush(QColor(248, 225, 174, int(185 * fade))))
            painter.setPen(QPen(QColor(255, 245, 205, int(220 * fade)), max(1.0, self.size * 0.02)))
            painter.drawPath(shard)
            painter.restore()
        painter.restore()


class AreaEffect(PrototypeEffect):
    """A ground-plane area effect that stays localized to a battlefield region."""

    primitive = "area"
    layer = "ground"

    def __init__(self, center, width=170.0, height=64.0, radius=None, lifetime=1.6,
                 pulse=True, fade=True, ground_plane=True, rune_marks=False,
                 color=(150, 240, 190), seed=303, delay=0.0):
        if radius is not None:
            width = float(radius) * 2.0
            height = float(radius) * 0.72
        center_point = _point(center)
        super().__init__(center_point, center_point, lifetime=lifetime, color=color, seed=seed, delay=delay)
        self.center = center_point
        self.width = max(2.0, float(width))
        self.height = max(2.0, float(height))
        self.radius = None if radius is None else float(radius)
        self.pulse = bool(pulse)
        self.fade = bool(fade)
        self.ground_plane = bool(ground_plane)
        self.rune_marks = bool(rune_marks)

    def draw(self, painter) -> None:
        if not self.has_started:
            return
        progress = self.progress
        fade_ratio = 1.0 - progress if self.fade else 1.0
        pulse_ratio = 1.0 + (0.08 * math.sin(progress * math.pi * 4.0) if self.pulse else 0.0)
        width = self.width * pulse_ratio
        height = self.height * pulse_ratio
        alpha = int(190 * fade_ratio)
        painter.save()
        painter.translate(self.center[0], self.center[1])
        if self.ground_plane:
            gradient = QRadialGradient(0, 0, max(width, height) * 0.58)
            gradient.setColorAt(0.0, _color(self.color, int(alpha * 0.62)))
            gradient.setColorAt(0.65, _color(self.color, int(alpha * 0.24)))
            gradient.setColorAt(1.0, _color(self.color, 0))
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(0, 0), width * 0.62, height * 0.70)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(_color(self.color, alpha), 2.0))
        painter.drawEllipse(QPointF(0, 0), width * 0.50, height * 0.50)
        painter.setPen(QPen(QColor(255, 255, 255, int(alpha * 0.62)), 1.0))
        painter.drawArc(QRectF(-width * 0.50, -height * 0.50, width, height), 20 * 16, 120 * 16)
        if self.rune_marks:
            painter.setPen(QPen(QColor(255, 250, 205, int(alpha * 0.58)), 1.0))
            for mark_idx in range(8):
                angle = math.radians(mark_idx * 45.0 + progress * 24.0)
                inner_x = math.cos(angle) * width * 0.27
                inner_y = math.sin(angle) * height * 0.27
                outer_x = math.cos(angle) * width * 0.42
                outer_y = math.sin(angle) * height * 0.42
                painter.drawLine(QPointF(inner_x, inner_y), QPointF(outer_x, outer_y))
        painter.restore()


class LightningEffect(PrototypeEffect):
    """Deterministic jagged lightning between arbitrary source and target points."""

    primitive = "lightning"

    def __init__(self, source, target, lifetime=0.42, segment_count=7,
                 visual_jitter=18.0, branching=False, color=(150, 210, 255), seed=404,
                 delay=0.0):
        super().__init__(source, target, lifetime=lifetime, color=color, seed=seed, delay=delay)
        self.segment_count = max(2, int(segment_count))
        self.visual_jitter = max(0.0, float(visual_jitter))
        self.branching = bool(branching)

    def draw(self, painter) -> None:
        if not self.has_started:
            return
        progress = self.progress
        alpha = int(255 * (1.0 - progress))
        _draw_crackling_lightning(
            painter,
            self.source,
            self.target,
            progress,
            self.color,
            alpha,
            jitter=self.visual_jitter,
            steps=self.segment_count,
            seed=self.seed,
        )
        if self.branching and progress < 0.75:
            midpoint = _lerp(self.source, self.target, 0.55)
            branch_target = (
                midpoint[0] + (self.target[1] - self.source[1]) * 0.22,
                midpoint[1] - (self.target[0] - self.source[0]) * 0.22,
            )
            _draw_crackling_lightning(
                painter,
                midpoint,
                branch_target,
                progress,
                self.color,
                int(alpha * 0.65),
                jitter=self.visual_jitter * 0.65,
                steps=max(3, self.segment_count // 2),
                seed=self.seed + 17,
            )


class ImpactEffect(PrototypeEffect):
    """Small reusable impact flash/ring/burst for presentation feedback."""

    primitive = "impact"
    layer = "impact"

    def __init__(self, position, size=26.0, lifetime=0.30, flash=True,
                 ring=True, burst=True, color=(255, 220, 130), seed=505, delay=0.0,
                 style="default", shard_count=6):
        super().__init__(position, position, lifetime=lifetime, color=color, seed=seed, delay=delay)
        self.position = _point(position)
        self.size = max(1.0, float(size))
        self.flash = bool(flash)
        self.ring = bool(ring)
        self.burst = bool(burst)
        self.style = str(style)
        self.shard_count = max(1, int(shard_count))

    def draw(self, painter) -> None:
        if not self.has_started:
            return
        progress = self.progress
        fade = 1.0 - progress
        x, y = self.position
        painter.save()
        if self.flash and progress < 0.22:
            flash_alpha = int(225 * (1.0 - progress / 0.22))
            painter.setBrush(QBrush(QColor(255, 255, 235, flash_alpha)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(x, y), self.size * 0.58, self.size * 0.42)
        if self.ring:
            radius = self.size * (0.28 + 0.95 * progress)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(_color(self.color, int(235 * fade)), max(1.2, self.size * 0.08 * fade)))
            painter.drawEllipse(QPointF(x, y), radius, radius * 0.62)
        if self.burst:
            rnd = random.Random(self.seed)
            painter.setPen(QPen(QColor(255, 248, 210, int(220 * fade)), max(1.0, self.size * 0.055)))
            for idx in range(8):
                angle = rnd.uniform(0.0, math.pi * 2.0)
                inner = self.size * (0.22 + progress * 0.18)
                outer = self.size * (0.52 + progress * 0.80)
                painter.drawLine(
                    QPointF(x + math.cos(angle) * inner, y + math.sin(angle) * inner * 0.7),
                    QPointF(x + math.cos(angle) * outer, y + math.sin(angle) * outer * 0.7),
                )
        if self.style == "angular_shard":
            self._draw_angular_shards(painter, x, y, fade)
        elif self.style == "cross_cut":
            self._draw_cross_cut(painter, x, y, fade)
        elif self.style == "fan_cut":
            self._draw_fan_cut(painter, x, y, fade)
        elif self.style == "ground_crack":
            self._draw_ground_cracks(painter, x, y, fade)
        painter.restore()

    def _draw_angular_shards(self, painter, x, y, fade):
        rnd = random.Random(self.seed + 31)
        painter.setPen(QPen(_color(self.color, int(230 * fade)), max(1.0, self.size * 0.045)))
        for index in range(self.shard_count):
            angle = index * math.pi / 3.0 + rnd.uniform(-0.08, 0.08)
            inner = self.size * (0.32 + self.progress * 0.14)
            outer = self.size * (0.70 + self.progress * 0.58)
            painter.drawLine(
                QPointF(x + math.cos(angle) * inner, y + math.sin(angle) * inner),
                QPointF(x + math.cos(angle) * outer, y + math.sin(angle) * outer),
            )

    def _draw_cross_cut(self, painter, x, y, fade):
        span = self.size * (0.42 + self.progress * 0.46)
        painter.setPen(QPen(QColor(248, 232, 255, int(235 * fade)), max(1.1, self.size * 0.045)))
        for angle in (-28.0, 28.0):
            radians = math.radians(angle)
            painter.drawLine(
                QPointF(x - math.cos(radians) * span, y - math.sin(radians) * span),
                QPointF(x + math.cos(radians) * span, y + math.sin(radians) * span),
            )
        ghost_span = span * 0.72
        painter.setPen(QPen(QColor(135, 94, 195, int(135 * fade)), max(1.0, self.size * 0.025)))
        painter.drawLine(
            QPointF(x - ghost_span * 0.92, y - self.size * 0.16),
            QPointF(x + ghost_span * 0.92, y - self.size * 0.16),
        )
        painter.drawLine(
            QPointF(x - self.size * 0.16, y - ghost_span * 0.92),
            QPointF(x + self.size * 0.16, y + ghost_span * 0.92),
        )

    def _draw_fan_cut(self, painter, x, y, fade):
        """Draw several small cut marks as a fan, not an expanding blast."""
        painter.setPen(QPen(_color(self.color, int(225 * fade)), max(1.0, self.size * 0.040)))
        for index in range(5):
            offset = (index - 2) * self.size * 0.19
            angle = math.radians(-24.0 + index * 12.0)
            center_x = x + offset
            center_y = y + abs(index - 2) * self.size * 0.045
            span = self.size * (0.22 + self.progress * 0.16)
            direction_x = math.cos(angle)
            direction_y = math.sin(angle)
            painter.drawLine(
                QPointF(center_x - direction_x * span, center_y - direction_y * span),
                QPointF(center_x + direction_x * span, center_y + direction_y * span),
            )

    def _draw_ground_cracks(self, painter, x, y, fade):
        rnd = random.Random(self.seed + 53)
        base_y = y + self.size * 0.20
        painter.setPen(QPen(_color(self.color, int(235 * fade)), max(1.2, self.size * 0.050)))
        for branch in (-1, 0, 1):
            direction = -1.0 if branch < 0 else 1.0
            if branch == 0:
                direction = 1.0
            path = QPainterPath(QPointF(x + branch * self.size * 0.10, base_y))
            for step in range(1, 4):
                path.lineTo(QPointF(
                    x + branch * self.size * 0.10 + direction * step * self.size * (0.28 + rnd.random() * 0.10),
                    base_y + (rnd.random() - 0.5) * self.size * 0.18 + step * self.size * 0.035,
                ))
            painter.drawPath(path)


class PersistentEffect(PrototypeEffect):
    """A reusable retained presentation visual with normal manager cleanup.

    ``style`` intentionally describes a visual family (currently ``aura`` or
    ``sword``), not a Hero state.  Callers own the lifetime they want to show;
    the effect never grants a buff, resource, cooldown, or gameplay outcome.
    """

    primitive = "persistent"

    def __init__(self, position, style="aura", lifetime=8.0, size=72.0,
                 color=(120, 220, 255), pulse_speed=2.0, offset=(0.0, 0.0),
                 layer=None, seed=606, delay=0.0):
        super().__init__(position, position, lifetime=lifetime, color=color, seed=seed, delay=delay)
        self.position = _point(position)
        self.style = str(style)
        self.size = max(1.0, float(size))
        self.pulse_speed = float(pulse_speed)
        self.offset = _point(offset)
        self.layer = str(layer or ("before_avatar" if self.style == "aura" else "after_avatar"))

    def draw(self, painter) -> None:
        if not self.has_started:
            return
        elapsed = self.duration * self.progress
        pulse = 0.72 + 0.28 * math.sin(elapsed * self.pulse_speed)
        x = self.position[0] + self.offset[0]
        y = self.position[1] + self.offset[1]
        painter.save()
        if self.style == "sword":
            self._draw_sword(painter, x, y, pulse)
        else:
            self._draw_aura(painter, x, y, pulse)
        painter.restore()

    def _draw_sword(self, painter, x, y, pulse):
        blade_height = self.size * 1.45
        blade_width = self.size * 0.20
        top = y - blade_height * 0.5
        bottom = y + blade_height * 0.5
        painter.setPen(QPen(QColor(255, 109, 53, int(85 * pulse)), max(6.0, self.size * 0.34), Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(x, top), QPointF(x, bottom))
        blade = QPainterPath()
        blade.moveTo(QPointF(x - blade_width, top))
        blade.lineTo(QPointF(x + blade_width, top))
        blade.lineTo(QPointF(x, bottom + blade_width * 0.9))
        blade.closeSubpath()
        painter.setBrush(QColor(255, 188, 91, int(210 * pulse)))
        painter.setPen(QPen(QColor(255, 246, 186, int(235 * pulse)), 1.3))
        painter.drawPath(blade)
        painter.setPen(QPen(QColor(255, 105, 45, int(220 * pulse)), max(1.5, self.size * 0.07), Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(x - blade_width * 2.1, y), QPointF(x + blade_width * 2.1, y))

    def _draw_aura(self, painter, x, y, pulse):
        radius_x = self.size * (1.0 + 0.012 * pulse)
        radius_y = self.size * (0.30 + 0.008 * pulse)
        painter.setBrush(QColor(81, 204, 255, int(16 * pulse)))
        painter.setPen(QPen(QColor(126, 235, 255, int(92 * pulse)), max(1.5, self.size * 0.035), Qt.DashLine))
        painter.drawEllipse(QRectF(x - radius_x, y - radius_y, radius_x * 2, radius_y * 2))
        painter.setPen(QPen(QColor(207, 252, 255, int(95 * pulse)), max(1.0, self.size * 0.022), Qt.SolidLine, Qt.RoundCap))
        for angle in (-35, 35, 145, 215):
            direction = QPointF(math.cos(math.radians(angle)), math.sin(math.radians(angle)))
            painter.drawLine(
                QPointF(x + direction.x() * radius_x * 0.65, y + direction.y() * radius_y * 0.65),
                QPointF(x + direction.x() * radius_x * 0.92, y + direction.y() * radius_y * 0.92),
            )


@dataclass(frozen=True)
class VFXPreset:
    """Presentation-only construction data for a reusable visual."""

    name: str
    effect_type: str
    params: Mapping[str, object] = field(default_factory=dict)


CANNONEER_CANNON_BARRAGE_SKILL_ID = "cannon_barrage"
CANNONEER_MONKEY_ASSIST_SKILL_ID = "monkey_assist"

_CANNON_BARRAGE_PARAMS = {
    "speed": 235.0,
    "size": 34.0,
    "lifetime": 1.60,
    "trail": True,
    "trail_length": 0.24,
    "shape": "cannonball",
    "style": "cannon_combo",
    "visual_shots": 4,
    "shot_spacing": 0.18,
    "shot_travel": 0.86,
    "landing_spread": 0.90,
    "recoil_scale": 1.0,
    "muzzle_flash": True,
    "color": (255, 145, 70),
    "seed": 1303,
}

_MONKEY_ASSIST_PARAMS = {
    "speed": 300.0,
    "size": 24.0,
        "lifetime": 1.30,
    "trail": True,
    "trail_length": 0.12,
    "shape": "assist_orb",
    "style": "monkey_assist",
        "assist_delay": 0.28,
        "assist_travel": 0.62,
        "assist_impact_window": 0.72,
    "companion_offset": (-52.0, -26.0),
    "color": (255, 166, 72),
    "seed": 1304,
}


PRESETS = {
    "hero_slash": VFXPreset(
        "hero_slash", "slash",
        {"size": 104.0, "lifetime": 0.55, "arc": 118.0, "color": (255, 215, 90), "seed": 1101},
    ),
    "hero_rage_attack": VFXPreset(
        "hero_rage_attack", "slash",
        {"size": 104.0, "lifetime": 0.55, "arc": 118.0, "color": (255, 215, 90), "seed": 2101},
    ),
    "hero_sword_illusion": VFXPreset(
        "hero_sword_illusion", "slash",
        {"size": 104.0, "lifetime": 0.55, "arc": 118.0, "color": (255, 224, 130), "seed": 2102},
    ),
    "hero_burning_soul_sword": VFXPreset(
        "hero_burning_soul_sword", "persistent",
        {"style": "sword", "lifetime": 8.0, "size": 28.0,
         "color": (255, 142, 55), "layer": "after_avatar", "seed": 2103},
    ),
    "hero_spatial_slash": VFXPreset(
        "hero_spatial_slash", "slash",
        {"style": "rift", "variant": "normal", "size": 112.0, "lifetime": 0.52,
         "color": (105, 204, 255), "seed": 2104},
    ),
    "hero_fighting_instinct": VFXPreset(
        "hero_fighting_instinct", "persistent",
        {"style": "aura", "lifetime": 8.0, "size": 88.0,
         "color": (116, 228, 255), "layer": "before_avatar", "seed": 2105},
    ),
    "hero_sacred_sword_descent": VFXPreset(
        "hero_sacred_sword_descent", "projectile",
        {"speed": 560.0, "size": 28.0, "lifetime": 0.38, "trail": True,
         "trail_length": 0.20, "shape": "sword", "variant": "normal",
         "color": (189, 232, 255), "seed": 2106},
    ),
    "night_lord_shuriken": VFXPreset(
        "night_lord_shuriken", "projectile",
        {"speed": 720.0, "size": 13.0, "lifetime": 0.48, "trail": True,
         "trail_length": 0.10, "shape": "shuriken", "color": (176, 132, 255), "seed": 1202},
    ),
    "night_lord_four_flying": VFXPreset(
        "night_lord_four_flying", "projectile",
        {"speed": 1080.0, "size": 8.0, "lifetime": 0.28, "trail": True,
         "trail_length": 0.055, "shape": "shuriken", "spin_rate": 720.0,
         "color": (205, 168, 255), "seed": 2201},
    ),
    "night_lord_taunt_contract": VFXPreset(
        "night_lord_taunt_contract", "mark",
        {"size": 42.0, "mark_lifetime": 1.15, "detonation": False,
         "color": (219, 128, 255), "seed": 2202, "style": "contract"},
    ),
    "night_lord_fuma_shuriken": VFXPreset(
        "night_lord_fuma_shuriken", "projectile",
        {"speed": 420.0, "size": 46.0, "lifetime": 0.44, "trail": True,
         "trail_length": 0.34, "shape": "shuriken", "style": "heavy_shuriken",
         "spin_rate": 1800.0, "wind_streaks": 1, "trail_width_scale": 0.26,
         "color": (191, 143, 255), "seed": 2203},
    ),
    "night_lord_dakrus_secret": VFXPreset(
        "night_lord_dakrus_secret", "projectile",
        {"speed": 600.0, "size": 20.0, "lifetime": 0.46, "trail": True,
         "trail_length": 0.20, "shape": "shuriken", "style": "secret_route",
         "spin_rate": 1080.0, "color": (124, 91, 190), "seed": 2204},
    ),
    "night_lord_spread_throw": VFXPreset(
        "night_lord_spread_throw", "spread",
        {"projectile_count": 5, "spread_angle": 88.0, "fan_radius": 70.0,
         "speed": 560.0, "size": 10.0, "lifetime": 0.46, "trail": True,
         "trail_length": 0.09, "shape": "shuriken", "style": "fan_burst",
         "color": (182, 136, 255), "seed": 2205},
    ),
    "night_lord_detonation_talisman": VFXPreset(
        "night_lord_detonation_talisman", "mark",
        {"size": 46.0, "mark_lifetime": 0.20, "detonation_delay": 0.14,
         "detonation_lifetime": 0.30, "detonation": True,
         "color": (244, 146, 255), "seed": 2206, "style": "talisman"},
    ),
    # ``cannon_barrage`` follows the existing gameplay skill id. The Gallery
    # currently binds its Cannon slot to ``cannonball_heavy``; keep that
    # presentation id as a compatibility alias until Gallery work is in scope.
    CANNONEER_CANNON_BARRAGE_SKILL_ID: VFXPreset(
        CANNONEER_CANNON_BARRAGE_SKILL_ID, "projectile", dict(_CANNON_BARRAGE_PARAMS),
    ),
    "cannonball_heavy": VFXPreset(
        "cannonball_heavy", "projectile", dict(_CANNON_BARRAGE_PARAMS),
    ),
    CANNONEER_MONKEY_ASSIST_SKILL_ID: VFXPreset(
        CANNONEER_MONKEY_ASSIST_SKILL_ID, "projectile", dict(_MONKEY_ASSIST_PARAMS),
    ),
    "bishop_holy_area": VFXPreset(
        "bishop_holy_area", "area",
        {"width": 190.0, "height": 72.0, "lifetime": 1.80, "pulse": True, "fade": True,
         "ground_plane": True, "rune_marks": True, "color": (255, 224, 140), "seed": 1404},
    ),
}


def resolve_preset(name: str) -> VFXPreset:
    try:
        return PRESETS[name]
    except KeyError as exc:
        raise KeyError(f"Unknown VFX preset: {name}") from exc


def create_effect(preset: str | VFXPreset, source, target=None, **overrides) -> PrototypeEffect:
    definition = resolve_preset(preset) if isinstance(preset, str) else preset
    params = dict(definition.params)
    params.update(overrides)
    if definition.effect_type == "slash":
        return SlashEffect(source, target if target is not None else source, **params)
    if definition.effect_type == "projectile":
        if target is None:
            raise ValueError("Projectile presets require a target position")
        return ProjectileEffect(source, target, **params)
    if definition.effect_type == "spread":
        if target is None:
            raise ValueError("Spread presets require a target position")
        return SpreadProjectileEffect(source, target, **params)
    if definition.effect_type == "mark":
        position = target if target is not None else source
        return MarkDetonationEffect(position, source=source, **params)
    if definition.effect_type == "area":
        # Area presets target a battlefield region; an explicit center wins,
        # otherwise use the target point when one is supplied.
        return AreaEffect(params.pop("center", target if target is not None else source), **params)
    if definition.effect_type == "persistent":
        return PersistentEffect(source, **params)
    raise ValueError(f"Unsupported VFX preset type: {definition.effect_type}")


def emit_vfx(manager, preset: str | VFXPreset, source, target=None, **overrides) -> PrototypeEffect:
    """Create a preset effect and enqueue it in the shared visual manager."""
    effect = create_effect(preset, source, target, **overrides)
    manager.add_effect(effect)
    return effect


__all__ = [
    "AreaEffect",
    "CANNONEER_CANNON_BARRAGE_SKILL_ID",
    "CANNONEER_MONKEY_ASSIST_SKILL_ID",
    "ImpactEffect",
    "LightningEffect",
    "MarkDetonationEffect",
    "PRESETS",
    "PersistentEffect",
    "ProjectileEffect",
    "PrototypeEffect",
    "SlashEffect",
    "SpreadProjectileEffect",
    "VFXPreset",
    "create_effect",
    "emit_vfx",
    "resolve_preset",
]
