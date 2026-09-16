"""Combat avatar presentation and anchor generation for the visual sandbox."""

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen


AVATAR_NAMES = ("Hero", "Night Lord", "Cannon", "Bishop")


class AvatarRenderer:
    """Draw the four sandbox avatars without depending on the QWidget."""

    def __init__(self, idle_phase: float, cannon_recoil: float = 0.0) -> None:
        self.idle_phase = idle_phase
        self.cannon_recoil = cannon_recoil

    def draw(self, painter: QPainter, avatar_index: int, center: QPointF, area: QRectF) -> dict[str, QPointF]:
        if avatar_index == 0:
            return self._draw_hero(painter, center, area)
        if avatar_index == 1:
            return self._draw_night_lord(painter, center, area)
        if avatar_index == 2:
            return self._draw_cannon(painter, center, area)
        return self._draw_bishop(painter, center, area)

    @staticmethod
    def _path_from_points(points: tuple[QPointF, ...]) -> QPainterPath:
        path = QPainterPath()
        path.moveTo(points[0])
        for point in points[1:]:
            path.lineTo(point)
        path.closeSubpath()
        return path

    def _draw_hero(self, painter: QPainter, center: QPointF, area: QRectF) -> dict[str, QPointF]:
        size = area.width() * 0.135
        # Rotate the two endpoints together so every sword component remains rigid.
        raw_grip = QPointF(center.x() - size * 0.20, center.y() + size * 0.43)
        raw_tip = QPointF(center.x() + size * 0.66, center.y() - size * 0.70)
        idle_rotation = math.sin(self.idle_phase) * math.radians(1.5)
        cos_angle = math.cos(idle_rotation)
        sin_angle = math.sin(idle_rotation)

        def rotate_around_pivot(point: QPointF) -> QPointF:
            dx = point.x() - center.x()
            dy = point.y() - center.y()
            return QPointF(center.x() + dx * cos_angle - dy * sin_angle, center.y() + dx * sin_angle + dy * cos_angle)

        grip = rotate_around_pivot(raw_grip)
        tip = rotate_around_pivot(raw_tip)
        delta_x = tip.x() - grip.x()
        delta_y = tip.y() - grip.y()
        axis_length = math.hypot(delta_x, delta_y)
        sword_axis = QPointF(delta_x / axis_length, delta_y / axis_length)
        normal = QPointF(-sword_axis.y(), sword_axis.x())

        def along(point: QPointF, distance: float) -> QPointF:
            return QPointF(point.x() + sword_axis.x() * distance, point.y() + sword_axis.y() * distance)

        def across(point: QPointF, distance: float) -> QPointF:
            return QPointF(point.x() + normal.x() * distance, point.y() + normal.y() * distance)

        blade_base = along(grip, size * 0.045)
        blade_shoulder = along(grip, size * 0.14)
        blade_tip = along(tip, -size * 0.035)
        blade = self._path_from_points(
            (
                across(blade_base, -size * 0.085),
                across(blade_shoulder, -size * 0.13),
                across(blade_tip, -size * 0.026),
                tip,
                across(blade_tip, size * 0.026),
                across(blade_shoulder, size * 0.13),
                across(blade_base, size * 0.085),
            )
        )
        painter.setBrush(QColor("#e9f5ff"))
        painter.setPen(QPen(QColor("#87b8e7"), 2))
        painter.drawPath(blade)

        guard_left = across(grip, -size * 0.32)
        guard_right = across(grip, size * 0.32)
        painter.setPen(QPen(QColor("#f5cf6d"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(guard_left, guard_right)

        handle_end = along(grip, -size * 0.38)
        painter.setPen(QPen(QColor("#dbeaff"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(grip, handle_end)
        pommel_center = along(handle_end, -size * 0.055)
        painter.setBrush(QColor("#5b87bc"))
        painter.setPen(QPen(QColor("#d3e9ff"), 2))
        painter.drawEllipse(QRectF(pommel_center.x() - size * 0.09, pommel_center.y() - size * 0.09, size * 0.18, size * 0.18))
        # A small floating medallion is the Hero's secondary emblem, not a shield.
        medallion = across(grip, -size * 0.60)
        painter.setBrush(QColor("#315e91"))
        painter.setPen(QPen(QColor("#f2d47b"), 2))
        painter.drawEllipse(QRectF(medallion.x() - size * 0.13, medallion.y() - size * 0.13, size * 0.26, size * 0.26))
        painter.setBrush(QColor("#f2d47b"))
        painter.setPen(Qt.PenStyle.NoPen)
        badge = self._path_from_points(
            (
                QPointF(medallion.x(), medallion.y() - size * 0.08),
                QPointF(medallion.x() + size * 0.08, medallion.y()),
                QPointF(medallion.x(), medallion.y() + size * 0.08),
                QPointF(medallion.x() - size * 0.08, medallion.y()),
            )
        )
        painter.drawPath(badge)
        return {"center": center, "attack_origin": grip, "tip": tip, "ground": QPointF(center.x(), center.y() + size * 0.76)}

    def _draw_shuriken(self, painter: QPainter, center: QPointF, radius: float, rotation: float) -> QPointF:
        points = []
        for index in range(8):
            angle = math.radians(-90 + rotation + index * 45)
            distance = radius if index % 2 == 0 else radius * 0.27
            points.append(QPointF(center.x() + math.cos(angle) * distance, center.y() + math.sin(angle) * distance))
        painter.setBrush(QColor("#816ee6"))
        painter.setPen(QPen(QColor("#d2c8ff"), 1.5))
        painter.drawPath(self._path_from_points(tuple(points)))
        painter.setBrush(QColor("#25214b"))
        painter.drawEllipse(QRectF(center.x() - radius * 0.18, center.y() - radius * 0.18, radius * 0.36, radius * 0.36))
        return points[0]

    def _draw_night_lord(self, painter: QPainter, center: QPointF, area: QRectF) -> dict[str, QPointF]:
        size = area.width() * 0.12
        # The main silhouette is a compact hand-back gauntlet, not a claw blade.
        gauntlet = self._path_from_points(
            (
                QPointF(center.x() - size * 0.28, center.y() + size * 0.10),
                QPointF(center.x() - size * 0.18, center.y() - size * 0.18),
                QPointF(center.x() + size * 0.08, center.y() - size * 0.25),
                QPointF(center.x() + size * 0.25, center.y() - size * 0.08),
                QPointF(center.x() + size * 0.21, center.y() + size * 0.17),
                QPointF(center.x() - size * 0.07, center.y() + size * 0.24),
            )
        )
        painter.setBrush(QColor("#30265f"))
        painter.setPen(QPen(QColor("#a996ff"), 2))
        painter.drawPath(gauntlet)

        # Wrist strap and three small knuckle plates sell the hand-worn shape.
        strap = self._path_from_points(
            (
                QPointF(center.x() - size * 0.31, center.y() + size * 0.02),
                QPointF(center.x() - size * 0.21, center.y() + size * 0.20),
                QPointF(center.x() - size * 0.10, center.y() + size * 0.18),
                QPointF(center.x() - size * 0.19, center.y() - size * 0.01),
            )
        )
        painter.setBrush(QColor("#25214b"))
        painter.setPen(QPen(QColor("#8b70e5"), 2))
        painter.drawPath(strap)
        painter.setBrush(QColor("#bdaeff"))
        painter.setPen(QPen(QColor("#554493"), 1))
        for index in range(3):
            plate = QRectF(center.x() + size * (0.01 + index * 0.065), center.y() - size * (0.16 - index * 0.025), size * 0.055, size * 0.10)
            painter.drawRoundedRect(plate, size * 0.02, size * 0.02)
        # Only two short forward fins remain, suggesting a throwing gauntlet
        # without turning the main silhouette into a beast claw.
        attack_origin = QPointF(center.x() + size * 0.21, center.y() - size * 0.04)
        upper_fin = self._path_from_points(
            (
                QPointF(center.x() + size * 0.14, center.y() - size * 0.15),
                QPointF(center.x() + size * 0.35, center.y() - size * 0.18),
                QPointF(center.x() + size * 0.20, center.y() - size * 0.01),
            )
        )
        lower_fin = self._path_from_points(
            (
                QPointF(center.x() + size * 0.17, center.y() + size * 0.06),
                QPointF(center.x() + size * 0.37, center.y() + size * 0.10),
                QPointF(center.x() + size * 0.21, center.y() + size * 0.18),
            )
        )
        painter.setBrush(QColor("#816ee6"))
        painter.setPen(QPen(QColor("#d2c8ff"), 1.5))
        painter.drawPath(upper_fin)
        painter.drawPath(lower_fin)
        painter.setBrush(QColor("#4b3c91"))
        painter.setPen(QPen(QColor("#cfc5ff"), 1.5))
        painter.drawEllipse(QRectF(center.x() - size * 0.06, center.y() - size * 0.04, size * 0.12, size * 0.12))

        # Presentation tip remains the leading point of one orbiting shuriken.
        tip = attack_origin
        orbit_radius = size * 0.72
        for index, offset in enumerate((0.0, 120.0, 240.0)):
            angle = self.idle_phase * 16.0 + offset
            shard_center = QPointF(center.x() + math.cos(math.radians(angle)) * orbit_radius, center.y() + math.sin(math.radians(angle)) * orbit_radius)
            shard_tip = self._draw_shuriken(painter, shard_center, size * 0.20, -angle)
            if index == 0:
                tip = shard_tip
        # A small hanging charm is the canonical secondary item for the Claw.
        charm_top = QPointF(center.x() - size * 0.37, center.y() + size * 0.31)
        charm = QPointF(charm_top.x(), charm_top.y() + size * 0.19)
        painter.setPen(QPen(QColor("#8e76db"), 1.5))
        painter.drawLine(charm_top, charm)
        painter.setBrush(QColor("#d6a956"))
        painter.setPen(QPen(QColor("#ffe9a6"), 1.5))
        painter.drawPath(self._path_from_points((QPointF(charm.x(), charm.y() - size * 0.10), QPointF(charm.x() + size * 0.09, charm.y()), QPointF(charm.x(), charm.y() + size * 0.10), QPointF(charm.x() - size * 0.09, charm.y()))))
        return {"center": center, "attack_origin": attack_origin, "tip": tip, "ground": QPointF(center.x(), center.y() + size * 0.78)}

    def _draw_cannon(self, painter: QPainter, center: QPointF, area: QRectF) -> dict[str, QPointF]:
        size = area.width() * 0.17
        breath = math.sin(self.idle_phase * 0.7) * size * 0.012
        body_center = QPointF(center.x() - self.cannon_recoil, center.y() + breath)
        barrel_left = body_center.x() - size * 0.52
        muzzle = QPointF(body_center.x() + size * 0.72, body_center.y() - size * 0.06)
        # Rear stock sits behind the barrel so this reads as a carried hand cannon.
        stock = self._path_from_points(
            (
                QPointF(body_center.x() - size * 0.78, body_center.y() - size * 0.19),
                QPointF(body_center.x() - size * 0.48, body_center.y() - size * 0.19),
                QPointF(body_center.x() - size * 0.43, body_center.y() + size * 0.17),
                QPointF(body_center.x() - size * 0.72, body_center.y() + size * 0.27),
                QPointF(body_center.x() - size * 0.86, body_center.y() + size * 0.12),
            )
        )
        painter.setBrush(QColor("#3b414e"))
        painter.setPen(QPen(QColor("#b8733d"), 3))
        painter.drawPath(stock)
        painter.drawRoundedRect(QRectF(barrel_left, body_center.y() - size * 0.17, size * 1.20, size * 0.33), size * 0.11, size * 0.11)
        painter.setBrush(QColor("#d18445"))
        painter.drawEllipse(QRectF(muzzle.x() - size * 0.14, muzzle.y() - size * 0.20, size * 0.28, size * 0.40))
        painter.setBrush(QColor("#596171"))
        painter.setPen(QPen(QColor("#d89655"), 2))
        painter.drawRoundedRect(QRectF(body_center.x() - size * 0.24, body_center.y() + size * 0.13, size * 0.50, size * 0.33), size * 0.06, size * 0.06)
        # A pronounced grip and brace imply hands/shoulder support without a sprite.
        grip = self._path_from_points(
            (
                QPointF(body_center.x() - size * 0.04, body_center.y() + size * 0.18),
                QPointF(body_center.x() + size * 0.19, body_center.y() + size * 0.16),
                QPointF(body_center.x() + size * 0.25, body_center.y() + size * 0.56),
                QPointF(body_center.x() - size * 0.01, body_center.y() + size * 0.56),
            )
        )
        painter.setBrush(QColor("#252b36"))
        painter.setPen(QPen(QColor("#d89655"), 2))
        painter.drawPath(grip)
        painter.setPen(QPen(QColor("#9ea8b8"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(body_center.x() - size * 0.43, body_center.y() + size * 0.20), QPointF(body_center.x() - size * 0.01, body_center.y() + size * 0.49))
        # Powder keg hangs as a small, static side accessory.
        keg = QRectF(body_center.x() - size * 0.84, body_center.y() - size * 0.57, size * 0.40, size * 0.25)
        painter.setBrush(QColor("#70462e"))
        painter.setPen(QPen(QColor("#e1a05c"), 2))
        painter.drawRoundedRect(keg, size * 0.08, size * 0.08)
        painter.setPen(QPen(QColor("#d98b3c"), 2))
        painter.drawLine(QPointF(keg.left() + size * 0.12, keg.top()), QPointF(keg.left() + size * 0.12, keg.bottom()))
        painter.drawLine(QPointF(keg.right() - size * 0.12, keg.top()), QPointF(keg.right() - size * 0.12, keg.bottom()))
        painter.setBrush(QColor("#efc06b"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(keg.right() - size * 0.03, keg.top() - size * 0.08, size * 0.07, size * 0.07))
        return {"center": center, "attack_origin": body_center, "tip": muzzle, "ground": QPointF(center.x(), center.y() + size * 0.70), "muzzle": muzzle}

    def _draw_bishop(self, painter: QPainter, center: QPointF, area: QRectF) -> dict[str, QPointF]:
        size = area.width() * 0.12
        grip = QPointF(center.x() - size * 0.25, center.y() + size * 0.48)
        tip = QPointF(center.x() + size * 0.30, center.y() - size * 0.60)
        book_float = math.sin(self.idle_phase * 0.7) * size * 0.018
        book_center = QPointF(center.x() - size * 0.64, center.y() + size * 0.02 + book_float)
        # A simple open-book silhouette supplies Bishop's canonical secondary item.
        cover = self._path_from_points(
            (
                QPointF(book_center.x() - size * 0.37, book_center.y() - size * 0.20),
                QPointF(book_center.x() - size * 0.03, book_center.y() - size * 0.10),
                QPointF(book_center.x() + size * 0.32, book_center.y() - size * 0.20),
                QPointF(book_center.x() + size * 0.25, book_center.y() + size * 0.27),
                QPointF(book_center.x() - size * 0.03, book_center.y() + size * 0.18),
                QPointF(book_center.x() - size * 0.29, book_center.y() + size * 0.27),
            )
        )
        painter.setBrush(QColor("#3c638f"))
        painter.setPen(QPen(QColor("#e0c878"), 2))
        painter.drawPath(cover)
        left_page = self._path_from_points(
            (
                book_center,
                QPointF(book_center.x() - size * 0.34, book_center.y() - size * 0.17),
                QPointF(book_center.x() - size * 0.07, book_center.y() - size * 0.08),
                QPointF(book_center.x() - size * 0.02, book_center.y() + size * 0.20),
            )
        )
        right_page = self._path_from_points(
            (
                book_center,
                QPointF(book_center.x() + size * 0.29, book_center.y() - size * 0.16),
                QPointF(book_center.x() + size * 0.09, book_center.y() - size * 0.06),
                QPointF(book_center.x() - size * 0.02, book_center.y() + size * 0.20),
            )
        )
        painter.setBrush(QColor("#f6f0d2"))
        painter.setPen(QPen(QColor("#d0b96c"), 1.5))
        painter.drawPath(left_page)
        painter.drawPath(right_page)
        painter.setPen(QPen(QColor("#a79563"), 1))
        painter.drawLine(QPointF(book_center.x() - size * 0.19, book_center.y() - size * 0.07), QPointF(book_center.x() - size * 0.05, book_center.y() - size * 0.02))
        painter.drawLine(QPointF(book_center.x() + size * 0.04, book_center.y() - size * 0.03), QPointF(book_center.x() + size * 0.18, book_center.y() - size * 0.07))
        painter.setPen(QPen(QColor("#f5e5a4"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(grip, tip)
        painter.setPen(QPen(QColor("#c5fbff"), 2))
        painter.drawEllipse(QRectF(tip.x() - size * 0.32, tip.y() - size * 0.32, size * 0.64, size * 0.64))
        glow_alpha = 145 + int((math.sin(self.idle_phase * 1.4) + 1) * 40)
        painter.setBrush(QColor(196, 250, 255, glow_alpha))
        painter.setPen(QPen(QColor("#fff4bc"), 2))
        painter.drawEllipse(QRectF(tip.x() - size * 0.14, tip.y() - size * 0.14, size * 0.28, size * 0.28))
        painter.setBrush(QColor("#f6db79"))
        painter.setPen(QPen(QColor("#fff6d0"), 2))
        painter.drawEllipse(QRectF(grip.x() - size * 0.10, grip.y() - size * 0.04, size * 0.20, size * 0.20))
        return {"center": center, "attack_origin": grip, "tip": tip, "ground": QPointF(center.x(), center.y() + size * 0.70)}


def draw_debug_anchors(painter: QPainter, anchors: dict[str, QPointF]) -> None:
    colors = {"center": "#ffffff", "attack_origin": "#ffdc70", "tip": "#ff8c8c", "ground": "#77efb1", "muzzle": "#ffad63"}
    painter.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
    for name, point in anchors.items():
        painter.setPen(QPen(QColor(colors.get(name, "#ffffff")), 1.5))
        painter.setBrush(QColor(colors.get(name, "#ffffff")))
        painter.drawEllipse(point, 4, 4)
        painter.drawText(point + QPointF(7, -6), name)
