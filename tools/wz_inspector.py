"""
新楓之谷 WZ 檔案檢測與結構拆解工具 (WZ Inspector)
支援單一 .wz 檔案、多分卷檔檢測、以及整個資料夾批次掃描。
"""

import sys
import os
import struct

# 楓之谷職業 ID 映射字典
JOB_NAMES = {
    "000": "新手 (Beginner)",
    "100": "劍士一轉",
    "110": "狂戰士 (Fighter)",
    "111": "十字軍 (Crusader)",
    "112": "英雄 (Hero)",
    "120": "見習騎士 (Page)",
    "121": "騎士 (White Knight)",
    "122": "聖騎士 (Paladin)",
    "130": "槍騎兵 (Spearman)",
    "131": "嗜血狂騎 (Dragon Knight)",
    "132": "黑騎士 (Dark Knight)",
    "200": "法師一轉",
    "210": "火毒巫師",
    "211": "火毒魔導士",
    "212": "火毒大魔導士",
    "220": "冰雷巫師",
    "221": "冰雷魔導士",
    "222": "冰雷大魔導士",
    "230": "僧侶 (Cleric)",
    "231": "祭司 (Priest)",
    "232": "主教 (Bishop)",
    "300": "弓箭手一轉",
    "310": "獵人 (Hunter)",
    "311": "遊俠 (Ranger)",
    "312": "箭神 (Bowmaster)",
    "320": "弩弓手 (Crossbowman)",
    "321": "狙擊手 (Sniper)",
    "322": "神射手 (Marksman)",
    "330": "開拓者一轉",
    "331": "開拓者二轉",
    "332": "開拓者 (Pathfinder)",
    "400": "盜賊一轉",
    "410": "刺客 (Assassin)",
    "411": "暗殺者 (Hermit)",
    "412": "夜使者 (Night Lord)",
    "420": "俠盜 (Bandit)",
    "421": "神偷 (Chief Bandit)",
    "422": "暗影神偷 (Shadower)",
    "430": "下忍 (Blade Recruit)",
    "431": "中忍 (Blade Acolyte)",
    "432": "上忍 (Blade Specialist)",
    "433": "隱忍 (Blade Lord)",
    "434": "影武者 (Dual Blade)",
    "500": "海盜一轉",
    "510": "打手 (Brawler)",
    "511": "狂奪 (Marauder)",
    "512": "拳霸 (Buccaneer)",
    "520": "槍手 (Gunslinger)",
    "521": "神槍手 (Outlaw)",
    "522": "槍神 (Corsair)",
    "530": "重砲兵一轉",
    "531": "重砲兵二轉",
    "532": "重砲指揮官 (Cannoneer)",
    "1000": "皇家騎士團新手",
    "1100": "聖魂劍士一轉",
    "1110": "聖魂劍士二轉",
    "1111": "聖魂劍士三轉",
    "1112": "聖魂劍士 (Dawn Warrior)",
    "1200": "烈焰巫師一轉",
    "1210": "烈焰巫師二轉",
    "1211": "烈焰巫師三轉",
    "1212": "烈焰巫師 (Flame Wizard)",
    "1300": "破風使者一轉",
    "1310": "破風使者二轉",
    "1311": "破風使者三轉",
    "1312": "破風使者 (Wind Archer)",
    "1400": "暗夜行者一轉",
    "1410": "暗夜行者二轉",
    "1411": "暗夜行者三轉",
    "1412": "暗夜行者 (Night Walker)",
    "1500": "閃雷悍將一轉",
    "1510": "閃雷悍將二轉",
    "1511": "閃雷悍將三轉",
    "1512": "閃雷悍將 (Thunder Breaker)",
    "3000": "末日反抗軍新手",
    "3200": "煉獄巫師一轉",
    "3210": "煉獄巫師二轉",
    "3211": "煉獄巫師三轉",
    "3212": "煉獄巫師 (Battle Mage)",
    "3300": "狂豹獵人一轉",
    "3310": "狂豹獵人二轉",
    "3311": "狂豹獵人三轉",
    "3312": "狂豹獵人 (Wild Hunter)",
    "3500": "機甲戰神一轉",
    "3510": "機甲戰神二轉",
    "3511": "機甲戰神三轉",
    "3512": "機甲戰神 (Mechanic)",
    "3700": "爆拳槍神一轉",
    "3710": "爆拳槍神二轉",
    "3711": "爆拳槍神三轉",
    "3712": "爆拳槍神 (Blaster)",
    "MobSkill": "怪物與BOSS專用技能 (MobSkill)",
    "Dragon": "龍族 / 龍魔導士技能 (Dragon)",
    "AbyssExpedition": "深淵遠征隊專用技能",
    "Roguelike": "Roguelike 特殊副本技能",
    "_Canvas": "畫布與視覺特效資源索引 (_Canvas)"
}


