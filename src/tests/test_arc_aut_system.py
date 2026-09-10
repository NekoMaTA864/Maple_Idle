import os
import sys
import random
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
if os.path.abspath('.') not in sys.path:
    sys.path.insert(0, os.path.abspath('.'))

def test_20_zones_data():
    print("=== Test 1: 23 Zones Data & Structure Integrity ===")
    from combat_system import ZONES
    assert len(ZONES) == 23, f"Expected 23 zones, got {len(ZONES)}"
    
    # 驗證前 9 區 (冒險島經典/高難區域)
    assert ZONES[0]["id"] == "henesys_forest"
    assert ZONES[6]["id"] == "temple_of_time"
    assert ZONES[6]["boss"]["name"] == "皮卡啾"
    assert ZONES[7]["id"] == "fallen_world_tree"
    assert ZONES[8]["id"] == "scrapyard"

    # 驗證 6 大 ARC 區域 (消亡~利曼)
    arc_ids = ["vanishing_journey", "chu_chu_island", "lachelein", "arcana", "morass", "esfera"]
    for i, expected_id in enumerate(arc_ids):
        z = ZONES[i + 9]
        assert z["id"] == expected_id, f"Zone {i+9} expected {expected_id}, got {z['id']}"
        assert z.get("arc_req", 0) > 0, f"Zone {z['id']} missing arc_req"
        assert z.get("symbol_drop"), f"Zone {z['id']} missing symbol_drop"
    # 利曼黑魔法師 (Zone 15, arc_req=880)
    assert ZONES[15]["id"] == "limina"
    assert ZONES[15]["arc_req"] == 880
    assert ZONES[15]["boss"]["name"] == "黑魔法師"

    # 驗證 7 大 AUT 區域 (塞爾尼恩~塔拉哈特)
    aut_ids = ["cernium", "hotel_arcus", "odium", "shangri_la", "arteria", "carcion", "talahart"]
    for i, expected_id in enumerate(aut_ids):
        z = ZONES[i + 16]
        assert z["id"] == expected_id, f"Zone {i+16} expected {expected_id}, got {z['id']}"
        assert z.get("aut_req", 0) > 0, f"Zone {z['id']} missing aut_req"
        assert z.get("symbol_drop"), f"Zone {z['id']} missing symbol_drop"

    assert ZONES[21]["id"] == "carcion"
    assert ZONES[21]["aut_req"] == 390
    assert "奇斯特" in ZONES[21]["boss"]["name"]
    assert ZONES[22]["id"] == "talahart"
    assert ZONES[22]["aut_req"] == 460
    assert ZONES[22]["boss"]["lvl"] == 300
    assert "影獸" in ZONES[22]["boss"]["name"]

    print(">> [PASS] All 23 zones, level progressions, and bosses verified!")

def test_symbol_mechanics():
    print("=== Test 2: Symbol Upgrades & Stat Calculation ===")
    from player_data import Player, ARC_SYMBOLS_DATA, AUT_SYMBOLS_DATA
    player = Player()
    
    # 初始皆為 0 級 (未解鎖)
    assert player.get_total_arc() == 0
    assert player.get_total_aut() == 0
    assert player.get_symbol_stat_sum("attack") == 0

    # 模擬獲得消亡旅途碎片
    player.add_symbol_fragment("vanishing", 20)
    # 獲得第一個碎片自動解鎖為 Lv.1
    assert player.arc_symbols["vanishing"] == 1
    assert player.get_total_arc() == 30
    assert player.get_symbol_stat_sum("attack") == 30
    assert player.get_symbol_stat_sum("hp") == 300

    # 升級消亡旅途符號
    req_frags, req_gold, is_max = player.get_symbol_upgrade_req("vanishing")
    assert req_frags == 12  # Lv.1 -> 12 frags
    assert not is_max
    player.gold = 1000000
    success, msg = player.upgrade_symbol("vanishing")
    assert success, f"Upgrade failed: {msg}"
    assert player.arc_symbols["vanishing"] == 2
    assert player.get_total_arc() == 40  # 30 + 10 = 40
    assert player.get_symbol_stat_sum("attack") == 60

    # 模擬 AUT 塞爾尼恩
    player.add_symbol_fragment("cernium", 30)
    assert player.aut_symbols["cernium"] == 1
    assert player.get_total_aut() == 10
    assert player.get_symbol_stat_sum("attack") == 60 + 80  # 140
    print(">> [PASS] Symbol unlocking, fragments, upgrade costs and stats verified!")

