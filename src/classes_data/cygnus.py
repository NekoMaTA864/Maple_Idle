"""新楓之谷 皇家騎士團陣營 (5 職業) 資料模組 (cygnus.py)"""
from classes_data.helpers import _s, _c

CYGNUS_CLASSES = {
    "dawn_warrior": _c(
        'dawn_warrior', '聖魂劍士', 'cygnus', '騎士團·戰士',
        '日月交替 & 日蝕終結',
        '切換旭日與月光姿態，引導【日月交替】並在【日蝕】降臨時終結敵人！',
        2.5, 1.25, 1.2, 1.25, 0.12, False,
        [
            _s('soluna_slash', '日月交替', 3.8, dmg=3.75, ign_def=0.20, ico='[交]', clr=(255, 180, 60), eff='soluna_slash', tag='[日月裂光]', desc='融合旭日與月光雙姿態斬擊，造成 375% 星曜烈光斬並無視目標 20% 防禦'),
            _s('eclipse', '日蝕', 7.0, dmg=3.8, st='aoe_beam', aoe=True, lvl=2, ico='[蝕]', clr=(255, 90, 50), eff='eclipse_blast', tag='[日蝕神技]', desc='召喚全螢幕日蝕降臨！爆發造成 380% 毀滅貫穿大傷害'),
            _s('solar_slash', '極月舞蹈', 5.2, dmg=4.05, hc=3, st='multi_hit', lvl=3, ico='[舞]', clr=(120, 200, 255), eff='solar_slash', tag='[多段 3連]', desc='極月光弧迴旋 3 段舞斬，合計造成 405% 星光衝擊傷害'),
            _s('styx_crossing', '靈魂裂斬', 6.5, dmg=2.4, st='freeze', bd=2.2, lvl=4, ico='[魂]', clr=(180, 100, 255), eff='styx_crossing', tag='[靈魂極凍]', desc='光魂之劍貫穿大地，造成 240% 傷害並凍結敵方行動 2.2 秒'),
            _s('soluna_time', '日月共鳴', 8.5, st='team_buff', bt='atk', bv=0.20, bd=8.5, lvl=5, ico='[辰]', clr=(255, 200, 70), eff='soluna_time_aura', tag='[日月共鳴]', desc='溝通天界日月軌跡！全隊攻擊力提升 20%，持續 8.5 秒'),
            _s('flaring_soluna', '烈日斬', 4.2, dmg=3.65, ico='[日]', clr=(255, 140, 40), eff='flaring_sun_cleave', tag='[旭日重刃]', desc='凝聚耀眼旭日狂焰垂直重劈，造成 365% 高溫陽炎傷害並撕裂敵方防禦'),
            _s('soul_penetration', '光魂刺擊', 5.0, dmg=3.60, hc=3, st='multi_hit', lvl=2, ico='[刺]', clr=(200, 160, 255), eff='soul_penetrate_thrust', tag='[多段 3連]', desc='召喚光之劍魂連續三次極速突刺，合計造成 360% 穿心靈魂重創'),
            _s('solunar_finale', '日月終焉', 8.5, dmg=4.35, lvl=3, ico='[終]', clr=(255, 90, 50), eff='cosmos_stars', tag='[日月終焉]', desc='日月交融終極爆發！召喚群星宇宙之輝引發大爆炸，造成 435% 毀滅性重創'),
        ]
    ),
    "flame_wizard": _c(
        'flame_wizard', '烈焰巫師', 'cygnus', '騎士團·法師',
        '軌道火球 & 焰火滅世',
        '操縱無窮無盡的【軌道火球】，召喚【焰火滅世】焚盡戰場一切阻礙！',
        2.4, 0.9, 0.85, 1.35, 0.12, False,
        [
            _s('orbital_flame', '軌道火球', 3.4, dmg=2.75, ico='[球]', clr=(255, 100, 40), eff='orbital_flame', tag='[軌道火球]', desc='激射烈焰軌道火球，造成 275% 高溫穿透火炎傷害'),
            _s('cataclysm', '焰火滅世', 7.0, dmg=3.7, st='aoe_beam', aoe=True, lvl=2, ico='[世]', clr=(255, 60, 20), eff='cataclysm', tag='[焰火滅世]', desc='召喚太古烈焰巨獸滅世！全螢幕天火焚燒，造成 370% 毀滅大爆炸'),
            _s('blazing_extinction', '滅絕烈焰', 5.0, dmg=0.9, hc=3, st='multi_hit', lvl=3, ico='[跡]', clr=(255, 130, 50), eff='blazing_extinction', tag='[多段 3連]', desc='熾熱火球盤旋持續燒灼，3 段每段造成 90% 燃燒撕裂傷害'),
            _s('burning_conduit', '燃燒法陣', 8.5, st='team_buff', bt='atk', bv=0.25, bd=8.5, lvl=4, ico='[陣]', clr=(255, 180, 60), eff='burning_conduit', tag='[全隊炎陣]', desc='建立烈焰法術陣地，全隊攻擊力提升 25%，持續 8.5 秒'),
            _s('flame_barrier', '烈焰守護', 9.0, st='shield', sh=80, team_sh=True, lvl=5, ico='[盾]', clr=(255, 140, 70), eff='flame_barrier', tag='[全隊護盾]', desc='燃燒烈火護盾守護，為全隊隊員附加 80 點吸收護盾'),
            _s('dragon_blaze', '炎龍狂怒', 5.5, dmg=3.35, ico='[龍]', clr=(255, 70, 30), eff='dragon_blaze_maw', tag='[火龍焚野]', desc='自火海中喚醒太古火龍之首狂暴撕咬敵人，造成 335% 烈炎燃燒巨創'),
            _s('spirit_of_flame', '火焰精靈之躍', 8.5, st='self_buff', bt='speed', bv=0.25, bd=8.5, lvl=2, ico='[精]', clr=(255, 160, 50), eff='spirit_flame_aura', tag='[自身加速]', desc='引導純淨火靈歡唱！自身法速與攻速提升 25%，持續 8.5 秒'),
            _s('inferno_wave', '地獄火浪', 4.5, dmg=0.88, hc=3, st='multi_hit', lvl=3, ico='[浪]', clr=(255, 110, 30), eff='inferno_wave_crests', tag='[多段 3連]', desc='激起三道滾滾向前推進的地表熔岩炎浪，連續衝擊造成 3 段 88% 穿甲焚傷'),
        ]
    ),
    "wind_archer": _c(
        'wind_archer', '破風使者', 'cygnus', '騎士團·弓箭手',
        '天空之歌 & 狂風席捲',
        '精靈風之祝福，【天空之歌】傾瀉翡翠箭雨，【狂風席捲】召喚狂暴龍捲！',
        2.3, 0.95, 0.9, 1.3, 0.18, False,
        [
            _s('song_of_heaven', '天空之歌', 3.5, dmg=4.20, hc=4, st='multi_hit', ico='[歌]', clr=(100, 240, 180), eff='song_of_heaven', tag='[多段 4連]', desc='引動天空之風吟唱，連射 4 發狂風之箭，合計造成 420% 穿透傷害'),
            _s('howling_gale', '狂風之嘯', 6.8, dmg=4.10, lvl=2, ico='[風]', clr=(80, 220, 160), eff='howling_gale', tag='[風暴龍捲]', desc='召喚巨大風暴龍捲風狂暴席捲，造成 410% 風之破壞傷害'),
            _s('trifling_wind', '妖精之矢', 4.8, dmg=3.45, hc=3, st='multi_hit', lvl=3, ico='[妖]', clr=(140, 255, 200), eff='trifling_wind', tag='[多段 3連]', desc='無數風之妖精化作追蹤光矢，連續 3 擊合計造成 345% 穿甲傷'),
            _s('monsoon', '季風', 6.2, dmg=2.3, st='freeze', bd=1.8, lvl=4, ico='[季]', clr=(120, 230, 220), eff='monsoon', tag='[風暴極凍]', desc='季風風暴席捲戰場，造成 230% 傷害並凍結敵方行動 1.8 秒'),
            _s('wind_blessing', '旋風守護', 8.5, st='team_buff', bt='speed', bv=0.25, bd=8.5, lvl=5, ico='[護]', clr=(160, 255, 190), eff='wind_blessing', tag='[全隊風護]', desc='風之精靈庇護全場，全隊攻速提升 25%'),
            _s('spiral_vortex', '螺旋衝擊', 4.2, dmg=3.85, ico='[旋]', clr=(90, 240, 190), eff='spiral_vortex_lance', tag='[風刃貫通]', desc='強風化作高速自轉的風之螺旋銳矛，射出造成 385% 破甲大重創並擊退目標'),
            _s('albatross', '天空信天翁', 8.5, st='self_buff', bt='atk', bv=0.25, bd=8.5, lvl=2, ico='[翁]', clr=(120, 255, 210), eff='albatross_wings_aura', tag='[自身輸出]', desc='喚醒巨鳥信天翁太古神聖羽翼！自身攻擊力提升 25%，持續 8.5 秒'),
            _s('vortex_sphere', '風暴法球', 5.2, dmg=3.68, hc=4, st='multi_hit', lvl=3, ico='[球]', clr=(150, 245, 180), eff='vortex_sphere_core', tag='[多段 4連]', desc='凝聚高密度的旋轉微型暴風球轟向前方，連續 4 段撕扯合計造成 368% 穿刺傷害'),
        ]
    ),
    "night_walker": _c(
        'night_walker', '暗夜行者', 'cygnus', '騎士團·飛俠',
        '影分身投擲 & 暗影之矛',
        '潛伏於暗夜中的幻影刺客，召喚【影分身】狂擲暗黑之鏢與【暗影之矛】！',
        2.0, 0.9, 0.85, 1.50, 0.25, False,
        [
            _s('quintuple_throw', '五連投擲', 3.5, dmg=0.98, hc=5, st='multi_hit', ign_def=0.20, ico='[投]', clr=(170, 70, 230), eff='quintuple_dark_stars', tag='[多段 5連]', desc='黑暗手裏劍極速連發 5 枚連續破甲狂打，每枚造成 98% 致命傷害並無視 20% 防禦'),
            _s('shadow_spear', '暗影之矛', 6.0, dmg=4.6, ign_def=0.30, lvl=2, ico='[矛]', clr=(130, 60, 220), eff='shadow_spear', tag='[暗影巨矛]', desc='召喚大地暗黑巨矛貫穿敵人，造成 460% 撕裂大重創並無視目標 30% 防禦'),
            _s('shadow_spark', '快速暗影鏢', 4.2, dmg=1.85, hc=3, st='multi_hit', aoe=True, lvl=3, ico='[鏢]', clr=(180, 110, 255), eff='shadow_spark', tag='[多段 3連]', desc='極速暗夜星鏢連續 3 段追擊全屏，每鏢造成 185% 穿透傷害'),
            _s('shadow_bat', '暗影蝙蝠', 4.8, dmg=3.2, ls=0.35, lvl=4, ico='[蝠]', clr=(200, 130, 255), eff='shadow_bat', tag='[群蝠吸血]', desc='群蝠出擊撕咬目標，造成 320% 傷害並自身吸血回復 35%'),
            _s('darkness_ascending', '暗黑昇華', 8.5, dmg=1.5, st='heal', lvl=5, ico='[治]', clr=(150, 100, 255), eff='darkness_ascending', tag='[暗夜復甦]', desc='黑暗力量洗滌生機，為遠征隊全員每人恢復 150% 攻擊力等量生命值'),
            _s('shadow_illusion', '影分身投擲', 3.2, dmg=1.05, hc=6, st='multi_hit', lvl=2, ico='[影]', clr=(160, 90, 240), eff='shadow_illusion', tag='[多段 6連]', desc='影分身三重共鳴投擲，6 段暗影飛鏢狂襲，每鏢 105% 暴擊傷害'),
            _s('shadow_servant', '僕從召喚', 8.5, st='self_buff', bt='crit', bv=0.30, bd=8.5, lvl=3, ico='[僕]', clr=(140, 80, 210), eff='shadow_servant_aura', tag='[自身暴擊]', desc='自影子中喚出死忠僕從！自身暴擊率+30%，持續 8.5 秒'),
            _s('dark_omen', '黑暗預兆', 4.5, dmg=3.80, aoe=True, ign_def=0.25, lvl=4, ico='[兆]', clr=(100, 40, 180), eff='dark_omen_summon', tag='[預兆天罰]', desc='召喚暗黑靈體法陣自地下噴湧黑暗衝擊波席捲全場，造成 380% 穿透重創並削弱目標 25% 防禦'),
        ]
    ),
    "thunder_breaker": _c(
        'thunder_breaker', '閃雷悍將', 'cygnus', '騎士團·海盜',
        '殲滅雷光 & 霹靂海嘯',
        '引動天際落雷與海嘯衝擊，以【殲滅雷光】進行無情連打轟殺！',
        2.4, 1.15, 1.1, 1.3, 0.15, False,
        [
            _s('annihilate', '殲滅', 3.6, dmg=3.60, hc=4, st='multi_hit', ico='[殲]', clr=(120, 210, 255), eff='thunder_shark', tag='[多段 4連]', desc='閃電灌注巨刃破甲 4 連轟擊，合計造成 360% 閃電衝擊傷害'),
            _s('thunderbolt', '霹靂', 6.8, dmg=3.5, st='freeze', bd=2.0, aoe=True, lvl=2, ico='[靂]', clr=(80, 180, 255), eff='thunderbolt', tag='[雷霆驚濤]', desc='九天驚雷劈裂戰場掀起狂濤，造成 350% 驚雷重創並使怪物觸電麻痺凍結 2.0 秒'),
            _s('typhoon', '颱風', 5.0, dmg=3.68, hc=4, st='multi_hit', lvl=3, ico='[風]', clr=(100, 230, 255), eff='typhoon_wave', tag='[多段 4連]', desc='巨浪翻滾連續衝擊 4 次，合計造成 368% 穿甲狂暴傷害'),
            _s('electrify', '疾風雷電', 8.5, st='team_buff', bt='speed', bv=0.25, bd=8.5, lvl=4, ico='[疾]', clr=(170, 235, 255), eff='electrify_surge_aura', tag='[全隊加速]', desc='雷神充能遍布全場！全隊攻速提升 25%，持續 8.5 秒'),
            _s('lightning_cascade', '閃電連鎖', 6.0, dmg=2.95, lvl=5, ico='[連]', clr=(140, 200, 255), eff='lightning_cascade', tag='[電弧重擊]', desc='電弧激盪重轟目標，造成 295% 傷害'),
            _s('shark_sweep', '海鯊突擊', 4.2, dmg=2.85, ico='[鯊]', clr=(90, 190, 255), eff='shark_sweep_charge', tag='[雷鯊巨浪]', desc='凝聚狂暴雷電之狂鯊幻影向前猛衝，造成 285% 穿透電擊並擊碎目標護甲'),
            _s('god_of_the_sea', '雷神降臨', 8.5, st='self_buff', bt='atk', bv=0.25, bd=8.5, lvl=2, ico='[神]', clr=(160, 240, 255), eff='god_of_the_sea', tag='[自身神威]', desc='太古雷神意志降臨，自身攻擊力提升 25%，持續 8.5 秒'),
            _s('tidal_crash', '迴旋狂潮', 5.0, dmg=3.40, hc=4, st='multi_hit', lvl=3, ico='[潮]', clr=(110, 210, 255), eff='tidal_crash_splashes', tag='[多段 4連]', desc='掀起四道巨型帶電海嘯浪頭重轟敵人，合計造成 340% 衝擊破甲重創'),
        ]
    ),
}
