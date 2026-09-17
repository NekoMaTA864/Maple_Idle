"""Small presentation-only combat avatars for the vertical arena.

An avatar is a weapon or class-symbol silhouette, not a gameplay entity.  The
definitions below expose only visual anchors and a tiny pose timer so the arena
and the Debug Gallery can use the same source points for VFX.
"""

from dataclasses import dataclass
import math
from typing import Mapping

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainterPath,
    QPen,
    QPolygonF,
    QRadialGradient,
)


Point = tuple[float, float]


@dataclass(frozen=True)
class CombatAvatarDefinition:
    """Static visual data; no combat or progression values are stored here."""

    avatar_id: str
    label: str
    silhouette: str
    color: tuple[int, int, int]
    size: float
    anchors: Mapping[str, Point]


AVATAR_DEFINITIONS = {
    "hero": CombatAvatarDefinition(
        "hero", "Sword", "sword", (255, 211, 86), 1.0,
        {"center": (0.0, 0.0), "attack_origin": (0.0, -18.0),
         "tip": (0.0, -54.0), "ground": (0.0, 30.0), "muzzle": (0.0, -54.0)},
    ),
    "night_lord": CombatAvatarDefinition(
        "night_lord", "Claw / Shuriken", "shuriken", (181, 132, 255), 0.92,
        {"center": (0.0, 0.0), "attack_origin": (0.0, -9.0),
         "tip": (0.0, -25.0), "ground": (0.0, 24.0)},
    ),
    "cannon": CombatAvatarDefinition(
        "cannon", "Heavy Cannon", "cannon", (255, 145, 70), 1.0,
        {"center": (0.0, 0.0), "attack_origin": (0.0, -42.0),
         "tip": (0.0, -48.0), "ground": (0.0, 30.0), "muzzle": (0.0, -50.0)},
    ),
    "bishop": CombatAvatarDefinition(
        "bishop", "Holy Staff", "staff", (255, 226, 145), 0.98,
        {"center": (0.0, 0.0), "attack_origin": (0.0, -42.0),
         "tip": (0.0, -51.0), "ground": (0.0, 29.0)},
    ),
}


def _clamp(value, low=0.0, high=1.0):
    return max(low, min(high, float(value)))


def _qcolor(rgb, alpha=255):
    return QColor(int(rgb[0]), int(rgb[1]), int(rgb[2]), int(_clamp(alpha, 0, 255)))


def _rotated(offset: Point, degrees: float, scale: float) -> Point:
    radians = math.radians(degrees)
    x = offset[0] * scale
    y = offset[1] * scale
    return (
        x * math.cos(radians) - y * math.sin(radians),
        x * math.sin(radians) + y * math.cos(radians),
    )


