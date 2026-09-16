"""Small, stateless presentation helpers and local effect state."""

import math
from dataclasses import dataclass

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen


@dataclass
class EffectState:
    """One presentation-only effect instance; no damage or combat semantics."""

    effect_id: str
    age: float
    duration: float
    origin: QPointF
    target: QPointF
    target_ground: QPointF
    variant: str = "normal"


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def lerp_point(start: QPointF, end: QPointF, progress: float) -> QPointF:
    return QPointF(start.x() + (end.x() - start.x()) * progress, start.y() + (end.y() - start.y()) * progress)


def draw_hero_slash(painter: QPainter, effect: EffectState, area: QRectF) -> None:
    slash_progress = (effect.age - 0.035) / 0.34
    if not 0.0 <= slash_progress <= 1.0:
        return
    fade = min(clamp01(slash_progress / 0.16), clamp01((1.0 - slash_progress) / 0.28))
    radius_x = area.width() * 0.23
    radius_y = area.height() * 0.055
    target = effect.target
    slash_center = QPointF(target.x(), target.y() + area.height() * 0.015)
    start = QPointF(slash_center.x() - radius_x, slash_center.y() + radius_y * 0.90)
    end = QPointF(slash_center.x() + radius_x, slash_center.y() + radius_y * 0.90)
    slash = QPainterPath()
    slash.moveTo(start)
    slash.cubicTo(
        QPointF(slash_center.x() - radius_x * 0.62, slash_center.y() - radius_y * 1.65),
        QPointF(slash_center.x() + radius_x * 0.62, slash_center.y() - radius_y * 1.65),
        end,
    )
    painter.save()
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QColor(92, 193, 255, int(100 * fade)), max(7.0, area.width() * 0.017), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawPath(slash)
    painter.setPen(QPen(QColor(224, 248, 255, int(230 * fade)), max(2.0, area.width() * 0.005), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawPath(slash)
    painter.restore()


def _draw_slash_arc(
    painter: QPainter,
    center: QPointF,
    area: QRectF,
    progress: float,
    scale: float,
    alpha: float,
) -> None:
    """Draw one lightweight arc used by the Hero phantom presentation."""
    fade = min(clamp01(progress / 0.16), clamp01((1.0 - progress) / 0.28)) * alpha
    radius_x = area.width() * 0.23 * scale
    radius_y = area.height() * 0.055 * scale
    start = QPointF(center.x() - radius_x, center.y() + radius_y * 0.90)
    end = QPointF(center.x() + radius_x, center.y() + radius_y * 0.90)
    slash = QPainterPath()
    slash.moveTo(start)
    slash.cubicTo(
        QPointF(center.x() - radius_x * 0.62, center.y() - radius_y * 1.65),
        QPointF(center.x() + radius_x * 0.62, center.y() - radius_y * 1.65),
        end,
    )
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QColor(75, 151, 255, int(90 * fade)), max(5.0, area.width() * 0.014), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawPath(slash)
    painter.setPen(QPen(QColor(200, 235, 255, int(205 * fade)), max(1.5, area.width() * 0.004), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawPath(slash)


def draw_hero_phantom_slash(painter: QPainter, effect: EffectState, area: QRectF) -> None:
    """Draw the main slash plus delayed phantom copies for Sword Illusion."""
    draw_hero_slash(painter, effect, area)
    slash_center = QPointF(effect.target.x(), effect.target.y() + area.height() * 0.015)
    delays = (0.16,) if effect.variant != "enhanced" else (0.13, 0.26)
    ghost_alpha = 0.48 if effect.variant != "enhanced" else 0.72
    for index, delay in enumerate(delays, start=1):
        local_age = effect.age - delay
        progress = (local_age - 0.035) / 0.30
        if 0.0 <= progress <= 1.0:
            _draw_slash_arc(painter, slash_center, area, progress, 1.0 - index * 0.06, ghost_alpha)


def draw_burning_soul_cast(painter: QPainter, effect: EffectState, area: QRectF) -> None:
    """Draw the short cast pulse that summons the persistent soul sword."""
    if not 0.0 <= effect.age <= 0.46:
        return
    progress = clamp01(effect.age / 0.46)
    fade = 1.0 - progress
    radius = area.width() * (0.025 + progress * 0.045)
    painter.save()
    painter.setBrush(QColor(255, 142, 55, int(35 * fade)))
    painter.setPen(QPen(QColor(255, 205, 105, int(180 * fade)), max(1.5, area.width() * 0.004)))
    painter.drawEllipse(QRectF(effect.origin.x() - radius, effect.origin.y() - radius, radius * 2, radius * 2))
    painter.setPen(QPen(QColor(255, 105, 45, int(170 * fade)), max(1.5, area.width() * 0.004), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    for angle in (-90, -45, 0, 45, 90):
        direction = QPointF(math.cos(math.radians(angle)), math.sin(math.radians(angle)))
        painter.drawLine(
            effect.origin,
            QPointF(effect.origin.x() + direction.x() * radius * 1.7, effect.origin.y() + direction.y() * radius * 1.7),
        )
    painter.restore()


def draw_burning_soul_followup(painter: QPainter, effect: EffectState, area: QRectF) -> None:
    """Draw the short, independent soul-sword follow-up presentation."""
    delay = 0.10
    local_age = effect.age - delay
    flight_duration = 0.27
    if local_age < 0.0:
        return

    travel_x = effect.target.x() - effect.origin.x()
    travel_y = effect.target.y() - effect.origin.y()
    travel_length = max(1.0, math.hypot(travel_x, travel_y))
    direction = QPointF(travel_x / travel_length, travel_y / travel_length)

    painter.save()
    if 0.0 <= local_age <= flight_duration:
        progress = clamp01(local_age / flight_duration)
        eased = 1.0 - (1.0 - progress) ** 2
        position = lerp_point(effect.origin, effect.target, eased)
        fade = min(1.0, (1.0 - progress) * 1.25)
        trail_start = QPointF(
            position.x() - direction.x() * area.width() * 0.075,
            position.y() - direction.y() * area.width() * 0.075,
        )
        painter.setPen(
            QPen(
                QColor(255, 112, 47, int(135 * fade)),
                max(2.0, area.width() * 0.009),
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        painter.drawLine(trail_start, position)

        blade_length = area.width() * 0.038
        blade_width = area.width() * 0.010
        normal = QPointF(-direction.y(), direction.x())
        base = QPointF(
            position.x() - direction.x() * blade_length * 0.55,
            position.y() - direction.y() * blade_length * 0.55,
        )
        tip = QPointF(
            position.x() + direction.x() * blade_length * 0.70,
            position.y() + direction.y() * blade_length * 0.70,
        )
        blade = QPainterPath()
        blade.moveTo(QPointF(base.x() + normal.x() * blade_width, base.y() + normal.y() * blade_width))
        blade.lineTo(QPointF(base.x() - normal.x() * blade_width, base.y() - normal.y() * blade_width))
        blade.lineTo(tip)
        blade.closeSubpath()
        painter.setBrush(QColor(255, 159, 64, int(220 * fade)))
        painter.setPen(QPen(QColor(255, 237, 164, int(235 * fade)), 1.2))
        painter.drawPath(blade)

    impact_progress = (local_age - 0.23) / 0.16
    if 0.0 <= impact_progress <= 1.0:
        draw_impact(painter, effect.target, impact_progress, "small", (255, 145, 64))
    painter.restore()


def draw_burning_soul_sword(painter: QPainter, center: QPointF, area: QRectF, phase: float, remaining: float) -> None:
    """Draw the small non-blocking sword-soul visual while Burning Soul is active."""
    pulse = 0.72 + 0.28 * math.sin(phase * 2.2)
    sword_center = QPointF(center.x() + area.width() * 0.15, center.y() - area.height() * 0.018)
    blade_height = area.height() * 0.075
    blade_width = area.width() * 0.012
    top = sword_center.y() - blade_height * 0.5
    bottom = sword_center.y() + blade_height * 0.5
    painter.save()
    painter.setPen(QPen(QColor(255, 109, 53, int(85 * pulse)), max(6.0, area.width() * 0.018), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(QPointF(sword_center.x(), top), QPointF(sword_center.x(), bottom))
    blade = QPainterPath()
    blade.moveTo(QPointF(sword_center.x() - blade_width, top))
    blade.lineTo(QPointF(sword_center.x() + blade_width, top))
    blade.lineTo(QPointF(sword_center.x(), bottom + blade_width * 0.9))
    blade.closeSubpath()
    painter.setBrush(QColor(255, 188, 91, int(210 * pulse)))
    painter.setPen(QPen(QColor(255, 246, 186, int(235 * pulse)), 1.3))
    painter.drawPath(blade)
    painter.setPen(QPen(QColor(255, 105, 45, int(220 * pulse)), max(1.5, area.width() * 0.004), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(
        QPointF(sword_center.x() - blade_width * 2.1, sword_center.y()),
        QPointF(sword_center.x() + blade_width * 2.1, sword_center.y()),
    )
    painter.restore()


def draw_spatial_slash(painter: QPainter, effect: EffectState, area: QRectF) -> None:
    """Draw one evolving spatial rift whose scale follows the resolved variant."""
    progress = (effect.age - 0.025) / 0.32
    if not 0.0 <= progress <= 1.0:
        return
    settings = {
        "normal": (0.88, 1, 105, 1.0),
        "empowered": (1.08, 2, 145, 1.12),
        "maximum": (1.34, 2, 195, 1.28),
    }
    scale, layer_count, alpha, width_scale = settings.get(effect.variant, settings["normal"])
    fade = min(clamp01(progress / 0.12), clamp01((1.0 - progress) / 0.22))
    center = QPointF(effect.target.x(), effect.target.y() + area.height() * 0.012)
    painter.save()
    for layer in range(layer_count):
        offset = (layer - (layer_count - 1) / 2.0) * area.height() * 0.012
        radius_x = area.width() * 0.16 * scale
        radius_y = area.height() * 0.038 * scale
        path = QPainterPath(QPointF(center.x() - radius_x, center.y() + radius_y + offset))
        path.lineTo(QPointF(center.x() - radius_x * 0.36, center.y() - radius_y * 0.35 + offset))
        path.lineTo(QPointF(center.x() + radius_x * 0.10, center.y() + radius_y * 0.22 + offset))
        path.lineTo(QPointF(center.x() + radius_x, center.y() - radius_y - offset))
        painter.setPen(QPen(QColor(74, 178, 255, int(alpha * fade)), max(4.0, area.width() * 0.010 * width_scale), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawPath(path)
        painter.setPen(QPen(QColor(218, 249, 255, int(230 * fade)), max(1.5, area.width() * 0.0035), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawPath(path)
    painter.restore()


def draw_fighting_instinct_burst(painter: QPainter, effect: EffectState, area: QRectF) -> None:
    """Draw the one-shot burst when Fighting Instinct is activated."""
    if not 0.0 <= effect.age <= 0.42:
        return
    progress = clamp01(effect.age / 0.42)
    fade = 1.0 - progress
    radius = area.width() * (0.035 + progress * 0.12)
    painter.save()
    painter.setBrush(QColor(104, 221, 255, int(20 * fade)))
    painter.setPen(QPen(QColor(116, 228, 255, int(190 * fade)), max(2.0, area.width() * 0.005)))
    painter.drawEllipse(QRectF(effect.origin.x() - radius, effect.origin.y() - radius * 0.55, radius * 2, radius * 1.1))
    painter.setPen(QPen(QColor(204, 250, 255, int(190 * fade)), max(1.0, area.width() * 0.003), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    for angle in range(0, 360, 45):
        direction = QPointF(math.cos(math.radians(angle)), math.sin(math.radians(angle)))
        painter.drawLine(
            QPointF(effect.origin.x() + direction.x() * radius * 0.55, effect.origin.y() + direction.y() * radius * 0.55),
            QPointF(effect.origin.x() + direction.x() * radius * 1.05, effect.origin.y() + direction.y() * radius * 1.05),
        )
    painter.restore()


def draw_sword_descent(painter: QPainter, effect: EffectState, area: QRectF) -> None:
    """Draw the variant-scaled vertical sword descent at the boss."""
    progress = (effect.age - 0.015) / 0.38
    if not 0.0 <= progress <= 1.0:
        return
    settings = {
        "normal": (0.78, 125, "#bde8ff"),
        "max_rage": (1.05, 180, "#fff0a8"),
        "instinct": (1.30, 225, "#d6ffff"),
    }
    scale, alpha, blade_color = settings.get(effect.variant, settings["normal"])
    fade = min(clamp01(progress / 0.10), clamp01((1.0 - progress) / 0.20))
    tip_y = effect.target.y() - area.height() * 0.015 + progress * area.height() * 0.035
    blade_height = area.height() * 0.14 * scale
    blade_width = area.width() * 0.018 * scale
    top_y = tip_y - blade_height
    painter.save()
    painter.setPen(QPen(QColor(157, 225, 255, int(alpha * fade)), max(7.0, area.width() * 0.020 * scale), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(QPointF(effect.target.x(), top_y), QPointF(effect.target.x(), tip_y))
    blade = QPainterPath(QPointF(effect.target.x() - blade_width, top_y))
    blade.lineTo(QPointF(effect.target.x() + blade_width, top_y))
    blade.lineTo(QPointF(effect.target.x() + blade_width * 0.55, tip_y - blade_width * 0.8))
    blade.lineTo(QPointF(effect.target.x(), tip_y))
    blade.lineTo(QPointF(effect.target.x() - blade_width * 0.55, tip_y - blade_width * 0.8))
    blade.closeSubpath()
    painter.setBrush(QColor(blade_color))
    painter.setPen(QPen(QColor(255, 255, 225, int(235 * fade)), 1.5))
    painter.drawPath(blade)
    guard_y = top_y + blade_height * 0.18
    painter.setPen(QPen(QColor(255, 210, 115, int(220 * fade)), max(2.0, area.width() * 0.005), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(QPointF(effect.target.x() - blade_width * 2.0, guard_y), QPointF(effect.target.x() + blade_width * 2.0, guard_y))
    painter.restore()


def draw_rage_aura(painter: QPainter, center: QPointF, area: QRectF, phase: float, remaining: float) -> None:
    """Draw a restrained aura while Fighting Instinct remains active."""
    pulse = 0.70 + 0.30 * math.sin(phase * 2.0)
    radius_x = area.width() * (0.12 + 0.012 * pulse)
    radius_y = area.height() * (0.070 + 0.008 * pulse)
    painter.save()
    painter.setBrush(QColor(81, 204, 255, int(16 * pulse)))
    painter.setPen(QPen(QColor(126, 235, 255, int(92 * pulse)), max(1.5, area.width() * 0.004), Qt.PenStyle.DashLine))
    painter.drawEllipse(QRectF(center.x() - radius_x, center.y() - radius_y, radius_x * 2, radius_y * 2))
    painter.setPen(QPen(QColor(207, 252, 255, int(95 * pulse)), max(1.0, area.width() * 0.0025), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    for angle in (-35, 35, 145, 215):
        direction = QPointF(math.cos(math.radians(angle)), math.sin(math.radians(angle)))
        painter.drawLine(
            QPointF(center.x() + direction.x() * radius_x * 0.65, center.y() + direction.y() * radius_y * 0.65),
            QPointF(center.x() + direction.x() * radius_x * 0.92, center.y() + direction.y() * radius_y * 0.92),
        )
    painter.restore()


def draw_flying_shuriken(painter: QPainter, center: QPointF, radius: float, rotation: float, direction: QPointF, fade: float) -> None:
    trail_start = QPointF(center.x() - direction.x() * radius * 2.8, center.y() - direction.y() * radius * 2.8)
    painter.setPen(QPen(QColor(177, 145, 255, int(130 * fade)), max(1.0, radius * 0.20), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(trail_start, center)
    points = []
    for index in range(8):
        angle = math.radians(-90 + rotation + index * 45)
        distance = radius if index % 2 == 0 else radius * 0.27
        points.append(QPointF(center.x() + math.cos(angle) * distance, center.y() + math.sin(angle) * distance))
    painter.setBrush(QColor(129, 110, 230, int(245 * fade)))
    painter.setPen(QPen(QColor(224, 215, 255, int(245 * fade)), 1.3))
    painter.drawPath(_path_from_points(tuple(points)))
    painter.setBrush(QColor(35, 29, 76, int(230 * fade)))
    painter.drawEllipse(QRectF(center.x() - radius * 0.17, center.y() - radius * 0.17, radius * 0.34, radius * 0.34))


def draw_cannon_muzzle_flash(painter: QPainter, origin: QPointF, area: QRectF, age: float) -> None:
    if not 0.0 <= age <= 0.14:
        return
    fade = 1.0 - age / 0.14
    painter.save()
    painter.setPen(QPen(QColor(255, 174, 76, int(170 * fade)), max(2.0, area.width() * 0.006), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    for angle in (-36, -18, 0, 18, 36):
        direction = QPointF(math.cos(math.radians(angle)), math.sin(math.radians(angle)))
        painter.drawLine(origin, QPointF(origin.x() + direction.x() * area.width() * 0.085 * fade, origin.y() + direction.y() * area.width() * 0.085 * fade))
    painter.setBrush(QColor(255, 217, 125, int(225 * fade)))
    painter.setPen(QPen(QColor(255, 244, 193, int(245 * fade)), 2))
    painter.drawEllipse(QRectF(origin.x() - area.width() * 0.025 * fade, origin.y() - area.width() * 0.025 * fade, area.width() * 0.05 * fade, area.width() * 0.05 * fade))
    painter.restore()


def draw_cannonball(painter: QPainter, origin: QPointF, target: QPointF, area: QRectF, progress: float) -> None:
    eased = 1.0 - (1.0 - progress) ** 2
    position = lerp_point(origin, target, eased)
    direction_x = target.x() - origin.x()
    direction_y = target.y() - origin.y()
    length = max(1.0, math.hypot(direction_x, direction_y))
    direction = QPointF(direction_x / length, direction_y / length)
    trail_start = QPointF(position.x() - direction.x() * area.width() * 0.07, position.y() - direction.y() * area.width() * 0.07)
    painter.setPen(QPen(QColor(187, 115, 55, 125), max(2.0, area.width() * 0.012), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(trail_start, position)
    ball_radius = area.width() * 0.035
    painter.setBrush(QColor("#c46c35"))
    painter.setPen(QPen(QColor("#ffd28a"), 2))
    painter.drawEllipse(QRectF(position.x() - ball_radius, position.y() - ball_radius, ball_radius * 2, ball_radius * 2))
    painter.setBrush(QColor(255, 214, 135, 210))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(QRectF(position.x() - ball_radius * 0.34, position.y() - ball_radius * 0.45, ball_radius * 0.42, ball_radius * 0.42))


def draw_holy_cast_pulse(painter: QPainter, origin: QPointF, target: QPointF, area: QRectF, age: float) -> None:
    if not 0.0 <= age <= 0.28:
        return
    pulse = 1.0 - age / 0.28
    painter.save()
    painter.setPen(QPen(QColor(205, 249, 255, int(95 * pulse)), max(2.0, area.width() * 0.007), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawEllipse(QRectF(origin.x() - area.width() * 0.045 * pulse, origin.y() - area.width() * 0.045 * pulse, area.width() * 0.09 * pulse, area.width() * 0.09 * pulse))
    painter.setPen(QPen(QColor(255, 245, 183, int(42 * pulse)), max(1.0, area.width() * 0.004), Qt.PenStyle.DashLine))
    painter.drawLine(origin, QPointF(target.x(), target.y() + area.height() * 0.04))
    painter.restore()


def draw_holy_area_base(painter: QPainter, ground: QPointF, area: QRectF, fade: float) -> None:
    if fade <= 0.0:
        return
    area_width = area.width() * 0.14
    area_height = area.height() * 0.038
    painter.save()
    painter.setBrush(QColor(255, 241, 166, int(25 * fade)))
    painter.setPen(QPen(QColor(255, 247, 198, int(130 * fade)), 2))
    painter.drawEllipse(QRectF(ground.x() - area_width, ground.y() - area_height, area_width * 2, area_height * 2))
    painter.restore()


def draw_holy_burst(painter: QPainter, center: QPointF, progress: float, area: QRectF) -> None:
    fade = 1.0 - progress
    radius_x = area.width() * (0.055 + progress * 0.065)
    radius_y = area.height() * (0.020 + progress * 0.016)
    painter.save()
    painter.setBrush(QColor(255, 248, 191, int(32 * fade)))
    painter.setPen(QPen(QColor(255, 247, 189, int(190 * fade)), max(1.0, area.width() * 0.004)))
    painter.drawEllipse(QRectF(center.x() - radius_x, center.y() - radius_y, radius_x * 2, radius_y * 2))
    painter.setPen(QPen(QColor(215, 255, 255, int(150 * fade)), max(1.0, area.width() * 0.003), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    for angle in range(0, 360, 60):
        direction = QPointF(math.cos(math.radians(angle)), math.sin(math.radians(angle)))
        start = QPointF(center.x() + direction.x() * radius_x * 0.65, center.y() + direction.y() * radius_y * 0.65)
        end = QPointF(center.x() + direction.x() * radius_x * 0.95, center.y() + direction.y() * radius_y * 0.95)
        painter.drawLine(start, end)
    painter.restore()


def draw_impact(painter: QPainter, center: QPointF, progress: float, level: str, color: tuple[int, int, int]) -> None:
    settings = {"small": (8.0, 25.0, 5), "medium": (14.0, 42.0, 7), "large": (22.0, 68.0, 10)}
    start_radius, end_radius, ray_count = settings[level]
    radius = start_radius + (end_radius - start_radius) * progress
    fade = 1.0 - progress
    painter.save()
    painter.setPen(QPen(QColor(*color, int(190 * fade)), max(1.5, end_radius * 0.08)))
    painter.setBrush(QColor(color[0], color[1], color[2], int(45 * fade)))
    painter.drawEllipse(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2))
    for index in range(ray_count):
        angle = math.radians(index * 360.0 / ray_count + 8.0)
        direction = QPointF(math.cos(angle), math.sin(angle))
        ray_start = QPointF(center.x() + direction.x() * radius * 0.55, center.y() + direction.y() * radius * 0.55)
        ray_end = QPointF(center.x() + direction.x() * radius * 1.18, center.y() + direction.y() * radius * 1.18)
        painter.drawLine(ray_start, ray_end)
    if level != "small":
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 248, 218, int((150 if level == "medium" else 205) * fade)))
        inner = radius * (0.28 if level == "medium" else 0.38)
        painter.drawEllipse(QRectF(center.x() - inner, center.y() - inner, inner * 2, inner * 2))
    painter.restore()


def cannon_recoil(effects: list[EffectState], area: QRectF) -> float:
    recoil = 0.0
    for effect in effects:
        if effect.effect_id == "cannon_shot" and 0.0 <= effect.age <= 0.16:
            recoil = max(recoil, area.width() * 0.018 * math.sin(math.pi * effect.age / 0.16))
    return recoil


def _path_from_points(points: tuple[QPointF, ...]) -> QPainterPath:
    path = QPainterPath()
    path.moveTo(points[0])
    for point in points[1:]:
        path.lineTo(point)
    path.closeSubpath()
    return path
