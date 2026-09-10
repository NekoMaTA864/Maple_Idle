"""新楓之谷 反抗軍陣營 (4 職業) 資料模組 (resistance.py)"""
from classes_data.helpers import _s, _c

RESISTANCE_CLASSES = {
    "blaster": _c(
        'blaster', '爆拳槍神', 'resistance', '反抗軍·戰士',
        '重拳擺動 & 燃燒重拳',
        '填裝彈藥火藥，以【重拳擺動】連拳破甲，並釋放【燃燒重拳】毀滅打擊！',
        2.5, 1.3, 1.25, 1.25, 0.12, False,
        [
            _s('magnum_punch', '巨型衝擊', 3.8, dmg=2.95, ico='[拳]', clr=(255, 120, 50), eff='magnum_punch', tag='[破甲重拳]', desc='旋轉巨型鐵拳重轟，造成 295% 破甲大傷害'),
            _s('bunker_buster', '燃燒重拳', 7.0, dmg=3.8, st='stack_burst', lvl=2, ico='[燃]', clr=(255, 70, 30), eff='bunker_buster', tag='[彈藥引爆]', desc='聚能汽缸引爆！消耗全部彈藥造成 380% 毀滅性爆裂重創'),
            _s('double_blast', '雙重重擊', 4.8, dmg=1.35, hc=3, st='multi_hit', lvl=3, ico='[雙]', clr=(255, 160, 60), eff='double_blast', tag='[雙重砲擊]', desc='雙手砲擊 2 連轟鳴，每段造成 135% 穿甲爆裂傷害'),
            _s('hurricane_blaster', '旋風衝擊', 5.5, dmg=0.82, hc=4, st='multi_hit', lvl=4, ico='[風]', clr=(255, 100, 40), eff='hurricane_blaster', tag='[多段 4連]', desc='旋風噴射連續 4 段重拳，每段造成 82% 衝擊傷害'),
            _s('vulcan_punch', '火神衝擊', 8.5, st='team_buff', bt='atk', bv=0.25, bd=8.5, lvl=5, ico='[神]', clr=(255, 200, 70), eff='vulcan_punch', tag='[全隊火藥]', desc='火藥過載運轉！全隊攻擊力提升 25%，持續 8.5 秒'),
            _s('shotgun_punch', '霰彈重拳', 4.0, dmg=3.05, gc=True, ico='[霰]', clr=(255, 90, 40), eff='shotgun_punch_blast', tag='[霰彈破甲]', desc='零距離扣下霰彈擊錘重拳直轟，噴射大量鐵片造成 305% 破壞打擊且必定暴擊'),
            _s('charge_mastery', '彈藥充填', 8.5, st='self_buff', bt='speed', bv=0.25, bd=8.5, lvl=2, ico='[填]', clr=(255, 170, 60), eff='ammo_overdrive_aura', tag='[自身加速]', desc='彈夾冷卻完畢全速上膛！自身攻速提升 25%，持續 8.5 秒'),
            _s('rocket_punch', '火箭鐵拳', 5.2, dmg=0.88, hc=3, st='multi_hit', lvl=3, ico='[箭]', clr=(255, 130, 30), eff='rocket_punch_propel', tag='[多段 3連]', desc='汽缸火箭噴射推進鐵拳進行連環重打，3 段每擊造成 88% 穿透碎骨傷害'),
        ]
    ),
    "wild_hunter": _c(
        'wild_hunter', '狂豹獵人', 'resistance', '反抗軍·弓箭手',
        '狂豹狂襲 & 咆哮',
        '騎乘凶悍美洲豹，【狂豹狂襲】疾速速射，並以【咆哮】鼓舞全體隊員！',
        2.3, 1.05, 1.0, 1.3, 0.15, False,
        [
            _s('wild_arrow_blast', '狂野之箭', 3.5, dmg=0.90, hc=5, st='multi_hit', ico='[箭]', clr=(255, 160, 80), eff='wild_arrow_blast', tag='[多段 5連]', desc='騎乘美洲豹極速連射 5 箭，每箭造成 90% 穿透傷害'),
            _s('jaguar_storm', '狂豹風暴', 6.8, dmg=3.9, lvl=2, ico='[豹]', clr=(255, 120, 50), eff='jaguar_storm', tag='[豹群撕咬]', desc='美洲豹群集結撕咬，造成 390% 猛獸狂襲重創'),
            _s('howling', '咆哮', 8.5, st='team_buff', bt='atk', bv=0.20, bd=8.5, lvl=3, ico='[哮]', clr=(255, 180, 70), eff='howling_aura', tag='[全隊戰吼]', desc='美洲豹戰吼震撼全場，全隊攻擊力提升 20%，持續 8.5 秒'),
            _s('claw_cut', '利爪揮擊', 4.2, dmg=3.1, ign_def=0.25, ico='[爪]', clr=(255, 130, 60), eff='jaguar_claw_slash', tag='[猛獸抓痕]', desc='美洲豹猛躍撲咬揮出巨爪，造成 310% 撕裂傷並無視目標 25% 防禦'),
            _s('sonic_boom', '音爆', 5.6, dmg=1.0, hc=3, st='multi_hit', lvl=4, ico='[音]', clr=(240, 140, 90), eff='sonic_boom', tag='[多段 3連]', desc='音爆利爪 3 段撕扯，每擊造成 100% 破甲流血傷害'),
            _s('jaguar_rider', '猛豹騎乘', 8.0, st='self_buff', bt='speed', bv=0.25, bd=8.5, lvl=5, ico='[騎]', clr=(255, 215, 60), eff='call_of_the_wild', tag='[自身加速]', desc='荒野猛獸騎乘戰鬥姿態，自身攻速提升 25%，持續 8.5 秒'),
            _s('cross_road', '狂暴衝刺', 5.0, dmg=3.2, lvl=2, ico='[衝]', clr=(255, 150, 70), eff='cross_road_charge', tag='[豹嘯衝鋒]', desc='與座騎化身一體直線撞擊目標，造成 320% 破甲大傷害並使怪物僵直倒退'),
            _s('extreme_archery', '野性終結', 9.0, dmg=4.2, lvl=3, ico='[終]', clr=(255, 200, 80), eff='silent_rampage_aura', tag='[個人大招]', desc='野性力量完全爆發！射出凝聚致命野性的毀滅一擊，造成 420% 毀滅大傷害'),
        ]
    ),
    "mechanic": _c(
        'mechanic', '機甲戰神', 'resistance', '反抗軍·海盜',
        '巨型雷射砲 & 重裝加特林',
        '駕駛重型人型機甲，發射【巨型雷射砲】與【重裝加特林】無情掃射！',
        2.6, 1.3, 1.3, 1.2, 0.1, True,
        [
            _s('full_metal_jacket', '重裝機槍', 3.6, dmg=3.12, hc=4, st='multi_hit', ico='[槍]', clr=(100, 200, 255), eff='full_metal_jacket', tag='[多段 4連]', desc='重型機槍 4 連狂轟掃射，合計造成 312% 貫穿傷害'),
            _s('laser_blast', '巨型雷射砲', 6.8, dmg=3.5, st='aoe_beam', aoe=True, lvl=2, ico='[光]', clr=(60, 160, 255), eff='laser_blast', tag='[核能光束]', desc='凝聚超載核能雷射光束，造成 350% 貫穿毀滅打擊'),
            _s('support_gate', '開放傳送門', 9.0, st='shield', sh=75, team_sh=True, lvl=3, ico='[門]', clr=(120, 230, 255), eff='support_gate', tag='[全隊護盾]', desc='展開重力防護力場，為全隊隊員各附加 75 點吸收護盾'),
            _s('ap_salvo_plus', '火箭齊射', 5.2, dmg=3.60, hc=4, st='multi_hit', lvl=4, ico='[彈]', clr=(255, 140, 60), eff='ap_salvo_plus', tag='[多段 4連]', desc='發射多重導彈群，連續 4 次追蹤轟擊，合計造成 360% 爆破傷'),
            _s('robot_launcher', '機械發射器', 8.5, st='team_buff', bt='atk', bv=0.2, bd=8.5, lvl=5, ico='[器]', clr=(160, 220, 255), eff='robot_launcher', tag='[無人機隊]', desc='部署微型戰鬥無人機隊，全隊攻擊力提升 20%，持續 8.5 秒'),
            _s('homing_beacon', '追蹤導彈', 4.0, dmg=3.28, hc=4, st='multi_hit', ico='[尋]', clr=(255, 120, 50), eff='homing_beacon_cluster', tag='[多段 4連]', desc='背部飛彈艙齊射 4 枚高敏度微型巡弋飛彈，合計造成 328% 穿甲追蹤爆炸傷害'),
            _s('war_machine', '金屬機甲：坦克', 8.5, st='self_buff', bt='def', bv=0.3, bd=8.5, lvl=2, ico='[坦]', clr=(110, 210, 255), eff='tank_mode_aura', tag='[自身重甲]', desc='機甲變形重裝坦克型態！自身防禦大幅提升 30%，持續 8.5 秒'),
            _s('distortion_bomb', '重力扭曲彈', 6.2, dmg=3.35, lvl=3, ico='[引]', clr=(130, 100, 255), eff='distortion_bomb_singularity', tag='[黑洞爆縮]', desc='射出重力特異點壓縮炸彈，引發小型黑洞坍塌爆縮造成 335% 高重力貫穿傷'),
        ]
    ),
    "battle_mage": _c(
        'battle_mage', '煉獄巫師', 'resistance', '反抗軍·法師',
        '聯盟光環 & 鬥王死神',
        '近戰法師霸主，張開【聯盟光環】融合全體增益，引爆【暗黑世紀】與【鬥王杖擊】！',
        2.5, 1.25, 1.15, 1.25, 0.12, False,
        [
            _s('finishing_blow', '終極攻擊', 3.8, dmg=0.74, hc=4, st='multi_hit', ico='[擊]', clr=(180, 70, 240), eff='finishing_blow_scythe', tag='[多段 4連]', desc='手持長杖高速重劈撕裂，引動死神鬼爪造成 4 段每段 74% 幽冥切割傷害'),
            _s('battle_king_bar', '鬥王杖擊', 5.5, dmg=2.8, lvl=2, ico='[杖]', clr=(255, 190, 50), eff='battle_king_bar_smash', tag='[超技破地]', desc='長杖延伸為巨型黑金鬥王神兵，極速破空橫掃後怒劈地面，造成 280% 霸王重創'),
            _s('dark_genesis', '暗黑世紀', 6.2, dmg=3.0, st='aoe_beam', aoe=True, bd=1.5, lvl=3, ico='[世]', clr=(210, 90, 255), eff='dark_genesis_thunder', tag='[全屏神罰]', desc='引動暗黑神罰！死靈黑電自天空狂轟而下，造成 300% 毀滅性電漿傷害並極凍控場 1.5 秒'),
            _s('altar_of_annihilation', '暗黑祭壇', 5.0, dmg=2.7, lvl=4, ico='[壇]', clr=(190, 60, 240), eff='altar_annihilation_hex', tag='[祭壇雷網]', desc='在目標身側立起多座暗黑祭壇，祭壇間射出高頻高壓激光鏈索，造成 270% 持續撕裂傷害'),
            _s('union_aura', '聯盟光環', 8.5, st='team_buff', bt='union', bv=0.25, bd=8.5, lvl=5, ico='[聯]', clr=(220, 80, 255), eff='union_aura_halo', tag='[終極光環]', desc='展開終極聯盟光環！融合攻擊、加速、守護與吸血四大光環，全隊攻擊+25%、攻速+25% 並賦予傷害吸血 15%，持續 8.5 秒'),
            _s('grim_reaper', '死神召喚', 6.8, dmg=3.15, gc=True, lvl=2, ico='[死]', clr=(150, 40, 210), eff='grim_reaper_slash', tag='[必暴斬首]', desc='召喚太古死神真身凌空具現，揮舞雙刃奪魂巨鐮斜向橫斬首級，造成 315% 死神重創且必定暴擊'),
            _s('abyssal_lightning', '深淵雷電', 4.8, dmg=0.83, hc=3, st='multi_hit', lvl=3, ico='[雷]', clr=(130, 60, 255), eff='abyssal_lightning_storm', tag='[多段 3連]', desc='撕開深淵冥府裂縫！暴走黑雷在虛空中瘋狂撕裂閃爍，造成 3 段每段 83% 高頻穿透雷暴'),
            _s('death_contract', '死神庇護', 9.0, st='shield', sh=90, team_sh=True, lvl=4, ico='[護]', clr=(160, 100, 255), eff='death_contract_shield', tag='[全隊護盾]', desc='死神黑翼包覆守護！為遠征隊全員各自賦予 90 點吸收護盾，持續 8 秒'),
        ]
    ),
}
