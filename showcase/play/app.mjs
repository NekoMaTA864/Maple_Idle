import {
  AFFIXES, BOSS_ORDER, DEFAULT_ORDER, OFFLINE, PITY, SKILLS, SLOTS, STAGES, STEP,
  affixChoices, finishBattle, newSave, readSave, reforge, reroll, settleOffline, startBattle, stats, tick, upgradeCost,
} from './rules.mjs';
import { createEffects } from './effects.mjs';
import { icon } from './icons.mjs';

const get = id => document.getElementById(id);
const testMode = new URLSearchParams(location.search).get('test') === '1';
const key = 'maple-idle.paladin.v1' + (testMode ? '.test' : '');
const panel = get('panel');
const field = get('field');
const motionPreference = matchMedia('(prefers-reduced-motion: reduce)');
const titles = { character: '角色與欄位強化', bag: '背包與重洗', map: '林地哨站', skills: '技能配置' };
let savedRaw = localStorage.getItem(key);
let save = readSave(savedRaw) ?? newSave(Date.now());
let blocked = false;
let storageWarning = savedRaw && !readSave(savedRaw) ? '原存檔格式無法讀取，保留原始備份，請從新進度開始。' : '';
if (storageWarning) {
  try { localStorage.setItem(key + '.backup', savedRaw); }
  catch { storageWarning = '原存檔無法讀取，且瀏覽器拒絕建立備份。'; }
}
let battle;
let readyAt = 0;
let battleLog = [];
let eventIndex = 0;
const effects = createEffects(field);
let speed = 1;
let activePanel = '';
let bagId;
let lastReport = '林地哨站';
let reportTime = 0;
let offlineReport = null;
let reduced = motionPreference.matches;
let paused = document.hidden;
let heartbeat = Date.now();
let lastFrame = performance.now();
let accumulator = 0;


function setReport(text, time = 0) {
  lastReport = text;
  reportTime = time;
  battleLog.push({ text, time });
  if (battleLog.length > 140) battleLog.shift();
}

function suspendForOtherTab() {
  if (blocked) return;
  blocked = true;
  setReport('另一個分頁已有更新，請重新載入後續玩');
  renderBattle();
  renderPanel();
}

function writable() {
  if (blocked) return false;
  if (localStorage.getItem(key) === savedRaw) return true;
  suspendForOtherTab();
  return false;
}

function checkpoint(now = Date.now()) {
  if (!writable()) return false;
  save.savedAt = Math.max(save.savedAt, now);
  try {
    const raw = JSON.stringify(save);
    localStorage.setItem(key, raw);
    savedRaw = raw;
  } catch {
    storageWarning = '瀏覽器無法儲存進度，請檢查本機儲存空間與設定。';
  }
  heartbeat = now;
  return true;
}

function resume(now = Date.now(), simulatedMinutes = 0) {
  if (!writable()) return;
  const effectiveNow = simulatedMinutes ? save.savedAt + simulatedMinutes * 60_000 : now;
  const result = settleOffline(save, effectiveNow);
  if (simulatedMinutes) save.savedAt = now;
  if (result) {
    offlineReport = result;
    const { minutes, gold, dust, drops } = result;
    setReport(`${simulatedMinutes ? '測試' : ''}離線 ${minutes} 分鐘，金幣 +${gold}、粉塵 +${dust}、掉落 ${drops} 件`);
  }
  checkpoint(now);
}

function queue(stage, mode) {
  if (!writable() || save.running) return;
  save.selected = stage;
  save.running = { stage, mode };
  battle = null;
  readyAt = performance.now();
  effects.clear();
  checkpoint();
  panel.close();
}

function startQueued() {
  battle = startBattle(save, save.running.stage);
  eventIndex = 0;
  effects.clear();
  setReport(`開始挑戰 ${STAGES[battle.stage].name}`);
}

function stop() {
  if (!save.running || !writable()) return;
  save.running = null;
  battle = null;
  effects.clear();
  setReport('已停止戰鬥，可以調整技能與裝備');
  checkpoint();
  renderBattle();
  renderPanel();
}

