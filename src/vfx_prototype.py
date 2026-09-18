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
from PySide6.QtGui import QColor, QBrush, QPainterPath, QPen, QRadialGradient

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
                 style="ribbon", variant="normal", alpha_scale=1.0):
        super().__init__(source, target, lifetime=lifetime, color=color, seed=seed, delay=delay)
        self.size = float(size)
        self.arc = float(arc)
        self.angle = None if angle is None else float(angle)
        self.fade = bool(fade)
        self.style = str(style)
        self.variant = str(variant)
        self.alpha_scale = max(0.0, float(alpha_scale))

    def draw(self, painter) -> None:
        if not self.has_started:
            return
        if self.style == "rift":
            self._draw_rift(painter)
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
                 shape="default", trail_length=0.12, delay=0.0, variant="normal"):
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
        position = self.position
        alpha = int(255 * (1.0 - self.progress))
        if self.trail:
            trail_start = _lerp(self.source, position, max(0.0, self.progress - self.trail_length))
            trail_width = self.size * (0.25 if self.shape == "shuriken" else 0.38)
            _draw_bloom_line(painter, trail_start, position, trail_width, self.color, int(alpha * 0.75))

        dx = self.target[0] - self.source[0]
        dy = self.target[1] - self.source[1]
        length = max(1.0, math.hypot(dx, dy))
        nx, ny = dx / length, dy / length
        px, py = -ny, nx
        tip = (position[0] + nx * self.size * 0.85, position[1] + ny * self.size * 0.85)
        left = (position[0] - nx * self.size * 0.7 + px * self.size * 0.62,
                position[1] - ny * self.size * 0.7 + py * self.size * 0.62)
        right = (position[0] - nx * self.size * 0.7 - px * self.size * 0.62,
                 position[1] - ny * self.size * 0.7 - py * self.size * 0.62)
        if self.shape == "shuriken":
            _draw_shuriken(
                painter, position[0], position[1],
                self.progress * 980.0 + self.seed,
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
                 ring=True, burst=True, color=(255, 220, 130), seed=505, delay=0.0):
        super().__init__(position, position, lifetime=lifetime, color=color, seed=seed, delay=delay)
        self.position = _point(position)
        self.size = max(1.0, float(size))
        self.flash = bool(flash)
        self.ring = bool(ring)
        self.burst = bool(burst)

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
        painter.restore()


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
    "cannonball_heavy": VFXPreset(
        "cannonball_heavy", "projectile",
        {"speed": 270.0, "size": 29.0, "lifetime": 1.15, "trail": True,
         "trail_length": 0.18, "shape": "cannonball", "color": (255, 145, 70), "seed": 1303},
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
    "ImpactEffect",
    "LightningEffect",
    "PRESETS",
    "PersistentEffect",
    "ProjectileEffect",
    "PrototypeEffect",
    "SlashEffect",
    "VFXPreset",
    "create_effect",
    "emit_vfx",
    "resolve_preset",
]