class CombatAvatar:
    """Weapon-symbol avatar with a deliberately tiny animation state."""

    ATTACK_DURATION = 0.42

    def __init__(self, avatar_id="hero"):
        self.animation_time = 0.0
        self.attack_elapsed = self.ATTACK_DURATION
        self.set_avatar(avatar_id)

    @property
    def definition(self) -> CombatAvatarDefinition:
        return self._definition

    @property
    def avatar_id(self) -> str:
        return self._definition.avatar_id

    @property
    def is_attacking(self) -> bool:
        return self.attack_elapsed < self.ATTACK_DURATION

    def set_avatar(self, avatar_id: str) -> None:
        try:
            self._definition = AVATAR_DEFINITIONS[str(avatar_id)]
        except KeyError as exc:
            raise KeyError(f"Unknown combat avatar: {avatar_id}") from exc
        self.attack_elapsed = self.ATTACK_DURATION

    def trigger_attack(self) -> None:
        self.attack_elapsed = 0.0

    def update(self, dt: float) -> None:
        self.animation_time += max(0.0, float(dt))
        self.attack_elapsed = min(self.ATTACK_DURATION, self.attack_elapsed + max(0.0, float(dt)))

    def _pose(self):
        t = self.animation_time
        idle_float = math.sin(t * 2.4) * 2.0
        rotation = math.sin(t * 1.8) * 2.5
        scale = 1.0
        translation = (0.0, idle_float)
        attack_t = _clamp(self.attack_elapsed / self.ATTACK_DURATION)
        attack_burst = math.sin(math.pi * attack_t) if self.is_attacking else 0.0

        if self.is_attacking:
            if self.avatar_id == "hero":
                rotation += -52.0 + 104.0 * attack_t
                translation = (0.0, idle_float - 4.0 * attack_burst)
            elif self.avatar_id == "night_lord":
                rotation += 360.0 * attack_t
                translation = (0.0, idle_float - 9.0 * attack_burst)
                scale += 0.06 * attack_burst
            elif self.avatar_id == "cannon":
                translation = (0.0, idle_float + 8.0 * attack_burst)
                scale += 0.025 * attack_burst
            elif self.avatar_id == "bishop":
                translation = (0.0, idle_float - 3.0 * attack_burst)
                scale += 0.14 * attack_burst
        elif self.avatar_id == "night_lord":
            scale += 0.045 * (0.5 + 0.5 * math.sin(t * 4.2))
        elif self.avatar_id == "bishop":
            scale += 0.045 * (0.5 + 0.5 * math.sin(t * 2.2))

        return rotation, self._definition.size * scale, translation, attack_t

    def anchor(self, name: str, center=(0.0, 0.0)) -> Point:
        """Resolve a visual anchor in canvas coordinates."""
        if name not in self._definition.anchors:
            raise KeyError(f"Unknown {self.avatar_id} avatar anchor: {name}")
        rotation, scale, translation, _attack_t = self._pose()
        offset = _rotated(self._definition.anchors[name], rotation, scale)
        return (float(center[0]) + translation[0] + offset[0],
                float(center[1]) + translation[1] + offset[1])

    def anchors(self, center=(0.0, 0.0)) -> dict[str, Point]:
        return {name: self.anchor(name, center) for name in self._definition.anchors}

    def draw(self, painter, center=(0.0, 0.0)) -> None:
        """Draw the weapon/class symbol; never draws a human-shaped sprite."""
        rotation, scale, translation, attack_t = self._pose()
        x = float(center[0]) + translation[0]
        y = float(center[1]) + translation[1]
        glow = 155 if self.is_attacking else 108

        painter.save()
        painter.translate(x, y)
        painter.rotate(rotation)
        painter.scale(scale, scale)
        painter.setPen(Qt.NoPen)

        glow_gradient = QRadialGradient(0, 0, 42)
        glow_gradient.setColorAt(0.0, _qcolor(self._definition.color, glow))
        glow_gradient.setColorAt(0.65, _qcolor(self._definition.color, int(glow * 0.28)))
        glow_gradient.setColorAt(1.0, _qcolor(self._definition.color, 0))
        painter.setBrush(QBrush(glow_gradient))
        painter.drawEllipse(QPointF(0, 0), 42, 26)

        if self.avatar_id == "hero":
            self._draw_sword(painter, glow)
        elif self.avatar_id == "night_lord":
            self._draw_shuriken_symbol(painter, glow, attack_t)
        elif self.avatar_id == "cannon":
            self._draw_cannon(painter, glow, attack_t)
        else:
            self._draw_staff(painter, glow, attack_t)
        painter.restore()

    def _draw_sword(self, painter, glow):
        blade = QPainterPath()
        blade.moveTo(QPointF(-5, 13))
        blade.lineTo(QPointF(5, 13))
        blade.lineTo(QPointF(4, -32))
        blade.lineTo(QPointF(0, -53))
        blade.lineTo(QPointF(-4, -32))
        blade.closeSubpath()
        gradient = QLinearGradient(0, -53, 0, 13)
        gradient.setColorAt(0.0, QColor(255, 255, 255, 245))
        gradient.setColorAt(0.38, QColor(255, 239, 165, 245))
        gradient.setColorAt(1.0, _qcolor(self._definition.color, 235))
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(255, 255, 255, 230), 1.2))
        painter.drawPath(blade)
        painter.setPen(QPen(QColor(255, 248, 190, glow), 4.0, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(-17, 12), QPointF(17, 12))
        painter.setPen(QPen(QColor(116, 67, 30, 240), 5.0, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(0, 14), QPointF(0, 27))
        painter.setPen(QPen(QColor(255, 255, 255, 220), 1.0))
        painter.drawArc(QRectF(-18, -19, 36, 30), 18 * 16, 118 * 16)

    def _draw_shuriken_symbol(self, painter, glow, attack_t):
        size = 20.0
        path = QPainterPath()
        path.moveTo(QPointF(0, -size))
        path.lineTo(QPointF(5, -5))
        path.lineTo(QPointF(size, 0))
        path.lineTo(QPointF(5, 5))
        path.lineTo(QPointF(0, size))
        path.lineTo(QPointF(-5, 5))
        path.lineTo(QPointF(-size, 0))
        path.lineTo(QPointF(-5, -5))
        path.closeSubpath()
        painter.setBrush(QBrush(_qcolor(self._definition.color, 225)))
        painter.setPen(QPen(QColor(255, 255, 255, glow), 1.3))
        painter.drawPath(path)
        painter.setBrush(QBrush(QColor(255, 255, 255, glow)))
        painter.drawEllipse(QPointF(0, 0), 4.5, 4.5)
        painter.setPen(QPen(QColor(212, 182, 255, int(glow * 0.9)), 2.0, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(-28, 10), QPointF(-11, 3))
        painter.drawLine(QPointF(11, -3), QPointF(28, -10))
        if self.is_attacking:
            painter.setPen(QPen(QColor(255, 255, 255, int(220 * (1.0 - attack_t))), 1.4))
            painter.drawEllipse(QPointF(0, 0), 26 + 8 * attack_t, 26 + 8 * attack_t)

    def _draw_cannon(self, painter, glow, attack_t):
        barrel_gradient = QLinearGradient(-12, -50, 12, 12)
        barrel_gradient.setColorAt(0.0, QColor(255, 225, 185, 245))
        barrel_gradient.setColorAt(0.35, _qcolor(self._definition.color, 245))
        barrel_gradient.setColorAt(1.0, QColor(116, 63, 44, 240))
        painter.setBrush(QBrush(barrel_gradient))
        painter.setPen(QPen(QColor(255, 230, 180, 220), 1.3))
        painter.drawRoundedRect(QRectF(-12, -48, 24, 56), 8, 8)
        painter.setBrush(QBrush(QColor(58, 43, 52, 245)))
        painter.drawEllipse(QPointF(0, -49), 15, 7)
        painter.setPen(QPen(QColor(255, 180, 90, glow), 3.0))
        painter.drawLine(QPointF(-19, 8), QPointF(19, 8))
        painter.setBrush(QBrush(QColor(85, 68, 82, 245)))
        painter.setPen(QPen(QColor(255, 190, 100, 190), 1.0))
        painter.drawEllipse(QPointF(0, 11), 18, 12)
        if self.is_attacking and attack_t < 0.25:
            flash = 1.0 - attack_t / 0.25
            painter.setBrush(QBrush(QColor(255, 248, 190, int(240 * flash))))
            painter.setPen(QPen(QColor(255, 178, 62, int(235 * flash)), 2.0))
            points = QPolygonF([
                QPointF(-16 * flash, -53), QPointF(-6, -69 * flash),
                QPointF(0, -55), QPointF(8, -73 * flash),
                QPointF(18 * flash, -53), QPointF(7, -44),
                QPointF(-8, -44),
            ])
            painter.drawPolygon(points)

    def _draw_staff(self, painter, glow, attack_t):
        painter.setPen(QPen(QColor(255, 244, 190, 240), 4.0, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(0, 28), QPointF(0, -43))
        focus_radius = 13.0 + (6.0 * math.sin(math.pi * attack_t) if self.is_attacking else 0.0)
        focus_gradient = QRadialGradient(0, -49, focus_radius * 1.8)
        focus_gradient.setColorAt(0.0, QColor(255, 255, 255, glow))
        focus_gradient.setColorAt(0.48, _qcolor(self._definition.color, int(glow * 0.9)))
        focus_gradient.setColorAt(1.0, QColor(255, 205, 95, 0))
        painter.setBrush(QBrush(focus_gradient))
        painter.setPen(QPen(QColor(255, 248, 190, glow), 1.4))
        painter.drawEllipse(QPointF(0, -49), focus_radius, focus_radius)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, int(glow * 0.85)), 1.2))
        painter.drawEllipse(QPointF(0, -49), focus_radius * 1.55, focus_radius * 0.58)
        painter.drawLine(QPointF(-18, -49), QPointF(18, -49))
        painter.drawLine(QPointF(0, -66), QPointF(0, -32))


def draw_enemy_emblem(painter, center, is_boss=False, is_elite=False, pulse=0.0):
    """Draw an abstract enemy core/emblem instead of a character placeholder."""
    x, y = float(center[0]), float(center[1])
    base = (177, 82, 108) if not is_boss else (180, 100, 236)
    if is_elite:
        base = (230, 166, 67)
    radius = 32.0 if is_boss else 24.0
    radius += 2.5 * math.sin(pulse * math.pi * 2.0)

    painter.save()
    glow = QRadialGradient(x, y, radius * 1.8)
    glow.setColorAt(0.0, _qcolor(base, 110))
    glow.setColorAt(0.6, _qcolor(base, 36))
    glow.setColorAt(1.0, _qcolor(base, 0))
    painter.setBrush(QBrush(glow))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(QPointF(x, y), radius * 1.65, radius * 1.2)

    painter.translate(x, y)
    painter.rotate(pulse * (12.0 if is_boss else -8.0))
    painter.setBrush(QBrush(_qcolor(base, 225)))
    painter.setPen(QPen(QColor(255, 255, 255, 195), 1.5))
    if is_boss:
        points = QPolygonF()
        for idx in range(8):
            angle = math.radians(idx * 45.0 - 22.5)
            points.append(QPointF(math.cos(angle) * radius, math.sin(angle) * radius * 0.82))
        painter.drawPolygon(points)
        painter.setBrush(QBrush(QColor(72, 36, 110, 235)))
        painter.drawEllipse(QPointF(0, 0), radius * 0.48, radius * 0.42)
        painter.setPen(QPen(QColor(255, 230, 160, 230), 1.8))
        painter.drawEllipse(QPointF(0, 0), radius * 0.72, radius * 0.55)
    else:
        points = QPolygonF([
            QPointF(0, -radius), QPointF(radius * 0.58, -radius * 0.32),
            QPointF(radius, 0), QPointF(radius * 0.42, radius * 0.45),
            QPointF(0, radius * 0.78), QPointF(-radius * 0.42, radius * 0.45),
            QPointF(-radius, 0), QPointF(-radius * 0.58, -radius * 0.32),
        ])
        painter.drawPolygon(points)
        painter.setBrush(QBrush(QColor(62, 35, 58, 230)))
        painter.drawEllipse(QPointF(0, 0), radius * 0.38, radius * 0.46)
        painter.setPen(QPen(QColor(255, 185, 145, 210), 1.3))
        painter.drawLine(QPointF(-radius * 0.25, -radius * 0.08), QPointF(radius * 0.25, radius * 0.08))
    painter.restore()


__all__ = [
    "AVATAR_DEFINITIONS",
    "CombatAvatar",
    "CombatAvatarDefinition",
    "draw_enemy_emblem",
]
