"""
新楓之谷純程式碼向量幾何視覺特效 - 核心繪圖與光環模組 (vfx_core.py)
包含幾何星芒、手裏劍、魔法陣與持續脈動光環渲染器
"""

import math
import random
from collections import OrderedDict
from PySide6.QtCore import Qt, QPointF, QRect, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QRadialGradient,
    QPainterPath, QPolygonF
)

# =========================================================================
# 0. 輕量有界 LRU 幾何快取層 (Bounded Geometric Cache) - 防記憶體洩漏
# =========================================================================
class BoundedCache(OrderedDict):
    """有界 LRU 快取字典，達到 maxsize 時自動淘汰最久未存取的元素"""
    def __init__(self, maxsize=512):
        super().__init__()
        self.maxsize = maxsize

    def get_or_set(self, key, factory_fn):
        if key in self:
            self.move_to_end(key)
            return self[key]
        val = factory_fn()
        if len(self) >= self.maxsize:
            self.popitem(last=False)
        self[key] = val
        return val


_vfx_geom_cache = BoundedCache(maxsize=512)


def clear_vfx_cache():
    """手動清理快取（例如重置場景時）"""
    _vfx_geom_cache.clear()


# =========================================================================
# 0.5 現代遊戲動力學 Easing 曲線庫 (Common Motion Easing)
# =========================================================================
def ease_in_out(p: float) -> float:
    """S 型平滑加減速 (0.0 -> 1.0)"""
    p = max(0.0, min(1.0, float(p)))
    return 0.5 - 0.5 * math.cos(p * math.pi)


def ease_out_quad(p: float) -> float:
    """二次方平滑減速 (最常用於衝擊波與斬擊)"""
    p = max(0.0, min(1.0, float(p)))
    return 1.0 - (1.0 - p) * (1.0 - p)


def ease_in_quad(p: float) -> float:
    """二次方平滑加速 (突進與能量匯聚)"""
    p = max(0.0, min(1.0, float(p)))
    return p * p


def ease_out_cubic(p: float) -> float:
    """三次方極速爆發後緩慢衰減"""
    p = max(0.0, min(1.0, float(p)))
    inv = 1.0 - p
    return 1.0 - inv * inv * inv


def ease_out_sine(p: float) -> float:
    """正弦溫和減速"""
    p = max(0.0, min(1.0, float(p)))
    return math.sin(p * (math.pi * 0.5))


def _draw_starburst(painter, x, y, size, core_color, glow_color):
    painter.save()
    painter.translate(x, y)
    painter.setPen(QPen(glow_color, 2.5))
    painter.drawLine(QPointF(-size, 0), QPointF(size, 0))
    painter.drawLine(QPointF(0, -size), QPointF(0, size))
    s_mid = size * 0.6
    painter.drawLine(QPointF(-s_mid, -s_mid), QPointF(s_mid, s_mid))
    painter.drawLine(QPointF(-s_mid, s_mid), QPointF(s_mid, -s_mid))
    painter.setBrush(QBrush(core_color))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(QPointF(0, 0), max(2.0, size * 0.35), max(2.0, size * 0.35))
    painter.restore()


def _draw_combo_orb(painter, ox, oy, scale=1.0, alpha=255):
    rad = int(10 * scale)
    rg = QRadialGradient(ox, oy, rad)
    rg.setColorAt(0.0, QColor(255, 255, 255, alpha))
    rg.setColorAt(0.5, QColor(100, 200, 255, int(alpha * 0.9)))
    rg.setColorAt(0.85, QColor(30, 80, 220, int(alpha * 0.6)))
    rg.setColorAt(1.0, QColor(0, 0, 0, 0))
    painter.setBrush(QBrush(rg))
    painter.setPen(QPen(QColor(200, 240, 255, alpha), 1))
    painter.drawEllipse(QPointF(ox, oy), rad, rad)


