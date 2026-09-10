"""
《新楓之谷：放置遠征隊》核心玩法百科 & 機率資料大全 (game_guide_dialog.py)
整合裝備潛能(主潛/附加)、內在能力、黃金轉蛋機、萌獸與寵物系統的完整數值與機率導覽
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QTabWidget, QTextBrowser
)
from PySide6.QtCore import Qt
from ui_styles import QSS_DARK_THEME


class GameGuideDialog(QDialog):
    """楓之谷遠征隊玩法百科與機率指南彈窗"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📖 新楓之谷：放置遠征隊 - 玩法百科 & 機率資料大全")
        self.resize(780, 800)
        self.setStyleSheet(QSS_DARK_THEME)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # 頂部標題與裝飾
        head_row = QHBoxLayout()
        title_lbl = QLabel(
            "<b style='font-size: 16px; color: #ffd700;'>"
            "🍁 新楓之谷正統數值百科與完整機率指南</b>"
        )
        head_row.addWidget(title_lbl)
        head_row.addStretch()

        btn_close = QPushButton("關閉 [Esc]")
        btn_close.setStyleSheet("background-color: #2d3748; color: #cbd5e1; border: 1px solid #4a5568; padding: 4px 12px; border-radius: 4px;")
        btn_close.clicked.connect(self.accept)
        head_row.addWidget(btn_close)
        main_layout.addLayout(head_row)

        # 分頁元件
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                background: #1a202c;
                color: #a0aec0;
                padding: 8px 14px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #2b4c7e;
                color: #ffd700;
                border-bottom: 2px solid #ecc94b;
            }
        """)

        # 5 大核心分頁
        self.tabs.addTab(self._create_equip_potential_tab(), "🔮 裝備潛能機率")
        self.tabs.addTab(self._create_inner_ability_tab(), "✨ 內在能力 (內潛)")
        self.tabs.addTab(self._create_gachapon_tab(), "🎰 黃金轉蛋機全獎池")
        self.tabs.addTab(self._create_familiar_tab(), "🐲 萌獸與終傷乘區")
        self.tabs.addTab(self._create_pet_tab(), "🐾 寵物與月光P寵神裝")

        main_layout.addWidget(self.tabs, 1)

    # ==================== Tab 1: 裝備潛能機率表 ====================
    def _create_equip_potential_tab(self) -> QWidget:
        tb = QTextBrowser()
        tb.setOpenExternalLinks(False)
        tb.setStyleSheet("background-color: #121622; color: #e2e8f0; border: 1px solid #2a3447; border-radius: 6px; padding: 12px; font-size: 12px; line-height: 1.6;")
        
        html = """
        <h2 style='color: #63b3ed; margin-top: 0;'>🔮 裝備潛能系統：部位限制與頂級詞條庫</h2>
        <p style='color: #cbd5e1;'>潛能永久賦予於裝備欄位，洗練永不降階。洗潛時以<b>該部位最高專屬規則</b>生成詞條：</p>

        <table border='1' cellspacing='0' cellpadding='6' style='border-color: #2d3748; width: 100%; border-collapse: collapse;'>
            <tr style='background-color: #1a233a; color: #ffd700;'>
                <th>裝備部位</th>
                <th>官方正統專屬限制詞條</th>
                <th>傳奇 (Legendary) 頂級數值</th>
                <th>罕見 (Unique) 頂級數值</th>
            </tr>
            <tr>
                <td><b>武器 / 副武 / 能源 / 徽章<br><span style='color:#a0aec0;'>(WSE 核心輸出位)</span></b></td>
                <td><b style='color: #fc8181;'>攻擊力 %、BOSS 傷害 %、無視防禦 %、總傷害 %</b></td>
                <td>攻擊力 +12% / +9%<br>BOSS傷 +40% / +35%<br>無視防禦 +35% / +30%</td>
                <td>攻擊力 +9%<br>BOSS傷 +30%<br>無視防禦 +15%</td>
            </tr>
            <tr>
                <td><b>手套 (Gloves)</b></td>
                <td><b style='color: #f6ad55;'>暴擊傷害 % (TMS 全域唯一部位)</b>、暴擊率 %、攻擊速度</td>
                <td><b style='color: #f6ad55;'>暴擊傷害 +8%</b><br>暴擊率 +10%、全屬性 +9%</td>
                <td><b style='color: #f6ad55;'>暴擊傷害 +6%</b><br>暴擊率 +9%、全屬性 +6%</td>
            </tr>
            <tr>
                <td><b>帽子 (Hat)</b></td>
                <td><b style='color: #68d391;'>技能冷卻時間減少 (-CD秒)</b>、HP%、防禦%</td>
                <td><b style='color: #68d391;'>技能冷卻時間 -2秒 / -1秒</b><br>全屬性 +9%、HP +12%</td>
                <td><b style='color: #68d391;'>技能冷卻時間 -1秒</b><br>HP +8%、全屬性 +6%</td>
            </tr>
            <tr>
                <td><b>飾品類 (Acc)<br><span style='color:#a0aec0;'>(戒指/項鍊/眼罩/印記/耳環/腰帶/口袋)</span></b></td>
                <td><b style='color: #ecc94b;'>道具掉落率 %、楓幣獲得量 %</b>、普攻吸血、攻擊力</td>
                <td><b style='color: #ecc94b;'>掉寶率 +20%</b><br><b style='color: #ecc94b;'>楓幣獲得量 +20%</b><br>普攻吸血 +5%、全屬 +9%</td>
                <td>掉寶率 +15%<br>楓幣獲得量 +15%<br>普攻吸血 +3%、全屬 +6%</td>
            </tr>
            <tr>
                <td><b>一般防具<br><span style='color:#a0aec0;'>(上衣/褲子/鞋子/披風/肩膀)</span></b></td>
                <td>全屬性 %、最大生命 HP %、防禦力 %、攻擊力</td>
                <td>全屬性 +12% / +9%<br>HP +12%、防禦 +12%</td>
                <td>全屬性 +6%<br>HP +8%、防禦 +8%</td>
            </tr>
        </table>

        <h3 style='color: #9f7aea; margin-top: 18px;'>🌟 附加潛能 (Bonus Potential) 詞條庫</h3>
        <p style='color: #cbd5e1;'>附加潛能與主潛能獨立存在，提供額外強效純數值加成：</p>
        <table border='1' cellspacing='0' cellpadding='5' style='border-color: #2d3748; width: 100%; border-collapse: collapse;'>
            <tr style='background-color: #1a233a; color: #b794f4;'>
                <th>階級</th>
                <th>WSE 部位核心詞條</th>
                <th>手套部位核心詞條</th>
                <th>全防具/飾品核心詞條</th>
            </tr>
            <tr>
                <td><b>傳奇 (Legendary)</b></td>
                <td>[附加] 攻擊力 +8%、BOSS傷 +18%、無視防禦 +15%、攻擊力 +30</td>
                <td>[附加] 暴傷 +4%、攻擊力 +24、全屬性 +5%</td>
                <td>[附加] 全屬性 +6%、攻擊力 +20、HP +800</td>
            </tr>
            <tr>
                <td><b>罕見 (Unique)</b></td>
                <td>[附加] 攻擊力 +6%、BOSS傷 +12%、無視防禦 +10%、攻擊力 +22</td>
                <td>[附加] 暴傷 +3%、攻擊力 +18、全屬性 +4%</td>
                <td>[附加] 全屬性 +4%、攻擊力 +16、HP +500</td>
            </tr>
            <tr>
                <td><b>稀有 (Epic)</b></td>
                <td>[附加] 攻擊力 +4%、攻擊力 +16、暴擊率 +4%</td>
                <td>[附加] 暴傷 +2%、攻擊力 +14、全屬性 +2%</td>
                <td>[附加] 全屬性 +2%、攻擊力 +12、HP +300</td>
            </tr>
            <tr>
                <td><b>特殊 (Rare)</b></td>
                <td>[附加] 攻擊力 +10、最大生命 +150、全屬性 +4、防禦力 +15</td>
                <td>[附加] 攻擊力 +10、最大生命 +150、全屬性 +4</td>
                <td>[附加] 攻擊力 +10、最大生命 +150、全屬性 +4</td>
            </tr>
        </table>

        <h3 style='color: #ecc94b; margin-top: 18px;'>🎲 四大方塊類型與升階機率</h3>
        <ul>
            <li><b>📦 楓方塊 ($6,000)</b>：重置主潛能，最高升級至 <b>稀有 (Epic)</b>。升階率約 15%。</li>
            <li><b>🌟 閃耀方塊 ($30,000)</b>：重置主潛能，最高升級至 <b>傳奇 (Legendary)</b>。特殊$\to$稀有: 20%，稀有$\to$罕見: 8%，罕見$\to$傳奇: 3.5%。</li>
            <li><b>📦 可疑附加方塊 ($15,000)</b>：重置附加潛能，最高升級至 <b>稀有 (Epic)</b>。升階率約 12%。</li>
            <li><b>🌟 閃耀附加方塊 ($50,000)</b>：重置附加潛能，最高升級至 <b>傳奇 (Legendary)</b>。特殊$\to$稀有: 18%，稀有$\to$罕見: 7%，罕見$\to$傳奇: 3.0%。</li>
        </ul>
        """
        tb.setHtml(html)
        return tb

    # ==================== Tab 2: 內在能力機率表 ====================
    def _create_inner_ability_tab(self) -> QWidget:
        tb = QTextBrowser()
        tb.setOpenExternalLinks(False)
        tb.setStyleSheet("background-color: #121622; color: #e2e8f0; border: 1px solid #2a3447; border-radius: 6px; padding: 12px; font-size: 12px; line-height: 1.6;")

        html = """
        <h2 style='color: #ecc94b; margin-top: 0;'>✨ 內在能力 (Inner Ability) 正統機制與詞條庫</h2>
        <p style='color: #cbd5e1;'>原版 TMS 規格考究實作：消耗名譽點數 (Honor EXP) 進行洗練，具備防掉階保護與排數極限法則：</p>

        <div style='background-color: #1a2234; border-left: 4px solid #48bb78; padding: 8px 12px; margin-bottom: 12px;'>
            <b style='color: #48bb78;'>🛡️ 核心防掉階與排數規則：</b><br>
            1. <b>永不降階</b>：升級至特殊/稀有/罕見/傳說後，後續洗練絕對不會降回低階級。<br>
            2. <b>首排傳說保底</b>：達到傳說階級時，<b>第 1 排必定為傳說級頂規詞條</b>！<br>
            3. <b>二三排極限</b>：第 2、3 排潛能最高上限僅能出現<b>罕見 (Unique)</b> 級詞條。<br>
            4. <b>鎖定排數</b>：洗練時可鎖定最多 2 排已洗出的神級詞條（鎖定 1 排額外消耗 +3,000 名譽，鎖定 2 排額外消耗 +10,000 名譽）。
        </div>

        <table border='1' cellspacing='0' cellpadding='6' style='border-color: #2d3748; width: 100%; border-collapse: collapse;'>
            <tr style='background-color: #1a233a; color: #ffd700;'>
                <th>詞條類型</th>
                <th>傳說 (Legendary)<br><span style='color:#68d391;'>(首排專屬)</span></th>
                <th>罕見 (Unique)<br><span style='color:#ecc94b;'>(二三排極限)</span></th>
                <th>稀有 (Epic)</th>
                <th>特殊 (Rare)</th>
                <th>實戰核心價值說明</th>
            </tr>
            <tr>
                <td><b>略過技能冷卻時間 (無冷)</b></td>
                <td><b style='color:#68d391;'>20% 機率略過</b></td>
                <td><b style='color:#ecc94b;'>10% 機率略過</b></td>
                <td>5% 機率略過</td>
                <td>-</td>
                <td>施放主力大招時直接刷新冷卻時間，可連續爆發！</td>
            </tr>
            <tr>
                <td><b>BOSS 怪物傷害增加 (B傷)</b></td>
                <td><b style='color:#68d391;'>+20%</b></td>
                <td><b style='color:#ecc94b;'>+10%</b></td>
                <td>+6%</td>
                <td>+3%</td>
                <td>挑戰首領與深淵副本之必備核心增傷。</td>
            </tr>
            <tr>
                <td><b>增益效果持續時間增加 (加持)</b></td>
                <td><b style='color:#68d391;'>+50%</b></td>
                <td><b style='color:#ecc94b;'>+35%</b></td>
                <td>+20%</td>
                <td>+10%</td>
                <td>大幅延長全隊終傷增幅、無敵與爆擊 Buff 時間。</td>
            </tr>
            <tr>
                <td><b>攻擊速度階段提升</b></td>
                <td><b style='color:#68d391;'>+0.20s 攻速提升</b></td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td><b>傳說首排專屬神技！</b>普攻與技能起手縮短，輸出頻率激增。</td>
            </tr>
            <tr>
                <td><b>被動技能等級提升 +1</b></td>
                <td><b style='color:#68d391;'>全隊傷害 +10%</b></td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td><b>傳說首排專屬神技！</b>直接提高全遠征隊被動光環威力。</td>
            </tr>
            <tr>
                <td><b>暴擊機率增加</b></td>
                <td><b style='color:#68d391;'>+30%</b></td>
                <td><b style='color:#ecc94b;'>+18%</b></td>
                <td>+10%</td>
                <td>+5%</td>
                <td>讓隊伍迅速湊滿 100% 滿爆擊，大幅釋放裝備詞條空間。</td>
            </tr>
            <tr>
                <td><b>物理 / 魔法攻擊力</b></td>
                <td><b style='color:#68d391;'>+30 攻擊力</b></td>
                <td><b style='color:#ecc94b;'>+20 攻擊力</b></td>
                <td>+12 攻擊力</td>
                <td>+6 攻擊力</td>
                <td>紮實直接加成於角色基礎面板攻擊力。</td>
            </tr>
            <tr>
                <td><b>無視目標怪物防禦力 (Def Ignore)</b></td>
                <td><b style='color:#68d391;'>+20%</b></td>
                <td><b style='color:#ecc94b;'>+10%</b></td>
                <td>+5%</td>
                <td>-</td>
                <td><b>正統打王必備神技！</b>高階首領 (戴米安/黑魔法師) 自帶 <b>300% 防禦率</b>，實質傷害 = 100% - 300%*(1-無視)。無視堆高才能突破 5% 刮痧保底打出完整傷害！</td>
            </tr>
            <tr>
                <td><b>道具掉落率 / 楓幣獲得量</b></td>
                <td><b style='color:#68d391;'>+20%</b></td>
                <td><b style='color:#ecc94b;'>+12%</b></td>
                <td>+6%</td>
                <td>-</td>
                <td>長時間掛機農怪獲取神裝與楓幣的極品打寶詞條。</td>
            </tr>
        </table>
        """
        tb.setHtml(html)
        return tb

    # ==================== Tab 3: 黃金轉蛋機全獎池 ====================
    def _create_gachapon_tab(self) -> QWidget:
        tb = QTextBrowser()
        tb.setOpenExternalLinks(False)
        tb.setStyleSheet("background-color: #121622; color: #e2e8f0; border: 1px solid #2a3447; border-radius: 6px; padding: 12px; font-size: 12px; line-height: 1.6;")

        html = """
        <h2 style='color: #ffd700; margin-top: 0;'>🎰 楓之谷【黃金轉蛋機】全獎池開箱機率表</h2>
        <p style='color: #cbd5e1;'>消耗金幣：單抽 100,000 金幣 / 十連抽 900,000 金幣 (9折特惠)。每抽必定獲得一項稀有大獎：</p>

        <table border='1' cellspacing='0' cellpadding='6' style='border-color: #2d3748; width: 100%; border-collapse: collapse;'>
            <tr style='background-color: #1a233a; color: #ffd700;'>
                <th style='width: 15%;'>類別與機率</th>
                <th style='width: 35%;'>具體獲得內容</th>
                <th>說明與原版 TMS 特權</th>
            </tr>
            <tr style='background-color: #221a24;'>
                <td><b style='color: #fc8181; font-size: 14px;'>4% 超級大獎</b><br><span style='color:#a0aec0;'>傳奇特等神裝</span></td>
                <td>
                    <b>• 漆黑 Boss 飾品 9 件套：</b><br>
                    巨大恐懼(戒)、苦痛的根源(墜)、狂暴印記(臉)、魔導石眼罩(眼)、指揮官耳環(耳)、夢幻腰帶(腰)、詛咒的魔導書(口袋)、米特拉的憤怒(胸章)、滅世黑心臟(心臟)<br>
                    <b>• 創世神裝：</b>創世真·雙手劍、創世黑魔導書<br>
                    <b>• 永恆神恩防具：</b>永恆冠冕、聖威戰袍、長褲、手套、戰靴、晨曦披風<br>
                    <b>• 起源之塔特殊神戒：</b>規範之戒、持續之戒、武器泡泡之戒
                </td>
                <td>新楓之谷巔峰裝備！自帶傳奇主潛能與最高基礎數值，套裝啟動攻擊力與無視防禦大幅暴增！</td>
            </tr>
            <tr style='background-color: #1f1a2e;'>
                <td><b style='color: #b794f4; font-size: 14px;'>4% 夢幻特賞</b><br><span style='color:#a0aec0;'>月光小寵物 (P寵)</span></td>
                <td>
                    <b>• 月光蒂塔妮亞 (Luna Petite)</b><br>
                    <b>• 月光貝拉 (Luna Petite)</b><br>
                    <b>• 月光皮可 (Luna Petite)</b><br>
                    <i>(附帶各專屬頂級飾品：蒂塔妮亞魔精羽冠、貝拉夜之迷蝶、皮可星辰耳環)</i>
                </td>
                <td><b>全圖黑洞磁力吸寶！</b>單隻提供拾取楓幣與經驗 +10%，集齊三隻出戰啟動【月光祝福】全隊攻擊力 +30、磁吸金幣 +30%！</td>
            </tr>
            <tr style='background-color: #1a2234;'>
                <td><b style='color: #ecc94b; font-size: 14px;'>6% 超絕神選</b><br><span style='color:#a0aec0;'>高階首領萌獸</span></td>
                <td>
                    <b>• 傳說級 (Legendary)：</b>純白聖靈賽蓮、守護者卡羅斯<br>
                    <b>• 罕見級 (Unique)：</b>夢之主露希妲、蜘蛛之王威爾、破滅之翼戴米安、真·希拉
                </td>
                <td>擁有<b>獨立終傷乘區</b>與 BOSS 傷害，高階萌獸可直接出戰發揮威力，亦可吞噬低階萌獸進一步強化！</td>
            </tr>
            <tr>
                <td><b style='color: #ecc94b;'>14% 神級卷軸</b><br><span style='color:#a0aec0;'>艾比卷軸禮盒</span></td>
                <td>
                    <b>• 艾比黑卷B：</b>單次 +12 攻擊力 (台服黑卷神話)<br>
                    <b>• 艾比V卷：</b>單次 +10 攻擊力<br>
                    <b>• 艾比X卷：</b>單次 +8 攻擊力<br>
                    <b>• 艾比R卷：</b>單次 +6 攻擊力<br>
                    <b>• 艾比極電卷：</b>單次 +4 攻擊力<br>
                    <b>• 回真卷軸：</b>清空卷軸強化次數供重新衝卷
                </td>
                <td>直接永久注入已穿戴裝備欄位，提供巨量攻擊力成長。</td>
            </tr>
            <tr>
                <td><b style='color: #9f7aea;'>22% 高級裝備</b><br><span style='color:#a0aec0;'>稀有神裝池</span></td>
                <td>
                    <b>• 黎明套裝：</b>黎明守護天使之戒、黃昏墜飾、暮色印記<br>
                    <b>• 頂級培羅德套裝：</b>頂培戒指、頂培項鍊、頂培腰帶<br>
                    <b>• 法夫納套裝：</b>斬首巨劍、深淵霸王頭盔
                </td>
                <td>自帶罕見 (Unique) 潛能階級與優異套裝效果，中期最強基石。</td>
            </tr>
            <tr>
                <td><b style='color: #4299e1;'>25% 方塊物資</b></td>
                <td>閃耀方塊 x2、閃耀附加方塊 x1、可疑附加方塊 x3、楓方塊 x5、神奇萌獸方塊</td>
                <td>洗練裝備潛能與萌獸詞條之必備素材。</td>
            </tr>
            <tr>
                <td><b style='color: #63b3ed;'>25% 符號碎片</b></td>
                <td>消逝旅途、啾啾島、拉契爾恩、阿爾卡娜、魔菈斯、艾斯佩拉 秘法符號碎片 (3~8 個)</td>
                <td>直接注入提升秘法符號等級，獲得超額攻擊力與全屬性。</td>
            </tr>
        </table>
        """
        tb.setHtml(html)
        return tb

    # ==================== Tab 4: 萌獸與終傷乘區 ====================
    def _create_familiar_tab(self) -> QWidget:
        tb = QTextBrowser()
        tb.setOpenExternalLinks(False)
        tb.setStyleSheet("background-color: #121622; color: #e2e8f0; border: 1px solid #2a3447; border-radius: 6px; padding: 12px; font-size: 12px; line-height: 1.6;")

        html = """
        <h2 style='color: #fc8181; margin-top: 0;'>🐲 萌獸系統：TMS 招牌獨立相乘終傷與培育</h2>
        <p style='color: #cbd5e1;'>新楓之谷台服特有超核心系統！出戰主戰萌獸所提供的<b>最終傷害 (Final Damage)</b> 為最高維度之獨立相乘乘區！</p>

        <div style='background-color: #2d1820; border-left: 4px solid #fc8181; padding: 8px 12px; margin-bottom: 12px;'>
            <b style='color: #feb2b2;'>🔥 什麼是獨立相乘終傷？為什麼雙終、三終如此強大？</b><br>
            一般傷害百分比採相加計算，邊際效應極為嚴重；而萌獸最終傷害採<b>獨立相乘公式</b>：<br>
            <span style='color: #ffd700; font-family: monospace;'>最終傷害總倍率 = (1 + 終傷排1) × (1 + 終傷排2) × (1 + 終傷排3)</span><br>
            • <b>單排 20% 終傷</b>：實戰總傷提升為 <b>1.200 倍 (+20%)</b><br>
            • <b>⭐ 雙終極品 (兩排 20% 終傷)</b>：(1 + 0.20) × (1 + 0.20) = <b>1.440 倍 (+44.0% 實質淨增傷)</b><br>
            • <b>👑 傳奇三終 (三排 20% 終傷)</b>：(1 + 0.20)³ = <b>1.728 倍 (+72.8% 實質翻倍輸出！)</b>
        </div>

        <h3 style='color: #ecc94b;'>📜 萌獸潛能各階級數值表</h3>
        <table border='1' cellspacing='0' cellpadding='6' style='border-color: #2d3748; width: 100%; border-collapse: collapse;'>
            <tr style='background-color: #1a233a; color: #ffd700;'>
                <th>潛能條目</th>
                <th>傳說 (Legendary)</th>
                <th>罕見 (Unique)</th>
                <th>稀有 (Epic)</th>
                <th>特殊 (Rare)</th>
            </tr>
            <tr>
                <td><b>最終傷害增加 (獨立乘區)</b></td>
                <td><b style='color:#68d391;'>+20%</b></td>
                <td><b style='color:#ecc94b;'>+12%</b></td>
                <td>+7%</td>
                <td>+4%</td>
            </tr>
            <tr>
                <td><b>BOSS 怪物傷害增加</b></td>
                <td><b style='color:#68d391;'>+40%</b></td>
                <td><b style='color:#ecc94b;'>+30%</b></td>
                <td>+20%</td>
                <td>+10%</td>
            </tr>
            <tr>
                <td><b>無視目標怪物防禦力</b></td>
                <td><b style='color:#68d391;'>+40%</b></td>
                <td><b style='color:#ecc94b;'>+30%</b></td>
                <td>+20%</td>
                <td>+15%</td>
            </tr>
            <tr>
                <td><b>全隊定時光環回復 HP</b></td>
                <td><b style='color:#68d391;'>每 4 秒回復 15% HP</b></td>
                <td><b style='color:#ecc94b;'>每 4 秒回復 10% HP</b></td>
                <td>每 4 秒回復 8% HP</td>
                <td>每 4 秒回復 5% HP</td>
            </tr>
            <tr>
                <td><b>物理 / 魔法攻擊力 %</b></td>
                <td><b style='color:#68d391;'>+12%</b></td>
                <td><b style='color:#ecc94b;'>+9%</b></td>
                <td>+6%</td>
                <td>+3%</td>
            </tr>
            <tr>
                <td><b>暴擊傷害增加 %</b></td>
                <td><b style='color:#68d391;'>+10%</b></td>
                <td><b style='color:#ecc94b;'>+6%</b></td>
                <td>+4%</td>
                <td>+2%</td>
            </tr>
        </table>

        <h3 style='color: #68d391; margin-top: 18px;'>🍖 萌獸關卡掉落、吞噬升階與一鍵洗潛</h3>
        <ul>
            <li><b>出戰限制</b>：同時間保留 1 隻主戰萌獸出戰生效，召喚新萌獸時會自動收回其他萌獸。</li>
            <li><b>關卡掉落</b>：所有野外冒險地圖中，普通小怪有機率掉落普通萌獸（綠水靈、菇菇寶貝、木妖等）；菁英怪與首領有機率掉落特殊萌獸（巨石人、幼魔精靈、殭屍蘑菇等）。</li>
            <li><b>吞噬升階</b>：點擊萌獸卡片上的 `[🍖 吞噬升階]`，可一鍵吞噬卡冊中未出戰的低階素材，累積 EXP 突破晉升：
                <ul>
                    <li>普通 $\to$ 特殊：需 50 EXP (吞噬普通萌獸 +25 EXP)</li>
                    <li>特殊 $\to$ 罕見：需 120 EXP (吞噬特殊萌獸 +60 EXP)</li>
                    <li>罕見 $\to$ 傳說：需 300 EXP (晉升傳說將解鎖 20% 終傷頂規池！)</li>
                </ul>
            </li>
            <li><b>神奇萌獸方塊一鍵洗潛</b>：在商城購買【神奇萌獸方塊】後，可點擊 `[⚡ 一鍵洗潛]`，支援設定目標（單終、⭐ 雙終極品、👑 傳奇三終、BOSS傷、突破至傳說階級），系統將自動洗練直到達成目標為止！</li>
        </ul>
        """
        tb.setHtml(html)
        return tb

    # ==================== Tab 5: 寵物與月光P寵專題 ====================
    def _create_pet_tab(self) -> QWidget:
        tb = QTextBrowser()
        tb.setOpenExternalLinks(False)
        tb.setStyleSheet("background-color: #121622; color: #e2e8f0; border: 1px solid #2a3447; border-radius: 6px; padding: 12px; font-size: 12px; line-height: 1.6;")

        html = """
        <h2 style='color: #b794f4; margin-top: 0;'>🐾 寵物系統：月光小寵物 (P寵) 與專屬裝備指南</h2>
        <p style='color: #cbd5e1;'>角色最多可同時召喚 3 隻寵物出戰，支援生命警戒線自動喝水、黑洞磁力吸寶與飾品衝卷：</p>

        <table border='1' cellspacing='0' cellpadding='6' style='border-color: #2d3748; width: 100%; border-collapse: collapse;'>
            <tr style='background-color: #1a233a; color: #ffd700;'>
                <th>寵物類型</th>
                <th>代表角色</th>
                <th>獲取途徑</th>
                <th>核心特權能力</th>
            </tr>
            <tr>
                <td><b>一般基本寵物</b></td>
                <td>棕色小狗、小白貓咪、粉紅企鵝、小柴犬、小哈士奇、雪吉拉寶寶</td>
                <td>遊戲初始贈送 3 隻<br>轉蛋屋商城直接金幣購買</td>
                <td>
                    • 自動喝水急救 (跌破 45%~50% HP 時瞬間使用超級藥水回滿)<br>
                    • 可穿戴飾品並衝卷 (基礎飾品攻 +6~+8)
                </td>
            </tr>
            <tr style='background-color: #221a2e;'>
                <td><b style='color: #b794f4;'>月光小寵物 (P寵)<br>(Luna Petite)</b></td>
                <td>
                    <b>• 月光蒂塔妮亞</b><br>
                    <b>• 月光貝拉</b><br>
                    <b>• 月光皮可</b>
                </td>
                <td><b>黃金轉蛋機特等大獎抽取</b></td>
                <td>
                    • <b>全圖黑洞磁力吸寶</b>：單隻拾取楓幣加成 +10%！<br>
                    • <b>【月光祝福】套裝共鳴</b>：三隻 P 寵同場出戰觸發<b>全隊攻擊力 +30、磁吸金幣 +30%！</b><br>
                    • 靈敏急救：跌破 60% HP 立即喝水。
                </td>
            </tr>
        </table>

        <h3 style='color: #ffd700; margin-top: 18px;'>🎀 寵物專屬裝備與飾品衝卷</h3>
        <p style='color: #cbd5e1;'>寵物裝備分為「通用寵物裝備」與「月光P寵專屬神裝」，可在轉蛋屋商店購買或轉蛋獲得：</p>
        <table border='1' cellspacing='0' cellpadding='6' style='border-color: #2d3748; width: 100%; border-collapse: collapse;'>
            <tr style='background-color: #1a233a; color: #ecc94b;'>
                <th>裝備名稱</th>
                <th>適配對象</th>
                <th>基礎攻擊力</th>
                <th>衝卷次數空間</th>
                <th>滿卷後攻擊力預估 (每張卷+3攻)</th>
            </tr>
            <tr style='background-color: #1e1828;'>
                <td><b>✨ 蒂塔妮亞魔精羽冠</b></td>
                <td>月光蒂塔妮亞專屬</td>
                <td><b style='color:#b794f4;'>+25 攻擊力</b></td>
                <td>10 次</td>
                <td><b style='color:#ffd700;'>+55 攻擊力</b></td>
            </tr>
            <tr style='background-color: #1e1828;'>
                <td><b>✨ 貝拉夜之迷蝶</b></td>
                <td>月光貝拉專屬</td>
                <td><b style='color:#b794f4;'>+25 攻擊力</b></td>
                <td>10 次</td>
                <td><b style='color:#ffd700;'>+55 攻擊力</b></td>
            </tr>
            <tr style='background-color: #1e1828;'>
                <td><b>✨ 皮可星辰耳環</b></td>
                <td>月光皮可專屬</td>
                <td><b style='color:#b794f4;'>+25 攻擊力</b></td>
                <td>10 次</td>
                <td><b style='color:#ffd700;'>+55 攻擊力</b></td>
            </tr>
            <tr>
                <td><b>精靈天使之翼</b></td>
                <td>通用所有寵物</td>
                <td>+18 攻擊力</td>
                <td>10 次</td>
                <td>+48 攻擊力</td>
            </tr>
            <tr>
                <td><b>黃金守護鈴鐺</b></td>
                <td>通用所有寵物</td>
                <td>+10 攻擊力</td>
                <td>10 次</td>
                <td>+40 攻擊力</td>
            </tr>
        </table>
        <p style='color: #a0aec0; font-size: 11px;'>※ 使用【寵物飾品攻擊卷軸 100%】每張可為裝備增加 +3 攻擊力，出戰的 3 隻寵物裝備總攻擊力將全額加總注入遠征隊全體角色！</p>
        """
        tb.setHtml(html)
        return tb