function endBattle(now) {
  if (!writable()) return;
  const { text } = finishBattle(save, battle);
  const next = save.running;
  setReport(next?.mode === 'boss' ? text + '，首次自動挑戰灰角守衛' : text, battle.time);
  readyAt = now + 1300;
  checkpoint();
  renderPanel();
}

const skillArt = {
  "guard": "<img src=\"./assets/paladin-shield.svg\" alt=\"\" aria-hidden=\"true\">",
  "strike": "<svg viewBox=\"0 0 40 40\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.45\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\">\n            <path d=\"m17 14 6-8 11 8-6 9Z\"/>\n            <path d=\"m20 18-13 15 3 2 13-15\"/>\n            <path d=\"M6 12l5 2M8 6l5 3\"/>\n          </svg>",
  "break": "<svg viewBox=\"0 0 40 40\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.45\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\">\n            <path d=\"M20 5 33 12.5v15L20 35 7 27.5v-15L20 5Z\"/>\n            <path d=\"M13 20h14M20 13v14M15 15l10 10\"/>\n          </svg>",
  "heal": "<svg viewBox=\"0 0 40 40\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.45\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\">\n            <path d=\"m20 6 3.6 10.4L34 20l-10.4 3.6L20 34l-3.6-10.4L6 20l10.4-3.6Z\"/>\n            <path d=\"M11 11l3 3m15-3-3 3m3 15-3-3m-15 3 3-3\"/>\n          </svg>"
};

function shownSkill(id, order, hero) {
  const skill = SKILLS[id];
  const left = hero && !battle.result ? Math.max(0, hero.cooldowns[id] - battle.time) : 0;
  return `<button type="button" class="slot skill" data-skill="${id}" aria-label="${order} ${skill.name}，開啟技能配置">
    <span class="order">${order}</span><span class="slot-icon">${skillArt[id] ?? icon(skill.icon)}</span>
    <strong class="slot-name">${skill.name}</strong><small class="slot-cd">${left > 0 ? '冷卻 ' + Math.ceil(left) + 's' : '就緒'}</small></button>`;
}