def _build_shuriken_path(s: float) -> QPainterPath:
    path = QPainterPath()
    path.moveTo(0, -s)
    path.lineTo(s * 0.25, -s * 0.25)
    path.lineTo(s, 0)
    path.lineTo(s * 0.25, s * 0.25)
    path.lineTo(0, s)
    path.lineTo(-s * 0.25, s * 0.25)
    path.lineTo(-s, 0)
    path.lineTo(-s * 0.25, -s * 0.25)
    path.closeSubpath()
    return path


def _draw_shuriken(painter, x, y, angle_deg, size, color, core_white=False):
    painter.save()
    painter.translate(x, y)
    painter.rotate(angle_deg)
    s = float(size)
    key = ("shuriken", round(s, 1))
    path = _vfx_geom_cache.get_or_set(key, lambda: _build_shuriken_path(s))

    painter.setBrush(QBrush(color))
    painter.setPen(QPen(QColor(255, 255, 255, color.alpha()), 1.2))
    painter.drawPath(path)
    if core_white:
        painter.setBrush(QBrush(QColor(255, 255, 255, color.alpha())))
        painter.drawEllipse(QPointF(0, 0), s * 0.25, s * 0.25)
    painter.restore()


def _build_magic_circle_polys(radius: float, rot_rad: float):
    polys = []
    for tri_idx in [0, 1]:
        poly = QPolygonF()
        base_ang = rot_rad + tri_idx * math.pi
        for pt_i in range(3):
            ang = base_ang + pt_i * (2 * math.pi / 3)
            px = math.cos(ang) * radius * 0.75
            py = math.sin(ang) * radius * 0.75 * 0.35
            poly.append(QPointF(px, py))
        polys.append(poly)
    return polys


def _draw_magic_circle(painter, x, y, radius, rot_rad, color):
    painter.save()
    painter.translate(x, y)
    painter.setPen(QPen(color, 1.8))
    painter.setBrush(Qt.NoBrush)
    r = float(radius)
    painter.drawEllipse(QPointF(0, 0), r, r * 0.35)
    painter.drawEllipse(QPointF(0, 0), r * 0.8, r * 0.28)

    key = ("magic_circle", round(r, 1), round(rot_rad % (math.pi * 2), 2))
    polys = _vfx_geom_cache.get_or_set(key, lambda: _build_magic_circle_polys(r, rot_rad))
    for poly in polys:
        painter.drawPolygon(poly)
    painter.restore()