def decode_wz_string(data, offset):
    """解密 WZ 內部字串"""
    if offset >= len(data):
        return "", offset
    
    len_byte = data[offset]
    offset += 1
    
    if len_byte == 0:
        return "", offset
    
    if len_byte < 128:
        # Unicode string
        str_len = len_byte * 2
        # Unicode XOR
        mask = 0xAAAA
        chars = []
        for i in range(0, str_len, 2):
            if offset + i + 1 < len(data):
                val = data[offset + i] | (data[offset + i + 1] << 8)
                chars.append(chr(val ^ mask))
                mask = (mask + 1) & 0xFFFF
        offset += str_len
        return "".join(chars), offset
    else:
        # ASCII string with 0xAA rotating mask
        str_len = 256 - len_byte
        mask = 0xAA
        chars = []
        for i in range(str_len):
            if offset + i < len(data):
                chars.append(chr(data[offset + i] ^ mask))
                mask = (mask + 1) & 0xFF
        offset += str_len
        return "".join(chars), offset


def inspect_wz_file(file_path):
    """檢測單一 WZ 檔案的結構與內容"""
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    
    report = {
        "file_path": file_path,
        "file_name": file_name,
        "size_bytes": file_size,
        "is_wz": False,
        "header_desc": "",
        "entries": [],
        "known_jobs": [],
        "summary": ""
    }
    
    if file_size < 60:
        report["summary"] = "檔案過小，並非有效的 WZ 封裝檔"
        return report
    
    with open(file_path, "rb") as f:
        data = f.read(min(file_size, 1024 * 1024))  # 讀取前 1MB 用於目錄掃描
    
    if data[:4] != b"PKG1":
        report["summary"] = "檔頭並非 PKG1，可能不是標準 WZ 檔"
        return report
    
    report["is_wz"] = True
    pkg_size, start_offset = struct.unpack("<QI", data[4:16])
    desc = data[16:start_offset].decode("ascii", errors="ignore").strip("\x00")
    report["header_desc"] = desc
    
    # 嘗試解析目錄段
    offset = start_offset
    if offset + 3 <= len(data):
        ver_hash = int.from_bytes(data[offset:offset+2], "little")
        offset += 2
        count = data[offset]
        offset += 1
        
        for _ in range(count):
            if offset >= len(data):
                break
            entry_type = data[offset]
            offset += 1
            name, offset = decode_wz_string(data, offset)
            if not name:
                break
            
            # 跳過 size, checksum, offset (約 6~10 bytes)
            offset += 6
            
            clean_name = name.replace(".img", "")
            job_desc = JOB_NAMES.get(clean_name, "")
            
            report["entries"].append({
                "type": entry_type,
                "name": name,
                "description": job_desc
            })
            
            if job_desc:
                report["known_jobs"].append(f"{name} -> {job_desc}")
    
    # 確保 Windows cp950 主控台輸出安全
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(errors="replace")
        except Exception:
            pass

    # 分析檔案角色
    if file_size <= 512 and report["entries"]:
        report["summary"] = (
            f"[*] 64位元階層式骨架索引檔 (僅 {file_size} bytes)\n"
            f"   內部定義了 {len(report['entries'])} 個子目錄節點：\n"
            f"   " + ", ".join([e['name'] for e in report['entries']]) + "\n"
            f"   【提示】實際技能數值與動畫貼圖位於同目錄下的分卷檔（例如 {file_name.replace('.wz', '_000.wz')} 等）！"
        )
    elif report["known_jobs"]:
        report["summary"] = (
            f"[*] 實體資料檔 (大小 {file_size / (1024*1024):.2f} MB)\n"
            f"   成功識別出 {len(report['known_jobs'])} 個職業/技能項目！\n"
            f"   包含：\n   " + "\n   ".join(report["known_jobs"][:10]) +
            ("\n   ..." if len(report["known_jobs"]) > 10 else "")
        )
    else:
        report["summary"] = f"WZ 封裝檔 (大小 {file_size / (1024*1024):.2f} MB)，包含 {len(report['entries'])} 個節點"
    
    return report