function renderBattle() {
  const { selected, running, best, order } = save;
  const stage = STAGES[battle?.stage ?? running?.stage ?? selected];
  const hero = battle?.allies[0];
  const attributes = hero?.attributes ?? stats(save);
  get('gold').textContent = save.gold;
  get('battle-status').textContent = stage.name + (running && battle && !battle.result ? `　${battle.time.toFixed(1)} 秒` : '');
  get('stage-status').textContent = blocked ? '請重新載入' : running?.mode === 'farm' ? '自動刷關' :
    running ? '自動戰鬥中' : best === 4 ? '首王已擊破' : '已通關 ' + Math.min(3, best) + '／3';
  const action = get('action');
  action.disabled = blocked;
  action.textContent = running ? '停止' : selected === 3 ? '挑戰' : selected < best ? '刷關' : '推關';
  get('progress').style.setProperty('--fill', Math.min(3, best) / 3 * 100 + '%');
  get('report-time').textContent = reportTime.toFixed(1) + ' 秒';
  get('report-text').textContent = lastReport;
  get('report-text').title = lastReport;
  get('field-note').hidden = Boolean(save.running || battle);

  const enemies = battle?.enemies ?? stage.enemies.map((name, index) => ({ name, hp: stage.hp, maxHp: stage.hp, boss: stage.boss, id: `enemy-${index}` }));
  const enemyRow = Array.from({ length: 4 }, (_, index) => {
    const enemy = enemies[index];
    if (!enemy) return '<article class="slot vacant" aria-label="空敵槽">—</article>';
    const { id, hp, maxHp, name, boss, impact } = enemy;
    const charging = impact != null;
    const shape = !hp ? 'tombstone' : boss ? 'grayhorn-warden' : name === '林間蝠' ? 'forest-bat' : 'moss-beast';
    return `<article id="${id}" class="slot enemy ${boss ? 'boss' : ''} ${hp ? '' : 'fallen'} ${charging ? 'charging' : ''}">
      <span class="slot-icon"><img src="./assets/${shape}.svg" alt=""></span><strong class="slot-name">${hp ? name : '已擊破'}</strong>
      <span class="slot-hp">HP <b>${hp}</b></span><div class="meter enemy-hp" style="--fill:${hp / maxHp * 100}%" aria-hidden="true"></div>
      <small class="slot-state">${charging ? '重擊蓄力' : hp ? '待機' : '已擊破'}</small></article>`;
  }).join('');
  if (get('enemies').dataset.render !== enemyRow) {
    get('enemies').innerHTML = enemyRow;
    get('enemies').dataset.render = enemyRow;
  }

  const hp = hero?.hp ?? attributes.hp;
  const shield = hero?.shield ?? 0;
  const weapon = save.equipped.weapon ? '哨衛聖鎚' : '見習聖鎚';
  const core = `<article class="slot core" id="hero-core" aria-label="聖騎士武器與護盾核心">
        <div class="core-emblems">
          <img class="emblem-hammer" src="./assets/trainee-hammer.svg" alt="" aria-hidden="true">
          <img class="emblem-shield" id="core-shield-icon" src="./assets/paladin-shield.svg" alt="" aria-hidden="true">
        </div>
        <strong class="slot-name">${weapon}</strong>
        <div class="resources">
          <div class="res-line"><span>生命</span><b id="hero-hp">${hp}</b></div>
          <div class="meter health" id="hero-hpbar" style="--fill:${hp / attributes.hp * 100}%" aria-hidden="true"></div>
          <div class="res-line"><span>護盾</span><b id="hero-shield">${shield}</b></div>
          <div class="meter shield" id="hero-shieldbar" style="--fill:${shield / Math.max(1, Math.round(attributes.hp * .4)) * 100}%" aria-hidden="true"></div>
        </div>
      </article>`;
  const row = order.map((id, index) => shownSkill(id, index + 1, hero));
  row.splice(2, 0, core);
  const allyRow = row.join('');
  const allies = get('allies');
  if (allies.dataset.render !== allyRow) {
    const focused = allies.contains(document.activeElement) ? document.activeElement.dataset.skill : null;
    allies.innerHTML = allyRow;
    allies.dataset.render = allyRow;
    if (focused) allies.querySelector(`[data-skill="${focused}"]`)?.focus({ preventScroll: true });
  }
  effects.refreshCards();
}

const button = (operation, label, value = '', disabled = false, description = '') =>
  `<button type="button" data-op="${operation}" data-value="${value}"${disabled ? ' disabled' : ''}${description ? ` aria-label="${description}"` : ''}>${label}</button>`;
const actions = content => `<div class="sheet-actions">${content}</div>`;
const line = (text, controls = '') => `<div class="sheet-row"><div>${text}</div>${controls}</div>`;
const itemName = item => `哨衛${SLOTS[item.slot]} #${item.id}`;
const affixLabel = ({ key, value }) => `${AFFIXES[key].name} +${value}${AFFIXES[key].unit ?? ''}`;

function characterPanel(locked) {
  const attributes = stats(save);
  return `<p>生命 ${attributes.hp}　攻擊 ${attributes.attack}　每擊固定減傷 ${attributes.reduction}</p>
    <p>強化保留在欄位，更換裝備後仍有效。</p>` +
    Object.entries(SLOTS).map(([slot, label]) => {
      const item = save.bag.find(candidate => candidate.id === save.equipped[slot]);
      const level = save.levels[slot];
      const cost = upgradeCost(level);
      return line(`<strong>${label} +${level}</strong><small>${item ? itemName(item) : '尚未裝備'}</small>`,
        actions(button('upgrade', level >= 5 ? '已滿級' : `強化 · ${cost} 金幣`, slot, locked || level >= 5 || save.gold < cost)));
    }).join('');
}