def render_aura_halo(painter, cx, cy, buff_type, buff_timer, max_timer=8.0, rot_angle=0.0, game_time=None):
    """
    在隊員腳下與周身渲染持續脈動的增益光環 (Persistent Aura Effect)
    支援 attack(紅橙), speed(翠綠), def(湛藍), crit(金黃), lifesteal(紫紅) 等多彩光芒
    支援透過 game_time 吃遊戲內部流逝時間，避免與主迴圈脫鉤
    """
    import time
    t = game_time if game_time is not None else time.time()
    pulse = 0.5 + 0.5 * math.sin(t * 4.0)
    ratio = max(0.1, min(1.0, buff_timer / max(1.0, max_timer)))
    
    # 根據增益類型配置配色
    color_map = {
        "attack": ((255, 100, 40), (255, 200, 60)),
        "attack_mult": ((255, 100, 40), (255, 200, 60)),
        "atk": ((255, 100, 40), (255, 200, 60)),
        "speed": ((40, 230, 140), (160, 255, 200)),
        "speed_bonus": ((40, 230, 140), (160, 255, 200)),
        "def": ((60, 150, 255), (180, 220, 255)),
        "defense": ((60, 150, 255), (180, 220, 255)),
        "crit": ((255, 215, 0), (255, 250, 180)),
        "lifesteal": ((210, 80, 240), (255, 160, 255)),
        "union": ((180, 50, 240), (255, 220, 90)),
        "union_aura": ((180, 50, 240), (255, 220, 90)),
    }
    main_c, high_c = color_map.get(buff_type, ((255, 215, 60), (255, 255, 200)))
    alpha = int(140 * ratio + 60 * pulse * ratio)
    is_union = buff_type in ["union", "union_aura"]
    
    painter.save()
    painter.translate(cx, cy)
    if is_union:
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
    
    # 1. 地面脈動多重光圈
    rad_x = int(32 + 10 * pulse)
    rad_y = int(rad_x * 0.35)
    rg = QRadialGradient(0, 12, rad_x)
    rg.setColorAt(0.0, QColor(high_c[0], high_c[1], high_c[2], int(alpha * 0.7)))
    rg.setColorAt(0.5, QColor(main_c[0], main_c[1], main_c[2], int(alpha * 0.4)))
    rg.setColorAt(1.0, QColor(main_c[0], main_c[1], main_c[2], 0))
    painter.setBrush(QBrush(rg))
    painter.setPen(QPen(QColor(high_c[0], high_c[1], high_c[2], alpha), 1.5))
    painter.drawEllipse(QPointF(0, 12), rad_x, rad_y)

    if is_union:
        # 1.5 聯盟光環專屬：金色八芒星軌複合陣
        for oct_idx in [0, 1]:
            poly = QPolygonF()
            base_ang = t * 1.5 + oct_idx * (math.pi / 4)
            for pt_i in range(4):
                ang = base_ang + pt_i * (math.pi / 2)
                poly.append(QPointF(math.cos(ang) * rad_x * 0.9, 12 + math.sin(ang) * rad_y * 0.9))
            painter.setPen(QPen(QColor(255, 215, 80, int(alpha * 0.75)), 1.3))
            painter.setBrush(Qt.NoBrush)
            painter.drawPolygon(poly)

        # 2. 四色光環融合旋轉神珠 (紅/黃/藍/綠 對應攻擊/加速/防禦/吸血四大光環)
        union_colors = [
            (255, 80, 40),   # 攻擊光環 (紅)
            (255, 225, 50),  # 黃色光環 (黃)
            (60, 160, 255),  # 藍色光環 (藍)
            (60, 240, 140)   # 吸血光環 (綠)
        ]
        for i, u_col in enumerate(union_colors):
            ang = -t * 2.5 + i * (math.pi / 2)
            ox = math.cos(ang) * rad_x * 0.92
            oy = 12 + math.sin(ang) * rad_y * 0.92 - (pulse * 3.0)
            painter.setBrush(QBrush(QColor(u_col[0], u_col[1], u_col[2], alpha)))
            painter.setPen(QPen(QColor(255, 255, 255, alpha), 1))
            painter.drawEllipse(QPointF(ox, oy), 4.5, 4.5)

        # 3. 升騰死神幽冥魂火 (6 顆紫金交織)
        for pi in range(6):
            p_t = (t * 1.8 + pi * 0.16) % 1.0
            py = 12 - p_t * 42
            px = math.sin(t * 4.0 + pi * 1.2) * 20
            p_alpha = int(alpha * (1.0 - p_t))
            p_col = QColor(190, 80, 255, p_alpha) if pi % 2 == 0 else QColor(255, 220, 100, p_alpha)
            painter.setBrush(QBrush(p_col))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(px, py), 2.5, 2.5)
    else:
        # 普通光環環繞光符
        orb_count = 3
        orb_rad_x = rad_x * 0.85
        orb_rad_y = rad_y * 0.85
        base_ang = t * 3.0 + rot_angle * 0.02
        for i in range(orb_count):
            ang = base_ang + i * (2 * math.pi / orb_count)
            ox = math.cos(ang) * orb_rad_x
            oy = 12 + math.sin(ang) * orb_rad_y - (pulse * 4.0)
            p_rg = QRadialGradient(ox, oy, 6)
            p_rg.setColorAt(0.0, QColor(255, 255, 255, alpha))
            p_rg.setColorAt(0.6, QColor(high_c[0], high_c[1], high_c[2], int(alpha * 0.8)))
            p_rg.setColorAt(1.0, QColor(main_c[0], main_c[1], main_c[2], 0))
            painter.setBrush(QBrush(p_rg))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(ox, oy), 4, 4)
            
        # 普通升騰微光粒子
        for pi in range(4):
            p_t = (t * 1.5 + pi * 0.25) % 1.0
            py = 12 - p_t * 35
            px = math.sin(t * 5.0 + pi * 1.6) * 16
            p_alpha = int(alpha * (1.0 - p_t))
            painter.setBrush(QBrush(QColor(high_c[0], high_c[1], high_c[2], p_alpha)))
            painter.drawEllipse(QPointF(px, py), 2, 2)
        
    painter.restore()


