"""
《新楓之谷：放置遠征隊》純程式碼向量幾何視覺特效渲染引擎 (vfx_renderer.py)
模組化統一調度入口：調度冒險家、皇家騎士團、反抗軍三大陣營共 192 招專屬幾何特效！
"""

import math
from PySide6.QtCore import Qt, QPointF, QRect, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QRadialGradient,
    QPainterPath, QPolygonF
)

from vfx_core import (
    render_aura_halo,
    _draw_starburst,
    _draw_combo_orb,
    _draw_shuriken,
    _draw_magic_circle
)
from vfx.vfx_explorers import render_explorer_vfx
from vfx.vfx_cygnus import render_cygnus_vfx
from vfx.vfx_resistance import render_resistance_vfx


def render_maple_vfx(painter, eff_name, p, color, cx, cy, tx, ty,
                     rot_angle=0.0, seed=0.0, fracture_lines=None, **kwargs):
    """
    通用新楓之谷特效繪製入口函數 (全 24 職業 192 招技能完全專屬客製調度)
    """
    alpha = int(255 * (1.0 - p))
    if alpha <= 0:
        return

    r, g, b = color[:3]
    painter.save()
    try:
        handled = (
            render_explorer_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty, rot_angle, seed, fracture_lines, **kwargs) or
            render_cygnus_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty, rot_angle, seed, fracture_lines, **kwargs) or
            render_resistance_vfx(painter, eff_name, p, r, g, b, alpha, cx, cy, tx, ty, rot_angle, seed, fracture_lines, **kwargs)
        )

        if not handled:
            # 通用後備特效 (Fallback)
            rad = int(35 + 65 * p)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(r, g, b, alpha), 4))
            painter.drawArc(QRect(int(tx - rad), int(ty - rad), rad * 2, rad * 2), int((-35 + p * 20) * 16), int(140 * 16))
    finally:
        painter.restore()