function skillsPanel(locked) {
  return `<p>冷卻完成即自動施放，同時就緒時由第 1 格起依序處理。停戰後可調整。</p>
    ${actions(button('preset', '刷圖配置', 'farm', locked) + button('preset', '首王配置', 'boss', locked))}
    <h3>施放順序</h3>` + save.order.map((id, index) => {
    const skill = SKILLS[id];
    const excluded = Object.keys(SKILLS).filter(key => !save.order.includes(key));
    const options = [id, ...excluded].map(key => `<option value="${key}">${SKILLS[key].name}</option>`).join('');
    return line(`<strong>${index + 1}　${skill.name} · ${skill.cooldown} 秒</strong><small>${skill.detail}</small>`,
      actions(button('up', '↑', index, locked || index === 0, `將${skill.name}往前移`) +
        button('down', '↓', index, locked || index === 3, `將${skill.name}往後移`) +
        `<select data-swap="${index}" aria-label="更換第 ${index + 1} 格"${locked ? ' disabled' : ''}>${options}</select>`));
  }).join('') + '<h3>未上場</h3>' + Object.keys(SKILLS).filter(id => !save.order.includes(id))
    .map(id => line(`<strong>${SKILLS[id].name} · ${SKILLS[id].cooldown} 秒</strong><small>${SKILLS[id].detail}</small>`)).join('');
}

function bagPanel(locked) {
  const item = save.bag.find(candidate => candidate.id === bagId) ?? save.bag.at(-1);
  if (!item) return '<p>背包是空的。推關或刷關可取得哨衛裝備。</p>';
  bagId = item.id;
  const isEquipped = save.equipped[item.slot] === item.id;
  const lockedKey = item.affixes[item.locked ?? -1]?.key;
  const canRoll = !locked && save.dust > 0;
  return `<p>粉塵 ${save.dust}　指定保底 ${save.pity}／${PITY}</p>
    <p>重洗花 1 粉塵，可鎖 1 條。累積 3 次後，下一次可指定一條相容詞綴。</p>
    <label>裝備 <select id="pick-item">${[...save.bag].reverse().map(entry =>
      `<option value="${entry.id}"${item.id === entry.id ? ' selected' : ''}>${itemName(entry)}${save.equipped[entry.slot] === entry.id ? '（裝備中）' : ''}</option>`).join('')}</select></label>
    <article class="item">
    ${line(`<strong>${itemName(item)}</strong><small>星火 ${['weapon', 'charm'].includes(item.slot) ? '攻擊 +' + item.flame : '生命 +' + item.flame * 5}</small>`,
      actions(button('equip', isEquipped ? '裝備中' : '裝備', item.id, locked || isEquipped) +
        button('salvage', '分解 +2', item.id, locked || isEquipped)))}
    ${item.affixes.map((affix, index) => line(`<span class="affix">${affixLabel(affix)}</span>`,
      actions(button('lock', item.locked === index ? '解鎖' : '鎖定', index, locked, (item.locked === index ? '解鎖' : '鎖定') + AFFIXES[affix.key].name)))).join('')}
    ${line('重洗未鎖詞綴', actions(button('reroll', '重洗 · 1 粉塵', '', !canRoll)))}
    ${line('指定一條', actions(`<select id="target" aria-label="指定詞綴"${!canRoll || save.pity < PITY ? ' disabled' : ''}>${affixChoices(item.slot, lockedKey)
      .map(key => `<option value="${key}">${AFFIXES[key].name}</option>`).join('')}</select>` +
      button('reforge', '指定重洗', '', !canRoll || save.pity < PITY)))}
    </article>`;
}