# =========================================================================
# 次世代純代碼幾何特效引擎高階圖元庫 (Next-Gen VFX Primitives)
# =========================================================================

def _draw_bloom_line(painter, p1, p2, base_width, color, alpha, core_white=True):
    """
    繪製三層核融輝光能量光束 (Atmospheric Bloom -> Saturated Body -> White Core)
    配合 CompositionMode_Plus 呈現極致物理熾熱能量感
    """
    if isinstance(p1, (tuple, list)):
        p1 = QPointF(float(p1[0]), float(p1[1]))
    if isinstance(p2, (tuple, list)):
        p2 = QPointF(float(p2[0]), float(p2[1]))
    r, g, b = color[:3] if isinstance(color, (tuple, list)) else (color.red(), color.green(), color.blue())
    w = max(1.0, float(base_width))

    # 1. 外層大光暈 (Atmospheric Falloff Corona)
    p_corona = QPen(QColor(r, g, b, int(alpha * 0.28)), w * 3.6, Qt.SolidLine, Qt.RoundCap)
    painter.setPen(p_corona)
    painter.drawLine(p1, p2)

    # 2. 中層飽和本體 (Saturated Body Beam)
    p_body = QPen(QColor(min(255, r + 40), min(255, g + 40), min(255, b + 40), int(alpha * 0.75)), w * 1.8, Qt.SolidLine, Qt.RoundCap)
    painter.setPen(p_body)
    painter.drawLine(p1, p2)

    # 3. 核心熾熱白心 (Incandescent White-Hot Core)
    if core_white:
        p_core = QPen(QColor(255, 255, 255, alpha), max(1.5, w * 0.55), Qt.SolidLine, Qt.RoundCap)
        painter.setPen(p_core)
        painter.drawLine(p1, p2)


def _build_ribbon_mesh(cx: float, cy: float, start_deg: float, sweep_deg: float, inner_r: float, outer_r: float):
    """計算平滑帶狀網格幾何頂點與路徑"""
    steps = 24
    outer_pts = []
    inner_pts = []

    for i in range(steps + 1):
        ratio = i / steps  # 0.0 (尾部) -> 1.0 (頭部)
        ang_deg = start_deg + sweep_deg * ratio
        ang_rad = math.radians(ang_deg)

        thickness_factor = math.sin(ratio * math.pi * 0.9 + 0.1)
        cur_outer = inner_r + (outer_r - inner_r) * thickness_factor
        cur_inner = inner_r + (outer_r - inner_r) * (1.0 - thickness_factor) * 0.25

        ox = cx + math.cos(ang_rad) * cur_outer
        oy = cy + math.sin(ang_rad) * cur_outer
        ix = cx + math.cos(ang_rad) * cur_inner
        iy = cy + math.sin(ang_rad) * cur_inner

        outer_pts.append(QPointF(ox, oy))
        inner_pts.append(QPointF(ix, iy))

    path = QPainterPath()
    path.moveTo(outer_pts[0])
    for pt in outer_pts[1:]:
        path.lineTo(pt)
    for pt in reversed(inner_pts):
        path.lineTo(pt)
    path.closeSubpath()

    blade_spine = QPainterPath()
    if len(outer_pts) > 2:
        mid_pts = [(outer_pts[i] + inner_pts[i]) * 0.5 for i in range(len(outer_pts))]
        blade_spine.moveTo(mid_pts[0])
        for mpt in mid_pts[1:]:
            blade_spine.lineTo(mpt)

    return path, blade_spine, outer_pts[0], outer_pts[-1]