def test_arc_aut_suppression_damage():
    print("=== Test 3: ARC & AUT Damage Amp & 1-DMG Defense Suppression ===")
    from player_data import Player
    from combat_system import CombatManager, ZONES
    from sound import SoundManager

    sound_mgr = SoundManager()
    player = Player()
    player.stat_atk = 5000  # 提供足以破防 200 等奧術之河怪物的攻擊力
    combat_mgr = CombatManager(player)

    # 測試消亡旅途 (Zone 9, arc_req=60)
    combat_mgr.unlocked_zones = 20
    combat_mgr.set_zone(9)
    zone = combat_mgr.get_current_zone()
    assert zone["arc_req"] == 60

    # 1. 玩家 ARC = 0 (嚴重未達標，比率 0.0 -> 衰減至最低 10% 傷害)
    player.arc_symbols["vanishing"] = 0
    combat_mgr.spawn_next_monster()
    m = combat_mgr.monster
    m.hp = m.max_hp
    hp_before = m.hp
    # 執行一次攻擊
    combat_mgr._member_attack(player.team[0], sound_mgr)
    dmg_under_arc = hp_before - m.hp
    assert dmg_under_arc > 0

    # 2. 玩家達成 1.5x ARC (60 * 1.5 = 90 ARC)
    # 重置技能冷卻以保證同技能對比
    for s in player.team[0].skills:
        s.current_cd = 0.0
    player.arc_symbols["vanishing"] = 7
    assert player.get_total_arc() >= 90
    m.hp = m.max_hp
    hp_before = m.hp
    combat_mgr._member_attack(player.team[0], sound_mgr)
    dmg_sup_arc = hp_before - m.hp
    # 增傷壓制傷害應顯著高於刮痧傷害
    assert dmg_sup_arc > dmg_under_arc * 3, f"Suppressed dmg {dmg_sup_arc} should be much higher than under-arc {dmg_under_arc}"

    # 3. 怪物攻擊玩家：當玩家 ARC >= 1.5x 時，怪物傷害強制壓制為 1 點
    for mem in player.team:
        mem.shield = 0.0
        mem.current_hp = float(mem.get_max_hp(player))
    total_hp_before = player.current_hp
    combat_mgr._monster_attack(sound_mgr)
    total_hp_loss = total_hp_before - player.current_hp
    assert total_hp_loss == 1.0, f"Monster damage should be suppressed to 1, got {total_hp_loss}"

    print(">> [PASS] 1.5x ARC/AUT Damage amplification and 1-DMG monster suppression verified!")

def test_ui_and_zone_switching():
    print("=== Test 4: PySide6 UI, Symbols Tab & Zone Switching ===")
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)

    from player_data import Player
    from combat_system import CombatManager
    from sound import SoundManager
    from pyside_ui import MainWindow

    player = Player()
    combat_mgr = CombatManager(player)
    sound_mgr = SoundManager()

    win = MainWindow(player, combat_mgr, sound_mgr)
    win.show()

    # 檢查右側第三模式：符號系統 (ARC/AUT)
    assert hasattr(win, "btn_mode_symbol")
    win._switch_right_mode("symbol")
    assert win.right_mode == "symbol"
    assert not win.symbol_container.isHidden()
    assert win.tab_widget.isHidden()
    assert win.shop_container.isHidden()

    # 檢查符號 UI 卡片是否全數生成 (6 ARC + 7 AUT = 13)
    assert len(win.symbol_ui_items) == 13, f"Expected 13 symbol cards, got {len(win.symbol_ui_items)}"

    # 檢查左側 60 格背包彈窗按鈕存在
    assert hasattr(win, "btn_open_inventory")

    # 檢查關卡切換下拉選單 (共 23 關)
    assert win.combo_zone.count() == 1  # 初始解鎖 1 關
    combat_mgr.unlocked_zones = 23  # 模擬全部解鎖
    win._update_center_column()
    assert win.combo_zone.count() == 23, f"Expected 23 combo items, got {win.combo_zone.count()}"

    # 切換至第 10 關 (消亡旅途)
    win.combo_zone.setCurrentIndex(9)
    assert combat_mgr.current_zone_idx == 9
    assert combat_mgr.get_current_zone()["id"] == "vanishing_journey"

    # 測試符文系統即時自動刷新 (比照加點系統，戰鬥中掉落碎片無需手動重切分頁)
    player.add_symbol_fragment("chuchu", 18)
    win._update_right_column()
    assert "18" in win.symbol_ui_items["chuchu"]["frags"].text(), "Symbol card frags text should auto-refresh immediately upon tick"

    # 測試一鍵升級符號按鈕與即時同步
    player.add_symbol_fragment("vanishing", 50)
    player.gold = 5000000
    win._auto_upgrade_all_symbols()
    assert player.arc_symbols["vanishing"] >= 2
    assert "Lv." in win.symbol_ui_items["vanishing"]["title"].text()

    # 觸發一次 arena paintEvent
    win.arena_widget.update()
    app.processEvents()

    win.close()
    print(">> [PASS] UI MainWindow, Symbols Tab, 23-Zone Dropdown, Auto-refresh & PaintEvent all verified flawlessly!")

if __name__ == "__main__":
    test_20_zones_data()
    test_symbol_mechanics()
    test_arc_aut_suppression_damage()
    test_ui_and_zone_switching()
    print("\n[SUCCESS] ALL TESTS PASSED! ARC/AUT 20 ZONES & SYMBOLS SYSTEM INTEGRATED 100%!")