function mapPanel(locked) {
  const progress = STAGES.map((stage, index) => {
    const status = index < save.best ? '已通關' : index === save.best ? '已解鎖' : '尚未解鎖';
    const op = index === 3 ? 'boss' : index < save.best ? 'farm' : 'push';
    return line(`<strong>${stage.boss ? '首王' : '第 ' + (index + 1) + ' 關'}　${stage.name}</strong><small>${status}</small>`,
      actions(button(op, { boss: '挑戰', farm: '刷關', push: '推關' }[op], index, locked || index > save.best)));
  }).join('');
  const loot = offlineReport ? `<p>上次結算 ${offlineReport.minutes} 分鐘，金幣 +${offlineReport.gold}、粉塵 +${offlineReport.dust}、掉落 ${offlineReport.drops} 件。</p>` : '';
  return `${progress}<h3>離線駐留</h3><p>林地哨站每分鐘 +${OFFLINE.gold} 金幣、+${OFFLINE.dust} 粉塵，每 ${OFFLINE.dropEvery} 分鐘掉 1 件裝備，單次最多結算 ${OFFLINE.minutes} 分鐘。</p>
    ${actions(button('reside', save.resident ? '駐留中 · 停止駐留' : '駐留林地哨站', '', blocked || save.best < 1))}${loot}
    ${testMode ? `<h3>測試時鐘</h3><p>以測試存檔模擬這段離線時間。</p>${actions(button('clock', '快轉 15 分鐘', 15, blocked || !save.resident) + button('clock', '快轉 3 小時', 180, blocked || !save.resident))}` : ''}
    <h3>戰報</h3><ol class="log-list">${[...battleLog].reverse().map(({ text, time }) => `<li><time>${time.toFixed(1)} 秒</time>${text}</li>`).join('')}</ol>`;
}

function renderPanel(message = '') {
  if (!panel.open && !activePanel) return;
  get('notice').textContent = message || storageWarning || (blocked ? '另一個分頁已有更新，請重新載入後續玩。' : '');
  const locked = Boolean(save.running || blocked);
  const body = get('panel-body');
  const rendered = { character: characterPanel, bag: bagPanel, skills: skillsPanel, map: mapPanel }[activePanel]?.(locked) ?? '';
  if (rendered !== body.innerHTML) {
    const previous = document.activeElement;
    const scroll = panel.scrollTop;
    body.innerHTML = rendered;
    panel.scrollTop = scroll;
    if (previous?.id) get(previous.id)?.focus({ preventScroll: true });
    else if (previous?.dataset.op) {
      [...body.querySelectorAll('[data-op]')].find(element => element.dataset.op === previous.dataset.op &&
        element.dataset.value === previous.dataset.value)?.focus({ preventScroll: true });
    }
  }
}

function openPanel(name) {
  if (name === 'battle') return;
  activePanel = name;
  get('panel-title').textContent = titles[name];
  renderPanel();
  if (!panel.open) panel.showModal();
}

panel.addEventListener('close', () => { if (!panel.open) activePanel = ''; });

get('action').addEventListener('click', () => {
  if (save.running) stop();
  else queue(save.selected, save.selected === 3 ? 'boss' : save.selected < save.best ? 'farm' : 'push');
});
get('speed').addEventListener('click', event => {
  speed = speed === 1 ? 4 : 1;
  event.currentTarget.textContent = speed + '×';
  event.currentTarget.setAttribute('aria-pressed', speed === 4);
});
get('tester').textContent = testMode ? '返回正式試玩' : '開啟測試存檔';
get('tester').href = testMode ? './' : './?test=1';
function showMotion() {
  document.body.classList.toggle('reduce', reduced);
  get('motion').setAttribute('aria-pressed', reduced);
}
get('motion').addEventListener('click', () => { reduced = !reduced; showMotion(); });
motionPreference.addEventListener('change', event => { reduced = event.matches; showMotion(); });
showMotion();
get('gray').addEventListener('click', event => {
  event.currentTarget.setAttribute('aria-pressed', document.body.classList.toggle('gray'));
});
document.querySelector('nav').addEventListener('click', event => {
  const name = event.target.closest('[data-panel]')?.dataset.panel;
  if (name) openPanel(name);
});
get('allies').addEventListener('click', event => {
  if (event.target.closest('[data-skill]')) openPanel('skills');
});

get('panel-body').addEventListener('change', event => {
  const input = event.target;
  if (input.id === 'pick-item') {
    bagId = Number(input.value);
    renderPanel();
  }
  if (input.dataset.swap !== undefined && !save.running && writable() && !save.order.includes(input.value)) {
    save.order[Number(input.dataset.swap)] = input.value;
    checkpoint();
    renderBattle();
    renderPanel('已更新技能配置');
    get('panel-body').querySelector(`[data-swap="${input.dataset.swap}"]`)?.focus();
  }
});