def _draw_ribbon_slash(painter, cx, cy, start_deg, sweep_deg, inner_r, outer_r, color, alpha, core_white=True):
    """
    繪製平滑帶狀網格刀光/揮擊流光 (Ribbon Spline Mesh - Cached)
    透過 LRU 幾何快取複用路徑頂點，消弭每幀三角函數重算
    """
    r, g, b = color[:3] if isinstance(color, (tuple, list)) else (color.red(), color.green(), color.blue())
    key = (
        "ribbon",
        round(float(cx), 1), round(float(cy), 1),
        round(float(start_deg), 1), round(float(sweep_deg), 1),
        round(float(inner_r), 1), round(float(outer_r), 1)
    )
    path, blade_spine, grad_p1, grad_p2 = _vfx_geom_cache.get_or_set(
        key,
        lambda: _build_ribbon_mesh(float(cx), float(cy), float(start_deg), float(sweep_deg), float(inner_r), float(outer_r))
    )

    # 外層大光暈
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(QColor(r, g, b, int(alpha * 0.35))))
    painter.drawPath(path)

    # 內層核心漸變色彩
    grad = QLinearGradient(grad_p1, grad_p2)
    grad.setColorAt(0.0, QColor(r, g, b, 0))
    grad.setColorAt(0.5, QColor(min(255, r + 50), min(255, g + 50), min(255, b + 50), int(alpha * 0.85)))
    grad.setColorAt(1.0, QColor(255, 255, 255, alpha) if core_white else QColor(r, g, b, alpha))
    painter.setBrush(QBrush(grad))
    painter.drawPath(path)

    # 刃口純白流光脊線
    if core_white and not blade_spine.isEmpty():
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, int(alpha * 0.95)), 2.0, Qt.SolidLine, Qt.RoundCap))
        painter.drawPath(blade_spine)


def _draw_expanding_shockwave(painter, x, y, max_radius, p, color, alpha, aspect=0.35, rings=2):
    """
    繪製動態空間衝擊破裂波紋環 (Expanding Distortion Shockwave)
    二次方減速膨脹與極速衰減邊界
    """
    r, g, b = color[:3] if isinstance(color, (tuple, list)) else (color.red(), color.green(), color.blue())
    p_ease = math.sqrt(max(0.0, min(1.0, p)))
    curr_r = max_radius * p_ease
    fade = 1.0 - p

    painter.save()
    painter.translate(x, y)
    painter.setBrush(Qt.NoBrush)

    for ri in range(rings):
        ring_r = curr_r * (1.0 - ri * 0.18)
        if ring_r <= 0:
            continue
        thick = max(1.2, 5.5 * fade * (1.0 - ri * 0.3))
        ring_alpha = int(alpha * fade * (0.85 - ri * 0.3))
        if ring_alpha <= 0:
            continue

        painter.setPen(QPen(QColor(r, g, b, ring_alpha), thick))
        painter.drawEllipse(QPointF(0, 0), ring_r, ring_r * aspect)

        # 核心亮白邊緣線
        if ri == 0 and fade > 0.3:
            painter.setPen(QPen(QColor(255, 255, 255, int(fade * alpha * 0.7)), max(1.0, thick * 0.35)))
            painter.drawEllipse(QPointF(0, 0), ring_r, ring_r * aspect)

    painter.restore()