def scan_target(target_path):
    """掃描目標檔案或資料夾"""
    target_path = target_path.strip('"').strip("'")
    
    if not os.path.exists(target_path):
        print(f"[-] 找不到指定路徑: {target_path}")
        return
    
    wz_files = []
    if os.path.isfile(target_path):
        wz_files.append(target_path)
    else:
        for root, _, files in os.walk(target_path):
            for file in files:
                if file.lower().endswith(".wz"):
                    wz_files.append(os.path.join(root, file))
    
    if not wz_files:
        print(f"[-] 在 {target_path} 中未發現任何 .wz 檔案！")
        return
    
    print("=" * 70)
    print(f" 新楓之谷 WZ 檔案結構分析報告")
    print(f" 檢測目標: {target_path}")
    print(f" 發現 WZ 檔案數量: {len(wz_files)}")
    print("=" * 70)
    
    full_reports = []
    for fpath in wz_files:
        rep = inspect_wz_file(fpath)
        full_reports.append(rep)
        
        print(f"\n[檔案] {rep['file_name']}  ({rep['size_bytes']:,} Bytes / {rep['size_bytes']/(1024*1024):.2f} MB)")
        print(f"       {rep['summary']}")
    
    # 輸出建議
    print("\n" + "=" * 70)
    print(" 結論與打包指引：")
    
    has_large_data = any(r['size_bytes'] > 1024 * 1024 for r in full_reports)
    has_stub = any(r['size_bytes'] < 1024 for r in full_reports)
    
    if has_stub and not has_large_data:
        print("  [!] 目前所檢測的都是「骨架索引檔（153 bytes 級別）」。")
        print("     實際的技能資料（如英雄、主教、夜使者等技能）尚未在現有檔案中。")
        print("     【建議】：回家後請尋找遊戲安裝目錄 (MapleStory\\Data\\Skill\\)")
        print("     將帶有數字後綴的分卷檔（如 Skill_000.wz、Skill_001.wz ...）")
        print("     或整個 Skill 資料夾一起打包帶來！")
    elif has_large_data:
        print("  [O] 成功檢測到「實體技能資料檔」！")
        print("     這些檔案包含了真實的技能貼圖、動畫與數值，請完整打包帶過來即可解讀。")
    print("=" * 70)
    
    # 寫入文字摘要檔
    report_out = "wz_inspect_report.txt"
    with open(report_out, "w", encoding="utf-8") as f:
        f.write("新楓之谷 WZ 檔案檢測報告\n")
        f.write("=" * 50 + "\n")
        for r in full_reports:
            f.write(f"檔案: {r['file_name']} ({r['size_bytes']} bytes)\n")
            f.write(f"說明: {r['summary']}\n")
            if r['known_jobs']:
                f.write("識別職業:\n")
                for job in r['known_jobs']:
                    f.write(f"  - {job}\n")
            f.write("\n")
    print(f"\n[+] 詳細檢測紀錄已存檔至: {os.path.abspath(report_out)}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scan_target(sys.argv[1])
    else:
        # 互動式輸入
        print("=" * 60)
        print(" 新楓之谷 WZ 檔案檢測小工具")
        print(" 請輸入欲檢測的 .wz 檔案路徑 或 包含 wz 檔案的資料夾路徑")
        print(" （也可直接把 .wz 檔案拖曳進本視窗後按 Enter）")
        print("=" * 60)
        user_input = input("\n請輸入路徑 [預設為當前目錄下的 Skill.wz]: ").strip()
        if not user_input:
            user_input = "Skill.wz"
        scan_target(user_input)
        input("\n請按 Enter 鍵結束...")