get('panel-body').addEventListener('click', event => {
  const action = event.target.closest('[data-op]');
  if (!action || action.disabled || !writable()) return;
  const { op, value } = action.dataset;
  const item = save.bag.find(candidate => candidate.id === bagId);
  const index = Number(value);
  let message = '';
  if (['push', 'farm', 'boss'].includes(op)) {
    queue(index, op);
    return;
  }
  switch (op) {
    case 'reside':
      save.resident = !save.resident;
      message = save.resident ? '已駐留林地哨站' : '已停止離線駐留';
      break;
    case 'clock': resume(Date.now(), index); message = lastReport; break;
    case 'preset':
      save.order = [...(value === 'boss' ? BOSS_ORDER : DEFAULT_ORDER)];
      message = '已套用技能配置';
      break;
    case 'up':
    case 'down': {
      const next = index + (op === 'up' ? -1 : 1);
      [save.order[index], save.order[next]] = [save.order[next], save.order[index]];
      message = '已更新施放順序';
      break;
    }
    case 'equip': save.equipped[item.slot] = item.id; message = `已裝備${itemName(item)}`; break;
    case 'salvage':
      save.bag = save.bag.filter(candidate => candidate !== item);
      save.dust += 2;
      message = '已分解，粉塵 +2';
      break;
    case 'lock':
      item.locked = item.locked === index ? null : index;
      message = item.locked === null ? '已解鎖詞綴' : '已鎖定詞綴';
      break;
    case 'reroll':
      message = reroll(save, item) ? '重洗完成，鎖定的詞綴已保留' : '粉塵不足';
      break;
    case 'reforge':
      message = reforge(save, item, get('target').value) ? '已取得指定詞綴，保底重新累積' : '指定詞綴不可用';
      break;
    case 'upgrade':
      save.gold -= upgradeCost(save.levels[value]);
      save.levels[value] += 1;
      message = `${SLOTS[value]}欄位已強化至 +${save.levels[value]}`;
      break;
  }
  checkpoint();
  renderBattle();
  renderPanel(message);
});

document.addEventListener('visibilitychange', () => {
  if (document.hidden === paused) return;
  paused = document.hidden;
  if (paused) checkpoint();
  else {
    resume();
    lastFrame = performance.now();
    accumulator = 0;
    renderBattle();
    renderPanel();
  }
});
window.addEventListener('pagehide', () => { if (!paused) checkpoint(); });
window.addEventListener('pageshow', event => {
  if (!event.persisted || document.hidden) return;
  resume();
  paused = false;
  lastFrame = performance.now();
  accumulator = 0;
  renderBattle();
  renderPanel();
});
window.addEventListener('storage', event => { if (event.key === key && event.newValue !== savedRaw) suspendForOtherTab(); });

resume();
if (save.running) setReport('已續玩，從上次交戰的關卡開頭繼續');
renderBattle();
setInterval(() => {
  const now = performance.now();
  const delta = Math.min(500, now - lastFrame);
  lastFrame = now;
  if (paused || blocked) return;
  if (Date.now() - heartbeat >= 10_000) checkpoint();
  if (save.running && now >= readyAt) {
    if (!battle || battle.result) {
      startQueued();
      accumulator = 0;
    }
    accumulator += delta / 1000 * speed;
    const beats = [];
    while (accumulator >= STEP && !battle.result) {
      accumulator -= STEP;
      tick(battle);
      const events = battle.events.slice(eventIndex);
      for (const event of events) setReport(event.text, event.time);
      if (events.length) beats.push(events);
      eventIndex = battle.events.length;
    }
    renderBattle();
    for (const beat of beats) {
      effects.play(beat, speed, reduced);
      const interrupt = beat.find(event => event.kind === 'ice');
      if (interrupt) {
        lastReport = interrupt.text;
        reportTime = interrupt.time;
      }
    }
    if (battle.result) endBattle(now);
  }
  renderBattle();
}, 80);