def _draw_physics_particles(painter, ox, oy, p, count, color, alpha, seed=42,
                            spread_x=80.0, spread_y=60.0, gravity=35.0, upward=False):
    """
    物理阻尼動力學粒子發射器 (Velocity / Drag / Gravity Embers)
    生成四散碎裂或裊裊升空的真實能量餘燼
    """
    r, g, b = color[:3] if isinstance(color, (tuple, list)) else (color.red(), color.green(), color.blue())
    rnd = random.Random(seed)

    for i in range(count):
        # 決定初始發射速度向量
        ang = rnd.uniform(0, math.pi * 2)
        speed = rnd.uniform(0.5, 1.2)
        vx = math.cos(ang) * spread_x * speed
        vy = math.sin(ang) * spread_y * speed
        drag = rnd.uniform(2.5, 4.5)
        p_sz = rnd.uniform(2.0, 4.5)

        # 阻尼位移演算: x = vx * (1 - e^(-drag * t)) / drag
        t = p
        disp_factor = (1.0 - math.exp(-drag * t))
        px = ox + vx * disp_factor
        py = oy + vy * disp_factor

        if upward:
            # 向上漂浮浮力
            py -= 55.0 * (t ** 1.3)
        else:
            # 拋物線重力下墜
            py += 0.5 * gravity * (t ** 2)

        p_life = max(0.0, 1.0 - t * rnd.uniform(0.9, 1.2))
        p_alpha = int(alpha * p_life)
        if p_alpha <= 0:
            continue

        # 繪製發光微粒
        painter.setPen(Qt.NoPen)
        # 外圈微暈
        painter.setBrush(QBrush(QColor(r, g, b, int(p_alpha * 0.45))))
        painter.drawEllipse(QPointF(px, py), p_sz * 1.6, p_sz * 1.6)
        # 核心亮點
        painter.setBrush(QBrush(QColor(255, 255, 255, p_alpha)))
        painter.drawEllipse(QPointF(px, py), p_sz * 0.7, p_sz * 0.7)


def _build_lightning_path(p1: QPointF, p2: QPointF, p_step: int, jitter: float, steps: int, seed: int) -> QPainterPath:
    rnd = random.Random(seed + p_step)
    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()
    dist = math.hypot(dx, dy)
    if dist <= 0:
        return QPainterPath()
    nx = -dy / dist
    ny = dx / dist

    main_pts = [p1]
    for st in range(1, steps):
        ratio = st / steps
        cur_jit = rnd.uniform(-jitter, jitter) * (1.0 - abs(ratio - 0.5) * 0.6)
        px = p1.x() + dx * ratio + nx * cur_jit
        py = p1.y() + dy * ratio + ny * cur_jit
        main_pts.append(QPointF(px, py))
    main_pts.append(p2)

    path = QPainterPath()
    path.moveTo(main_pts[0])
    for pt in main_pts[1:]:
        path.lineTo(pt)
    return path


def _draw_crackling_lightning(painter, p1, p2, p, color, alpha, jitter=22.0, steps=7, seed=77):
    """
    碎形分叉電漿電弧 (Fractal Jagged Plasma Lightning - Cached)
    透過 LRU 離散時間步階快取路徑，大幅減免每幀 random 計算與頂點配置
    """
    if isinstance(p1, (tuple, list)):
        p1 = QPointF(float(p1[0]), float(p1[1]))
    if isinstance(p2, (tuple, list)):
        p2 = QPointF(float(p2[0]), float(p2[1]))
    r, g, b = color[:3] if isinstance(color, (tuple, list)) else (color.red(), color.green(), color.blue())
    p_step = int(p * 20.0)

    key = (
        "lightning",
        round(p1.x(), 1), round(p1.y(), 1),
        round(p2.x(), 1), round(p2.y(), 1),
        p_step, round(jitter, 1), int(steps), int(seed)
    )
    path = _vfx_geom_cache.get_or_set(
        key,
        lambda: _build_lightning_path(p1, p2, p_step, jitter, steps, seed)
    )
    if path.isEmpty():
        return

    # 外圈電暈
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(QColor(r, g, b, int(alpha * 0.4)), 6.0, Qt.SolidLine, Qt.RoundCap))
    painter.drawPath(path)
    # 中層主色電漿
    painter.setPen(QPen(QColor(min(255, r + 40), min(255, g + 40), min(255, b + 40), int(alpha * 0.85)), 3.0, Qt.SolidLine, Qt.RoundCap))
    painter.drawPath(path)
    # 核心高熱白熾電弧
    painter.setPen(QPen(QColor(255, 255, 255, alpha), 1.4, Qt.SolidLine, Qt.RoundCap))
    painter.drawPath(path)


