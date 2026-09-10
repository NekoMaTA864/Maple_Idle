# -*- coding: utf-8 -*-
"""
測試同時特效數量上限 (Effect Cap)、優先權淘汰機制與 VFX 快取層
(tests/test_vfx_effect_cap.py)
"""

import sys
import os

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from combat_system import VisualEffectManager, VisualEffect, HIGH_PRIORITY_VFX
import vfx_core


def test_vfx_concurrency_cap():
    print("=== Test 1: VFX Concurrency Cap (Max 18 Effects) ===")
    vfx_mgr = VisualEffectManager()
    assert vfx_mgr.MAX_CONCURRENT_EFFECTS == 18, f"Expected cap 18, got {vfx_mgr.MAX_CONCURRENT_EFFECTS}"

    # 模擬 35 個特效連續觸發
    for i in range(35):
        vfx_mgr.add_vfx("slash", 100, 100, 200, 200, duration=1.0)

    assert len(vfx_mgr.effects) == 18, f"Effects count must not exceed 18, got {len(vfx_mgr.effects)}"
    assert vfx_mgr.total_dropped_effects == 17, f"Expected 17 dropped effects, got {vfx_mgr.total_dropped_effects}"
    print(">> [PASS] Concurrency cap and total_dropped_effects verified!")


def test_vfx_priority_eviction():
    print("=== Test 2: Priority-Based VFX Eviction ===")
    vfx_mgr = VisualEffectManager()

    # 1. 加入 1 個即將結束的普通特效 (p > 0.7)
    vfx_mgr.add_vfx("slash", 100, 100, 200, 200, duration=1.0)
    expiring_eff = vfx_mgr.effects[0]
    expiring_eff.timer = 0.2  # progress = 0.8 (即將淡出)

    # 2. 加入 1 個核心大招全屏特效 (progress = 0.1)
    vfx_mgr.add_vfx("holy", 100, 100, 200, 200, duration=2.0)
    holy_eff = vfx_mgr.effects[1]
    holy_eff.timer = 1.8  # progress = 0.1

    # 3. 陸續塞入一般特效填滿至 18 個上限
    for _ in range(16):
        vfx_mgr.add_vfx("arrow", 100, 100, 200, 200, duration=1.0)

    assert len(vfx_mgr.effects) == 18
    assert expiring_eff in vfx_mgr.effects
    assert holy_eff in vfx_mgr.effects

    # 4. 再加入第 19 個特效 -> 必須優先淘汰即將結束的 expiring_eff，且 holy_eff 必須被保護！
    vfx_mgr.add_vfx("ice", 100, 100, 200, 200, duration=1.0)

    assert len(vfx_mgr.effects) == 18
    assert expiring_eff not in vfx_mgr.effects, "Expiring effect (progress > 0.7) should have been evicted first!"
    assert holy_eff in vfx_mgr.effects, "High-priority holy effect must remain protected!"
    print(">> [PASS] Low priority/expiring effects evicted first, ultimates protected!")


def test_vfx_bounded_cache_and_easing():
    print("=== Test 3: BoundedCache LRU & Common Easing ===")
    # 測試 LRU 有界淘汰
    test_cache = vfx_core.BoundedCache(maxsize=3)
    test_cache.get_or_set("a", lambda: 1)
    test_cache.get_or_set("b", lambda: 2)
    test_cache.get_or_set("c", lambda: 3)
    # 存取 'a' 使其變為最近使用
    test_cache.get_or_set("a", lambda: 100)
    # 加入 'd'，'b' 應該被淘汰
    test_cache.get_or_set("d", lambda: 4)

    assert "b" not in test_cache, "'b' should have been evicted by LRU policy"
    assert "a" in test_cache and test_cache["a"] == 1
    assert "c" in test_cache
    assert "d" in test_cache

    # 測試 Easing 邊界值 [0.0, 1.0]
    for p in [0.0, 0.25, 0.5, 0.75, 1.0]:
        assert 0.0 <= vfx_core.ease_in_out(p) <= 1.0
        assert 0.0 <= vfx_core.ease_out_quad(p) <= 1.0
        assert 0.0 <= vfx_core.ease_in_quad(p) <= 1.0
        assert 0.0 <= vfx_core.ease_out_cubic(p) <= 1.0
        assert 0.0 <= vfx_core.ease_out_sine(p) <= 1.0

    assert vfx_core.ease_in_out(0.0) == 0.0
    assert abs(vfx_core.ease_in_out(1.0) - 1.0) < 1e-5
    print(">> [PASS] BoundedCache LRU and easing mathematics verified!")


if __name__ == "__main__":
    test_vfx_concurrency_cap()
    test_vfx_priority_eviction()
    test_vfx_bounded_cache_and_easing()
    print("\n[SUCCESS] ALL VFX CONCURRENCY CAP & CACHE TESTS PASSED!")

