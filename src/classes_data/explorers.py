"""新楓之谷 冒險家陣營 (15 職業) 資料模組 (explorers.py)"""
from classes_data.helpers import _s, _c

EXPLORER_CLASSES = {
    "hero": _c(
        'hero', '英雄', 'explorer', '戰士',
        '鬥氣集中 & 空間斬',
        '蓄積鬥氣球，引爆鬥氣施展【空間斬】撕裂次元對敵方造成毀滅性重創！',
        2.6, 1.25, 1.2, 1.2, 0.1, False,
        [
            _s('raging_blow', '無雙劍舞', 3.8, dmg=2.8, ign_def=0.20, ico='[舞]', clr=(255, 70, 40), eff='x_cross_slash', tag='[破甲爆發]', desc='鬥氣引爆無雙狂斬！雙刃交叉撕裂造成 280% 狂怒交叉裂痕傷害並無視目標 20% 防禦'),
            _s('combo_deathfault', '空間斬', 7.0, dmg=3.8, st='stack_burst', ign_def=0.30, lvl=2, ico='[空]', clr=(255, 40, 40), eff='dimension_rift', tag='[次元爆發]', desc='5轉超技！撕裂次元斬裂全螢幕，造成 380% 毀滅性重創並無視目標 30% 防禦'),
            _s('final_attack', '終極攻擊', 4.8, dmg=1.8, gc=True, lvl=3, ico='[擊]', eff='vertical_cleave', tag='[必暴追擊]', desc='蓄力重刃垂直怒劈貫頂，造成 180% 破甲傷害且必定暴擊'),
            _s('burning_soul_blade', '無雙劍舞連段', 5.5, dmg=0.95, hc=3, st='multi_hit', lvl=4, ico='[巨]', clr=(255, 140, 20), eff='soul_blade', tag='[多段 3連]', desc='召喚燃燒靈魂巨劍從天刺入地面自轉，連續 3 次衝擊，每段 95% 傷害'),
            _s('combo_instinct', '鬥氣本能', 8.5, st='team_buff', bt='atk', bv=0.25, bd=8.0, lvl=5, ico='[能]', clr=(80, 180, 255), eff='combo_orbs', tag='[全隊攻擊]', desc='周身召喚 8 顆旋轉鬥氣球！全隊攻擊傷害提升 25%，持續 8 秒'),
            _s('rising_rage', '怒濤斬', 6.0, dmg=3.0, lvl=2, ico='[怒]', clr=(255, 180, 50), eff='valhalla_aura', tag='[怒濤斬殺]', desc='狂怒斬擊地面！造成 300% 傷害，目標血量低於 35% 時傷害提升 40%', exec_b=0.40),
            _s('beam_blade', '劍氣斬', 4.2, dmg=0.85, hc=3, st='multi_hit', lvl=2, ico='[氣]', clr=(255, 110, 60), eff='beam_blade_slash', tag='[多段 3連]', desc='揮舞鬥氣巨刃向前激射三道半月形熾熱劍氣，每段造成 85% 穿透傷害'),
            _s('combo_fury', '鬥氣衝擊', 5.0, dmg=2.6, ign_def=0.20, lvl=3, ico='[衝]', clr=(240, 60, 40), eff='combo_fury_smash', tag='[鬥氣猛擊]', desc='引爆鬥氣鏈索猛烈向下重轟地面，激盪衝擊震碎地面造成 260% 重創並無視目標 20% 防禦'),
        ]
    ),
    "dark_knight": _c(
        'dark_knight', '黑騎士', 'explorer', '戰士',
        '神聖之火 & 永恆死槍',
        '高額生命與吸血能力，自帶瀕死契約無敵護盾與【永恆之槍】！',
        2.8, 1.45, 1.25, 1.1, 0.05, True,
        [
            _s('dark_impale', '暗黑穿刺', 4.0, dmg=2.3, ls=0.35, ico='[刺]', clr=(180, 80, 240), eff='dark_dragon_thrust', tag='[吸血長槍]', desc='長槍貫穿，造成 230% 傷害並恢復 35% 傷害值生命'),
            _s('gungnir_descent', '滅世永恆之槍', 6.8, dmg=3.4, ls=0.30, lvl=2, ico='[槍]', clr=(160, 60, 220), eff='gungnir_spear', tag='[死神巨槍]', desc='召喚死神巨矛從天貫刺，造成 340% 巨額貫穿傷害並吸血 30%'),
            _s('beholder', '召喚魔眼', 8.0, st='team_buff', bt='atk', bv=0.2, bd=8.0, lvl=3, ico='[眼]', clr=(140, 100, 255), eff='beholder_eye', tag='[全隊攻擊]', desc='召喚魔眼，使全隊攻擊力提升 20%，持續 8 秒'),
            _s('spear_of_darkness', '黑暗之矛', 5.6, dmg=3.80, hc=4, st='multi_hit', ls=0.15, lvl=4, ico='[矛]', clr=(160, 70, 230), eff='spear_forest', tag='[多段 4連]', desc='投擲暗黑之矛撕裂空間，連續貫穿 4 次，合計造成 380% 穿透傷害並吸血 15%'),
            _s('reincarnation', '轉生', 9.5, st='shield', sh=200, lvl=5, ico='[生]', clr=(100, 160, 255), eff='reincarnation_wings', tag='[自身護盾]', desc='瀕死轉生契約護體，為自身附加 200 點吸收護盾'),
            _s('sacrifice', '犧牲', 9.0, dmg=4.0, ls=0.40, lvl=2, ico='[祭]', clr=(150, 90, 255), eff='hyper_body_aura', tag='[重創吸血]', desc='點燃魔眼靈魂獻祭！全力重刺造成 400% 暴怒傷害並吸血 40%'),
            _s('beholder_impact', '魔眼衝擊', 4.5, dmg=2.8, ls=0.20, lvl=2, ico='[衝]', clr=(130, 80, 250), eff='beholder_laser', tag='[魔眼光束]', desc='魔眼瞳孔蓄力激射毀滅黑光射線，貫穿敵人造成 280% 黑暗傷害並吸血 20%'),
            _s('cyclone_spear', '槍刺旋風', 5.2, dmg=3.40, hc=4, st='multi_hit', ls=0.15, lvl=3, ico='[旋]', clr=(190, 70, 240), eff='cyclone_spear_spin', tag='[多段 4連]', desc='揮動長槍極速迴旋刮起暗黑龍捲風，造成 4 段合計 340% 撕裂絞殺傷害並吸血 15%'),
        ]
    ),
    "paladin": _c(
        'paladin', '聖騎士', 'explorer', '戰士',
        '元素衝擊 & 聖域神罰',
        '極致防禦與神聖壁壘，召喚【聖域】神罰轟炸敵方並吸引仇恨！',
        2.9, 1.4, 1.45, 1.05, 0.05, True,
        [
            _s('sanctuary', '聖域', 5.0, dmg=2.6, st='aoe_beam', aoe=True, ico='[域]', clr=(255, 230, 80), eff='sanctuary_hammer', tag='[神聖天罰]', desc='引動聖域巨鎚神罰，造成 260% 全體神聖破壞打擊並嘲諷敵方'),
            _s('grand_cross', '十字聖盾', 11.0, st='shield', sh=70, team_sh=True, lvl=2, ico='[盾]', clr=(255, 215, 120), eff='grand_cross', tag='[全隊護盾]', desc='神聖壁壘降臨！為遠征隊全員各自附加 70 點吸收護盾'),
            _s('blast', '連環環擊', 3.8, dmg=2.2, ign_def=0.25, ico='[擊]', clr=(120, 220, 255), eff='elemental_blast', tag='[元素破防]', desc='四屬性衝擊，造成 220% 元素穿透傷害並無視目標 25% 防禦'),
            _s('smite', '壓制術', 6.8, dmg=2.1, st='freeze', bd=2.2, lvl=4, ico='[封]', clr=(240, 210, 90), eff='smite_cross', tag='[十字極凍]', desc='投下降魔十字架封印，造成 210% 傷害並凍結敵方行動 2.2 秒'),
            _s('divine_echo', '神聖結合', 8.5, st='team_buff', bt='def', bv=0.3, bd=8.5, lvl=5, ico='[合]', clr=(255, 240, 160), eff='divine_echo', tag='[全隊守護]', desc='聖光洗禮戰場，全體隊員防禦力提升 30%，持續 8.5 秒'),
            _s('mighty_mjolnir', '雷神之鎚', 5.2, dmg=2.9, lvl=2, ico='[鎚]', clr=(255, 200, 50), eff='mjolnir_throw', tag='[天神飛鎚]', desc='擲出召喚之雷神巨鎚旋轉轟擊目標，造成 290% 爆發神聖雷傷'),
            _s('divine_charge', '神聖衝擊', 4.0, dmg=0.88, hc=3, st='multi_hit', lvl=3, ico='[衝]', clr=(255, 245, 140), eff='divine_charge_slash', tag='[多段 3連]', desc='將光芒元素注入雙手劍，施展神聖三連衝擊，每擊造成 88% 破甲聖焰打擊'),
            _s('bahamut_judgment', '神罰重擊', 6.0, dmg=3.0, lvl=4, ico='[罰]', clr=(130, 230, 255), eff='elemental_force_aura', tag='[神聖天譴]', desc='召喚太古神威重擊目標，轟碎護甲造成 300% 神聖重創'),
        ]
    ),
    "bowmaster": _c(
        'bowmaster', '箭神', 'explorer', '弓箭手',
        '暴風神射 & 會心之眼',
        '以超高射速聞名的箭神，【暴風神射】傾瀉如暴雨般的箭雨！',
        2.4, 0.95, 0.9, 1.30, 0.15, False,
        [
            _s('hurricane', '暴風神射', 3.4, dmg=4.32, hc=6, st='multi_hit', ico='[風]', clr=(100, 240, 160), eff='hurricane_barrage', tag='[多段 6連]', desc='引導暴風連續暴射 6 箭，每箭 72% 傷害（合計 432%），暴擊率額外 +15%'),
            _s('sharp_eyes', '會心之眼', 8.5, st='team_buff', bt='crit', bv=0.25, bd=8.5, lvl=2, ico='[眼]', clr=(255, 225, 75), eff='sharp_eyes', tag='[全隊暴擊]', desc='全隊開啟會心之眼！全員暴擊率+25% 且暴擊傷害大幅提升，持續 8.5 秒'),
            _s('arrow_stream', '箭流席捲', 6.0, dmg=3.0, st='aoe_beam', aoe=True, lvl=3, ico='[雨]', clr=(80, 220, 200), eff='arrow_stream', tag='[全屏箭流]', desc='大範圍強弓勁射，造成 300% 全場箭流席捲傷害'),
            _s('inhuman_speed', '幻影連矢', 4.6, dmg=3.60, hc=4, st='multi_hit', lvl=4, ico='[幻]', clr=(90, 200, 255), eff='inhuman_speed', tag='[多段 4連]', desc='殘影超速連續速射 4 箭，合計造成 360% 穿甲追擊傷害'),
            _s('phoenix', '火鳳凰', 6.0, dmg=2.6, lvl=5, ico='[鳳]', clr=(255, 120, 50), eff='phoenix_strike', tag='[鳳凰烈焰]', desc='召喚火鳳凰狂襲，造成 260% 烈炎傷害並附加高熱灼燒', dot='burn'),
            _s('armor_piercing', '終極一箭', 4.2, dmg=2.9, ign_def=0.25, ico='[貫]', clr=(120, 255, 180), eff='advanced_final_arrow', tag='[終極貫穿]', desc='神射奧義追擊！強弓射出蓄力巨矢，造成 290% 穿甲傷害並無視目標 25% 防禦'),
            _s('quiver_cartridge', '魔幻箭筒', 8.0, st='team_buff', bt='speed', bv=0.20, bd=8.0, lvl=2, ico='[筒]', clr=(255, 180, 80), eff='quiver_cartridge_aura', tag='[全隊神速]', desc='裝填特殊箭矢彈藥！全隊攻擊速度提升 20%，持續 8 秒'),
            _s('arrow_platter', '狂暴箭雨', 5.0, dmg=3.12, hc=4, st='multi_hit', aoe=False, lvl=3, ico='[狂]', clr=(140, 230, 160), eff='arrow_platter_turret', tag='[多段 4連]', desc='架設箭座單體集中傾瀉 4 段箭羽，合計造成 312% 密集暴雨撕裂傷害'),
        ]
    ),
    "marksman": _c(
        'marksman', '神射手', 'explorer', '弓箭手',
        '必殺狙擊 & 連弩速射',
        '超遠距離一擊必殺，【必殺狙擊】造成極致破甲暴擊大傷害！',
        2.3, 0.95, 0.95, 1.45, 0.22, False,
        [
            _s('snipe', '必殺狙擊', 4.5, dmg=5.5, gc=True, ign_def=0.35, exec_b=0.40, ico='[狙]', clr=(240, 100, 80), eff='sniper_laser', tag='[必殺狙擊]', desc='鎖定致命弱點狙擊，造成 550% 破甲大傷害、必定暴擊且無視目標 35% 防禦，對殘血敵人增傷 40%'),
            _s('split_arrow', '分裂箭弩', 4.5, dmg=1.15, hc=5, st='multi_hit', aoe=True, lvl=2, ico='[裂]', clr=(255, 160, 60), eff='split_arrow', tag='[多段 5連]', desc='重弩分裂彈道激射全屏，連續 5 段箭矢轟鳴，每段造成 115% 穿甲傷害'),
            _s('piercing_arrow', '貫穿射擊', 3.5, dmg=3.2, ign_def=0.25, aoe=True, lvl=3, ico='[穿]', clr=(255, 200, 80), eff='piercing_arrow', tag='[貫通破防]', desc='強穿勁弩貫通全場，造成 320% 貫通傷害並無視目標 25% 防禦'),
            _s('pain_amplification', '破綻標記', 4.2, dmg=2.8, lvl=4, ico='[痛]', clr=(255, 120, 120), eff='pain_focus', tag='[痛擊標記]', desc='標記目標弱點破綻，造成 280% 破甲貫穿傷害'),
            _s('repeater', '巨弩衝擊', 5.5, dmg=3.8, lvl=5, ico='[弩]', clr=(200, 140, 255), eff='repeater_cross', tag='[巨弩擊退]', desc='巨型重弩近距轟擊，造成 380% 衝擊傷害並使敵方行動條倒退'),
            _s('charged_arrow', '蓄力一擊', 3.8, dmg=3.8, gc=True, ign_def=0.25, ico='[蓄]', clr=(255, 140, 50), eff='charged_arrow_blast', tag='[蓄力爆裂]', desc='將氣旋完全凝縮於弩矢，爆射造成 380% 重型貫穿打擊、必定暴擊且無視目標 25% 防禦'),
            _s('bullseye', '精準瞄準', 8.5, st='team_buff', bt='crit', bv=0.25, bd=8.5, lvl=2, ico='[準]', eff='bullseye_aura', tag='[全隊瞄準]', desc='開啟精密狙擊準心！全隊暴擊率+25%，持續 8.5 秒'),
            _s('freezer', '極凍冰箭', 5.5, dmg=2.6, st='freeze', bd=2.5, lvl=3, ico='[凍]', clr=(120, 220, 255), eff='freezer_ice_arrow', tag='[極霜凍結]', desc='射出附帶遠古極寒冰晶的重箭，造成 260% 冰傷並凍結怪物 2.5 秒'),
        ]
    ),
    "pathfinder": _c(
        'pathfinder', '開拓者', 'explorer', '弓箭手',
        '主要射擊 & 遺物解放',
        '操縱古代遺物之弓，【遺物解放】引動上古詛咒力量毀滅敵方！',
        2.4, 1.0, 0.95, 1.25, 0.15, False,
        [
            _s('cardinal_burst', '主要射擊', 3.5, dmg=3.65, ico='[主]', clr=(160, 100, 255), eff='cardinal_burst', tag='[古代爆發]', desc='主要爆炸箭，造成 365% 古代暗影爆裂傷害'),
            _s('cardinal_deluge', '狂風分裂', 4.8, dmg=3.60, hc=3, st='multi_hit', lvl=2, ico='[狂]', clr=(100, 200, 255), eff='cardinal_deluge', tag='[多段 3連]', desc='釋放風之箭矢追蹤分裂，3 段合計造成 360% 疾風傷害'),
            _s('relic_unbound', '遺物解放', 7.2, dmg=3.90, st='aoe_beam', aoe=True, lvl=3, ico='[放]', clr=(255, 100, 200), eff='relic_unbound', tag='[遺物解放]', desc='古代遺物全面解放！全螢幕召喚巨型能量水晶，造成 390% 毀滅衝擊'),
            _s('raven_tempest', '冰霜印記', 6.0, dmg=2.0, st='freeze', bd=2.2, lvl=4, ico='[鴉]', clr=(140, 80, 230), eff='raven_tempest', tag='[古代凍結]', desc='黑渡鴉引導古代極寒之力，造成 200% 傷害並凍結敵方 2.2 秒'),
            _s('obsidian_barrier', '黑曜石屏障', 9.0, st='shield', sh=110, team_sh=True, lvl=5, ico='[障]', clr=(180, 140, 255), eff='obsidian_barrier', tag='[全隊護盾]', desc='召喚古代黑曜石護罩，為遠征隊全體隊員各提供 110 點傷害護盾'),
            _s('triple_impact', '三重衝擊', 4.5, dmg=3.75, hc=3, st='multi_hit', ico='[重]', clr=(190, 80, 255), eff='triple_impact_blast', tag='[多段 3連]', desc='飛躍半空向下射出三發古代爆裂矢，引發 3 連爆破合計造成 375% 撕裂傷'),
            _s('ancient_guidance', '古代導引', 8.5, st='team_buff', bt='atk', bv=0.22, bd=8.5, lvl=2, ico='[導]', clr=(255, 140, 220), eff='ancient_guidance_aura', tag='[古代神光]', desc='古代遺物力量充盈共鳴！全隊攻擊力提升 22%，持續 8.5 秒'),
            _s('curse_transition', '咒印破防', 5.2, dmg=3.40, ign_def=0.25, lvl=3, ico='[咒]', clr=(120, 70, 210), eff='curse_transition_mark', tag='[咒印破防]', desc='將古代詛咒刻印轟入目標體內，造成 340% 腐蝕破甲傷害並無視目標 25% 防禦'),
        ]
    ),
    "fire_poison_mage": _c(
        'fire_poison_mage', '火毒大魔導士', 'explorer', '法師',
        '劇毒迷霧 & 劇毒新星',
        '釋放烈炎與致命劇毒，疊加多層腐蝕後以【劇毒新星】一口氣引爆！',
        2.5, 0.9, 0.85, 1.35, 0.1, False,
        [
            _s('poison_mist', '劇毒迷霧', 4.0, dmg=2.2, dot='bleed', bd=4.0, ico='[霧]', clr=(130, 230, 80), eff='poison_mist', tag='[劇毒腐蝕]', desc='散佈劇毒毒霧，造成 220% 傷害並附加持續劇烈腐蝕流血'),
            _s('poison_nova', '劇毒新星', 7.0, dmg=3.6, st='stack_burst', lvl=2, ico='[星]', clr=(100, 255, 120), eff='poison_nova', tag='[毒素引爆]', desc='引爆全場毒性孢子，造成 360% 劇毒新星爆發傷害'),
            _s('meteor_shower', '火焰流星', 6.2, dmg=3.3, st='aoe_beam', aoe=True, lvl=3, ico='[星]', clr=(255, 90, 40), eff='meteor_shower', tag='[流星焚燒]', desc='召喚天外巨大流星砸向戰場，造成 330% 烈炎焚燒全場重創'),
            _s('flame_haze', '炙炎爆破', 5.0, dmg=0.92, hc=3, st='multi_hit', lvl=4, ico='[炙]', clr=(255, 140, 50), eff='flame_haze', tag='[多段 3連]', desc='火焰毒雲雙重衝擊，3 段每段造成 92% 灼熱傷害'),
            _s('mist_eruption', '劇毒爆發', 8.5, st='team_buff', bt='atk', bv=0.20, bd=8.5, ign_def=0.25, lvl=5, ico='[發]', clr=(150, 240, 90), eff='mist_eruption', tag='[全隊毒益]', desc='毒素感染全場，提升全隊攻擊 20% 並無視目標 25% 防禦'),
            _s('paralyze', '致命毒霧', 3.8, dmg=3.0, dot='burn', bd=4.0, ico='[麻]', clr=(110, 240, 70), eff='paralyze_cloud', tag='[麻痺毒雲]', desc='激射高濃度麻痺毒波，重轟敵人造成 300% 劇毒傷害並附加深度灼燒'),
            _s('ifrit_flame', '伊夫利特烈焰', 6.0, dmg=3.2, lvl=2, ico='[魔]', clr=(255, 130, 60), eff='meditation_aura', tag='[精靈烈焰]', desc='喚醒太古火精靈伊夫利特，噴吐爆炎重創目標造成 320% 高熱爆破傷害'),
            _s('megiddo_flame', '米吉多烈焰', 6.5, dmg=3.4, lvl=3, ico='[地]', clr=(255, 50, 20), eff='megiddo_fireball', tag='[地獄火球]', desc='引導地獄深淵藍白超高溫鬼火，直接鎖定目標造成 340% 毀滅性灼燒大爆炸'),
        ]
    ),
    "ice_lightning_mage": _c(
        'ice_lightning_mage', '冰雷大魔導士', 'explorer', '法師',
        '連鎖閃電 & 冰河紀元',
        '極寒冰凍封鎖怪物行動，以狂暴的【連鎖閃電】轟擊全場！',
        2.5, 0.95, 0.9, 1.35, 0.12, False,
        [
            _s('chain_lightning', '連鎖閃電', 3.2, dmg=3.95, ico='[電]', clr=(100, 200, 255), eff='chain_lightning', tag='[雷霆電殛]', desc='激盪奔騰雷電，造成 395% 閃電貫通傷害且暴擊率 +15%'),
            _s('blizzard', '暴風雪', 6.5, dmg=2.6, st='freeze', bd=3.0, aoe=True, lvl=2, ico='[雪]', clr=(150, 230, 255), eff='blizzard_storm', tag='[極寒凍結]', desc='暴風雪極凍戰場！造成 260% 全場冰霜傷害並凍結敵方行動 3.0 秒'),
            _s('ice_age', '冰河紀元', 6.0, dmg=3.60, hc=3, st='multi_hit', lvl=3, ico='[紀]', clr=(180, 240, 255), eff='ice_age', tag='[多段 3連]', desc='極寒冰河覆蓋戰場，冰錐裂隙 3 段連擊，合計造成 360% 穿透傷'),
            _s('lightning_sphere', '閃電球', 7.5, dmg=3.90, lvl=4, ico='[球]', clr=(80, 180, 255), eff='lightning_sphere', tag='[雷球爆破]', desc='聚能巨大雷電球轟鳴，造成 390% 爆發雷殛毀滅傷害'),
            _s('frozen_orb', '冰凍法珠', 8.5, st='team_buff', bt='crit', bv=0.20, bd=8.5, lvl=5, ico='[珠]', clr=(120, 220, 255), eff='frozen_orb', tag='[全隊寒威]', desc='寒冰法珠覆蓋全場，提升全隊技巧/暴擊率 20%，持續 8.5 秒'),
            _s('freezing_breath', '急凍吐息', 4.8, dmg=3.30, st='freeze', bd=3.0, ico='[息]', clr=(160, 230, 255), eff='freezing_breath_cone', tag='[極凍冰息]', desc='召喚極地冰龍吐息噴吐絕對零度冰霧，造成 330% 傷害並將敵方凍結 3.0 秒'),
            _s('ice_nova', '冰霜新星', 6.8, dmg=3.0, st='aoe_beam', aoe=True, lvl=2, ico='[詠]', clr=(100, 220, 255), eff='speed_cast_aura', tag='[全屏冰爆]', desc='引爆全場絕對零度冰霜新星，造成 300% 全場冰晶爆裂傷害'),
            _s('thunder_storm', '雷霆風暴', 4.5, dmg=3.45, hc=3, st='multi_hit', lvl=3, ico='[暴]', clr=(80, 190, 255), eff='thunder_storm_bolts', tag='[多段 3連]', desc='天空凝聚萬道落雷連續 3 次精確雷擊，合計造成 345% 破甲雷殛傷害'),
        ]
    ),
    "bishop": _c(
        'bishop', '主教', 'explorer', '法師',
        '天怒 & 神聖祈禱',
        '遠征隊不可或缺的聖職者，【天怒】神罰全場，【神聖祈禱】強化全隊！',
        2.7, 1.1, 1.05, 1.05, 0.08, False,
        [
            _s('angel_ray', '天使之箭', 3.8, dmg=2.0, ico='[矢]', clr=(255, 240, 120), eff='angel_ray', tag='[神聖天箭]', desc='射出聖潔光矢重創敵人，造成 200% 純淨神聖傷害'),
            _s('holy_symbol', '神聖祈禱', 9.0, st='team_buff', bt='atk', bv=0.20, bd=9.0, lvl=2, ico='[禱]', eff='holy_symbol', tag='[全隊攻擊]', desc='遠征隊核心光環！全體隊員攻擊傷害提升 20%，持續 9 秒'),
            _s('genesis', '天怒', 7.0, dmg=2.8, st='aoe_beam', aoe=True, lvl=3, ico='[怒]', clr=(255, 255, 140), eff='genesis_holy_pillar', tag='[全螢幕天罰]', desc='九天神怒！萬道金色光柱降臨全螢幕，造成 280% 神聖天罰重創'),
            _s('holy_magic_shell', '神聖之盾', 10.5, st='shield', sh=90, team_sh=True, lvl=4, ico='[盾]', clr=(240, 230, 160), eff='holy_magic_shell', tag='[全隊護盾]', desc='神聖守護聖盾降臨！為遠征隊全員各自附加 90 點吸收護盾'),
            _s('peacemaker', '祈禱聖泉', 5.5, dmg=0.75, hc=3, st='multi_hit', lvl=5, ico='[泉]', clr=(255, 230, 100), eff='peacemaker', tag='[多段 3連]', desc='神聖光彈穿梭，3 段每段造成 75% 神聖傷害並淨化全隊'),
            _s('heal', '群體治癒', 7.5, dmg=1.0, st='heal', ico='[治]', clr=(120, 255, 160), eff='holy_heal_wave', tag='[全體治療]', desc='降下大範圍聖光甘霖，為遠征隊全員每人恢復 100% 攻擊力等量生命值'),
            _s('divine_judgment', '神界審判', 4.2, dmg=2.0, lvl=2, ico='[祝]', clr=(255, 230, 80), eff='blessed_harmony_aura', tag='[神界審判]', desc='召喚神界裁決聖芒，自穹頂轟下純白光刃造成 200% 神聖傷害'),
            _s('divine_punishment', '神聖懲罰', 5.0, dmg=2.4, ign_def=0.25, lvl=3, ico='[制]', clr=(255, 245, 170), eff='divine_punish_light', tag='[神威制裁]', desc='呼喚神界審判之矛貫穿敵人，造成 240% 純淨神聖傷害並無視目標 25% 防禦'),
        ]
    ),
    "night_lord": _c(
        'night_lord', '夜使者', 'explorer', '飛俠',
        '四連飛鏢 & 風魔手裏劍',
        '極速飛鏢大師，投擲【四連飛鏢】與【風魔手裏劍】瞬間爆發多段狂轟！',
        2.3, 0.9, 0.85, 1.4, 0.2, False,
        [
            _s('quad_star', '四連殺', 3.5, dmg=0.80, hc=4, st='multi_hit', ico='[殺]', clr=(180, 100, 255), eff='shadow_stars', tag='[多段 4連]', desc='疾速投擲 4 枚暗黑手裏劍，每枚造成 80% 致命暴擊傷害'),
            _s('fuma_shuriken', '風魔手裏劍', 5.2, dmg=3.2, lvl=2, ico='[魔]', clr=(140, 70, 240), eff='fuma_shuriken', tag='[巨鏢撕裂]', desc='召喚巨型風魔手裏劍切裂目標，造成 320% 撕裂穿透傷害'),
            _s('shadow_partner', '影分身', 8.5, st='team_buff', bt='atk', bv=0.20, bd=8.5, lvl=3, ico='[影]', clr=(160, 90, 255), eff='shadow_partner', tag='[全隊暗影]', desc='召喚影分身相隨，全隊攻擊力提升 20%，持續 8.5 秒'),
            _s('showdown', '猛毒標記', 7.5, dmg=3.6, st='stack_burst', lvl=4, ico='[挑]', clr=(200, 120, 255), eff='showdown_talisman', tag='[疊層引爆]', desc='引爆猛毒標記，造成 360% 毀滅性爆發傷害'),
            _s('spread_throw', '散式投擲', 6.5, dmg=0.92, hc=3, st='multi_hit', lvl=5, ico='[散]', clr=(210, 140, 255), eff='spread_throw', tag='[多段 3連]', desc='飛鏢漫射擴散，連續 3 次飛鏢追擊，每鏢 92% 穿甲傷害'),
            _s('dark_serenity', '達克魯之影', 8.5, st='team_buff', bt='crit', bv=0.20, bd=8.5, ico='[達]', clr=(190, 110, 255), eff='dark_serenity_aura', tag='[盜賊心法]', desc='達克魯長老秘傳心法！全隊暴擊率提升 20%，持續 8.5 秒'),
            _s('assassin_mark', '標記引爆', 4.0, dmg=3.0, lvl=2, ico='[標]', clr=(150, 70, 230), eff='assassin_mark_burst', tag='[標記引爆]', desc='以飛鏢在怪物身上刻下刺客秘印，引爆造成 300% 暴烈撕裂重創'),
            _s('death_star', '五星投擲', 5.0, dmg=0.74, hc=5, st='multi_hit', lvl=3, ico='[星]', clr=(170, 80, 250), eff='five_star_barrage', tag='[多段 5連]', desc='雙手瞬間高速甩出 5 枚暗夜金鏢，5 連段每鏢造成 74% 致命打擊'),
        ]
    ),
    "shadower": _c(
        'shadower', '暗影神偷', 'explorer', '飛俠',
        '致命暗殺 & 楓幣炸彈',
        '潛行突襲，以【致命暗殺】撕裂弱點，並引爆【楓幣炸彈】連環轟炸！',
        2.4, 1.0, 0.95, 1.3, 0.18, False,
        [
            _s('assassinate', '致命暗殺', 3.8, dmg=3.0, gc=True, ico='[殺]', clr=(255, 60, 60), eff='assassinate_slash', tag='[必暴暗殺]', desc='暗影背刺，造成 300% 致命弱點傷害且必定暴擊'),
            _s('meso_explosion', '楓幣炸彈', 5.0, dmg=3.3, st='aoe_beam', aoe=True, lvl=2, ico='[幣]', clr=(255, 215, 0), eff='meso_explosion', tag='[金幣爆破]', desc='漫天楓幣灑落全場引爆！造成 330% 金幣連環爆破傷害'),
            _s('smoke_screen', '煙霧彈', 9.0, dmg=1.5, ls=0.15, exec_b=0.45, lvl=3, ico='[煙]', clr=(120, 120, 140), eff='smoke_screen', tag='[煙霧處決]', desc='釋放濃密防護煙霧隱蔽自身，造成 150% 傷害，目標血量低於 35% 時斬殺傷害提升 45% 並吸血 15%'),
            _s('shadow_assault', '暗影瞬步', 4.6, dmg=0.88, hc=3, st='multi_hit', lvl=4, ico='[瞬]', clr=(180, 80, 200), eff='shadow_assault', tag='[多段 3連]', desc='化身暗影連環瞬殺 3 次，每擊造成 88% 穿甲傷'),
            _s('boomerang_step', '死亡標記', 6.0, dmg=2.4, lvl=5, ico='[旋]', clr=(240, 100, 100), eff='boomerang_step', tag='[處決斬殺]', desc='標記致命死穴斬殺！造成 240% 傷害，目標血量低於 35% 時斬殺傷害提升 50%', exec_b=0.50),
            _s('trickblade', '秘傳斬殺', 4.0, dmg=3.4, gc=True, ico='[切]', clr=(255, 80, 80), eff='trickblade_strike', tag='[秘傳斬殺]', desc='配合暗殺印記瞬身欺敵，由陰影中拔刀直刺心臟，造成 340% 必暴重擊且必定暴擊'),
            _s('meso_guard', '迴旋斬', 6.2, dmg=3.6, lvl=2, ico='[護]', clr=(255, 200, 50), eff='meso_guard_aura', tag='[雙刃迴旋]', desc='揮動淬毒雙刃高速迴旋切割，造成 360% 穿透撕裂傷害'),
            _s('savage_blow', '六連斬', 5.2, dmg=3.48, hc=6, st='multi_hit', lvl=3, ico='[六]', clr=(230, 70, 90), eff='savage_blow_six', tag='[多段 6連]', desc='神速狂匕殘影連續 6 段狂刺，合計造成 348% 撕裂破甲傷害'),
        ]
    ),
    "dual_blade": _c(
        'dual_blade', '影武者', 'explorer', '飛俠',
        '幽靈一擊 & 阿修羅',
        '雙刀流奧義，化身狂暴【阿修羅】劍氣龍捲多段無情絞殺！',
        2.3, 0.95, 0.9, 1.35, 0.22, False,
        [
            _s('phantom_blow', '幽靈一擊', 3.6, dmg=4.00, hc=4, st='multi_hit', ico='[幽]', clr=(255, 90, 90), eff='phantom_blow', tag='[多段 4連]', desc='神速幽靈 4 連刺擊，合計造成 400% 破甲暴擊傷害'),
            _s('asura_anger', '阿修羅', 8.0, dmg=4.25, hc=5, st='aoe_beam', aoe=True, lvl=2, ico='[羅]', clr=(220, 30, 30), eff='asura_tempest', tag='[多段 5連]', desc='化身修羅旋風全場狂掃！5 段劍氣無敵絞殺，合計造成 425% 狂暴貫穿傷害'),
            _s('blade_fury', '狂刃風暴', 4.8, dmg=3.85, lvl=3, ico='[狂]', clr=(255, 120, 80), eff='blade_fury', tag='[劍氣風暴]', desc='雙刃高速旋轉掀起劍氣暴風，造成 385% 刀光斬擊'),
            _s('final_cut', '絕殺刃', 8.5, st='team_buff', bt='atk', bv=0.20, bd=8.5, lvl=4, ico='[絕]', eff='final_cut', tag='[全隊狂暴]', desc='蓄力雙刀十字重斬，全隊傷害提升 20%，持續 8.5 秒'),
            _s('blade_storm', '暴風之刃', 6.0, dmg=3.1, lvl=5, ico='[暴]', clr=(255, 70, 70), eff='blade_storm', tag='[終極重斬]', desc='終極神速重斬，造成 310% 毀滅性重創並擊退目標行動'),
            _s('blade_tornado', '利刃旋風', 5.0, dmg=4.14, hc=3, st='multi_hit', ico='[旋]', clr=(255, 60, 40), eff='blade_tornado_spin', tag='[多段 3連]', desc='旋轉釋放兩股狂暴的黑紅雙刀劍氣龍捲風，前進撕扯造成 3 段合計 414% 穿透重創'),
            _s('haunted_edge', '業火殘影', 4.2, dmg=2.9, gc=True, lvl=2, ico='[業]', clr=(240, 40, 60), eff='haunted_edge_slashes', tag='[業火十字]', desc='召喚修羅怨念附體，雙刀交錯引爆冥府業火，造成 290% 冥府暗影重創且必定暴擊'),
            _s('karma_blade', '死靈附體', 9.0, st='team_buff', bt='speed', bv=0.22, bd=9.0, lvl=3, ico='[魄]', clr=(255, 140, 100), eff='karma_blade_aura', tag='[修羅極速]', desc='喚醒體內太古修羅神力！全隊攻速提升 22%，持續 9 秒'),
        ]
    ),
    "buccaneer": _c(
        'buccaneer', '拳霸', 'explorer', '海盜',
        '能量爆發 & 閃·連殺',
        '蓄積澎湃格鬥能量，引動【海龍突擊】與【閃·連殺】多段狂拳重轟！',
        2.5, 1.2, 1.15, 1.25, 0.12, False,
        [
            _s('octopunch', '閃·連殺', 3.8, dmg=3.60, hc=6, st='multi_hit', ico='[連]', clr=(100, 180, 255), eff='octopunch', tag='[多段 6連]', desc='神速 6 連重拳狂轟！合計造成 360% 重拳衝擊傷害'),
            _s('lord_of_the_deep', '海龍突擊', 6.0, dmg=3.2, lvl=2, ico='[龍]', clr=(60, 140, 255), eff='lord_of_the_deep', tag='[海龍咬碎]', desc='太古海龍盤旋狂暴撕咬，造成 320% 驚濤駭浪爆發傷害'),
            _s('energy_blast', '能量爆發', 7.5, dmg=3.2, st='stack_burst', lvl=3, ico='[能]', clr=(120, 210, 255), eff='energy_blast', tag='[聚能爆破]', desc='釋放體內聚能巨浪衝擊波，造成 320% 破甲大傷害'),
            _s('power_unity', '超人拳', 8.5, st='team_buff', bt='atk', bv=0.22, bd=8.5, lvl=4, ico='[超]', clr=(255, 200, 70), eff='power_unity', tag='[全隊攻擊]', desc='引導格鬥光環激盪，全隊攻擊力提升 22%，持續 8.5 秒'),
            _s('super_transform', '變身', 6.2, dmg=0.90, hc=3, st='multi_hit', lvl=5, ico='[變]', clr=(160, 100, 255), eff='super_transform', tag='[多段 3連]', desc='霸主變身！神速 3 連重踢，每擊造成 90% 穿透重創'),
            _s('serpent_screw', '海龍迴旋', 4.5, dmg=3.60, hc=4, st='multi_hit', ico='[旋]', clr=(70, 160, 255), eff='serpent_screw_wave', tag='[多段 4連]', desc='水之海龍環繞身軀連續衝撞，4 段合計造成 360% 浪濤穿刺傷害'),
            _s('nautilus', '諾特勒斯號神威', 7.0, dmg=3.4, st='aoe_beam', aoe=True, lvl=2, ico='[諾]', clr=(90, 130, 240), eff='nautilus_battleship_strike', tag='[全屏轟炸]', desc='指揮諾特勒斯主力戰艦全場覆蓋轟炸，造成 340% 毀滅重創'),
            _s('time_leap', '生命脈動', 9.0, dmg=1.6, ls=0.18, lvl=3, ico='[時]', clr=(140, 200, 255), eff='time_leap_aura', tag='[格鬥自癒]', desc='激盪體內深海水流生機，造成 160% 傷害並恢復 18% 傷害值生命'),
        ]
    ),
    "corsair": _c(
        'corsair', '槍神', 'explorer', '海盜',
        '迅速射擊 & 全艦開火',
        '率領戰艦水手，以【迅速射擊】連發雙槍，並下達【全艦開火】齊射命令！',
        2.2, 1.0, 0.95, 1.40, 0.18, False,
        [
            _s('rapid_fire', '迅速射擊', 3.2, dmg=1.15, hc=5, st='multi_hit', ico='[速]', clr=(255, 170, 70), eff='rapid_fire', tag='[多段 5連]', desc='雙槍極速連發 5 槍，每發造成 115% 穿透火藥傷害'),
            _s('broadside', '全艦開火', 7.5, dmg=3.8, st='stack_burst', aoe=True, lvl=2, ico='[艦]', clr=(255, 100, 50), eff='broadside', tag='[全艦齊射]', desc='諾特勒斯主力艦彈藥裝填蓄力巨砲齊射全場，造成 380% 毀滅重創'),
            _s('target_lock', '瞄準', 4.5, dmg=3.2, ign_def=0.35, lvl=3, ico='[瞄]', clr=(255, 215, 80), eff='target_lock', tag='[靶心破防]', desc='紅外線精準瞄準弱點，造成 320% 傷害並無視目標 35% 防禦'),
            _s('death_trigger', '死亡真諦', 5.0, dmg=1.30, hc=4, st='multi_hit', lvl=4, ico='[死]', clr=(255, 130, 90), eff='death_trigger', tag='[多段 4連]', desc='彈跳穿甲彈連續 4 次反彈射擊，每發造成 130% 破甲傷害'),
            _s('nautilus_strike', '諾特勒斯海盜支援', 8.5, st='team_buff', bt='speed', bv=0.25, bd=8.5, lvl=5, ico='[水]', clr=(100, 200, 255), eff='nautilus_barrage', tag='[全隊鼓舞]', desc='水手特工隊集結，全隊攻速提升 25%，持續 8.5 秒'),
            _s('eight_legs_easton', '章魚砲台', 4.0, dmg=2.8, st='aoe_beam', dot='bleed', aoe=True, ico='[砲]', clr=(255, 120, 60), eff='eight_legs_cannon', tag='[全屏八爪]', desc='召喚巨型機械八爪章魚砲台連續掃射，造成 280% 全場重創並附加持續出血'),
            _s('pirate_flag', '海盜旗幟', 8.5, st='team_buff', bt='atk', bv=0.22, bd=8.5, lvl=2, ico='[旗]', clr=(255, 80, 40), eff='pirate_flag_aura', tag='[海盜戰歌]', desc='將骷髏海盜戰旗插向陣地！全隊攻擊力提升 22%，持續 8.5 秒'),
            _s('bullet_barrage', '狂暴射擊', 4.5, dmg=1.05, hc=5, st='multi_hit', lvl=3, ico='[狂]', clr=(255, 150, 40), eff='bullet_barrage_spit', tag='[多段 5連]', desc='拔出雙手特裝左輪進行彈幕掃射，5 段每發造成 105% 密集火藥重擊'),
        ]
    ),
    "cannoneer": _c(
        'cannoneer', '重砲指揮官', 'explorer', '海盜',
        '加農砲擊 & 巨型火箭彈',
        '手持巨大加農重砲，發射【巨型火箭彈】在戰場引發核爆級巨響！',
        2.3, 1.15, 1.1, 1.45, 0.12, False,
        [
            _s('cannon_barrage', '加農砲連擊', 3.5, dmg=1.45, hc=5, st='multi_hit', ico='[加]', clr=(255, 110, 50), eff='cannon_barrage', tag='[多段 5連]', desc='加農巨砲連續 5 發超重砲彈轟鳴，每發造成 145% 爆破傷害'),
            _s('icbm', '巨型火箭砲', 6.5, dmg=4.5, st='aoe_beam', aoe=True, ign_def=0.30, lvl=2, ico='[核]', clr=(255, 50, 30), eff='icbm_missile', tag='[全屏核彈]', desc='發射核彈級巨型火箭彈，在全場引發 450% 核爆破壞傷害並無視 30% 防禦'),
            _s('cannon_bazooka', '加農砲火箭', 4.2, dmg=3.6, ign_def=0.20, aoe=True, lvl=3, ico='[狂]', clr=(255, 150, 60), eff='cannon_bazooka', tag='[重砲爆轟]', desc='聚能填彈轟出穿甲重砲貫穿全屏，造成 360% 爆轟衝擊傷害並無視 20% 防禦'),
            _s('rolling_rainbow', '滾動彩虹', 5.0, dmg=1.20, hc=4, st='multi_hit', lvl=4, ico='[彩]', clr=(255, 215, 80), eff='rolling_rainbow', tag='[多段 4連]', desc='彩虹巨砲旋轉多段連續重擊，4 段每段 120% 爆裂傷害'),
            _s('monkey_militia', '猴子魔法', 8.5, st='team_buff', bt='atk', bv=0.25, bd=8.5, lvl=5, ico='[猴]', clr=(255, 180, 100), eff='monkey_militia', tag='[猴子魔法]', desc='猴子夥伴施展祝福魔法，全隊攻擊力提升 25%，持續 8.5 秒'),
            _s('poolmaker', '猴子傭兵隊', 4.0, dmg=3.2, hc=2, st='multi_hit', ico='[援]', clr=(255, 130, 40), eff='poolmaker_artillery', tag='[猴子援軍]', desc='呼叫猴子砲手特工隊投射大量高爆砲彈，連續 2 發合計造成 320% 衝擊傷害'),
            _s('pirate_spirit', '海盜精神', 8.5, st='team_buff', bt='crit', bv=0.25, bd=8.5, lvl=2, ico='[氣]', clr=(255, 190, 70), eff='pirate_spirit_aura', tag='[海盜豪氣]', desc='激發無畏加農水手豪情！全隊暴擊率提升 25%，持續 8.5 秒'),
            _s('cannon_overload', '過載填裝', 5.5, dmg=4.2, ign_def=0.25, exec_b=0.45, lvl=3, ico='[載]', clr=(255, 70, 20), eff='cannon_overload_blast', tag='[核能過載]', desc='加農砲汽缸全壓過載！發射熾熱火核重砲彈造成 420% 熔岩巨響傷害、無視目標 25% 防禦，目標血量低於 35% 時增傷 45%'),
        ]
    ),
}
