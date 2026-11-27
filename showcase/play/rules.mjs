export const SLOTS = { weapon: '武器', shield: '盾牌', armor: '鎧甲', charm: '飾品' };
export const SKILLS = {
  strike: { name: '審判重擊', icon: 'hammer', cooldown: 6, detail: '單體 1.9 倍攻擊。持盾時額外增加 0.8 倍。' },
  sweep: { name: '聖光橫掃', icon: 'sanctuary', cooldown: 6, detail: '對每個敵人造成 1.1 倍攻擊。' },
  guard: { name: '盾誓反擊', icon: 'shield', cooldown: 6, detail: '獲得 40% 最大生命的護盾，擋傷時反擊。' },
  orbit: { name: '迴旋聖鎚', icon: 'hammer', cooldown: 9, detail: '接下來 3 秒，每秒對全場造成 0.45 倍攻擊。' },
  heal: { name: '回生禱言', icon: 'star', cooldown: 9, detail: '回復 29% 最大生命。' },
  break: { name: '斷勢聖印', icon: 'seal', cooldown: 6, detail: '單體 0.95 倍攻擊，打斷正在蓄力的重擊。' },
};

export const STAGES = [
  { name: '苔石入口', enemies: ['苔石獸', '林間蝠', '苔石獸'], hp: 50, attack: 8, gold: 18, slot: 'weapon' },
  { name: '暮枝岔路', enemies: ['林間蝠', '苔石獸', '林間蝠'], hp: 74, attack: 12, gold: 24, slot: 'shield' },
  { name: '舊鐘坡', enemies: ['苔石獸', '林間蝠', '苔石獸'], hp: 99, attack: 15, gold: 32, slot: 'armor' },
  { name: '灰角守衛', enemies: ['灰角守衛'], hp: 770, attack: 20, gold: 80, slot: 'charm', boss: true },
];

export const AFFIXES = {
  force: { name: '攻擊', slots: ['weapon', 'charm'], min: 3, max: 6 },
  vitality: { name: '生命', slots: ['shield', 'armor', 'charm'], min: 12, max: 24 },
  ward: { name: '減傷', slots: ['shield', 'armor'], min: 2, max: 4 },
  haste: { name: '盾誓冷卻縮短', slots: ['shield', 'charm'], min: .5, max: 1, step: .5, unit: '秒' },
  expose: { name: '橫掃破防', slots: ['weapon', 'armor', 'charm'], min: 8, max: 16, unit: '%' },
  prayer: { name: '禱言額外回復', slots: ['weapon', 'shield', 'armor', 'charm'], min: 5, max: 10, unit: '%' },
};

export const PITY = 3;
export const OFFLINE = { minutes: 120, gold: 2, dust: 1, dropEvery: 15 };
export const STEP = .25;
export const SAVE_VERSION = 1;
export const DEFAULT_ORDER = ['strike', 'sweep', 'guard', 'orbit'];
export const BOSS_ORDER = ['guard', 'strike', 'break', 'heal'];

const slotKeys = Object.keys(SLOTS);
const integer = (random, min, max) => min + Math.floor(random() * (max - min + 1));

export function newSave(now) {
  return {
    version: SAVE_VERSION, savedAt: now, gold: 0, dust: 0, pity: 0, best: 0,
    firstBoss: false, selected: 0, resident: false, offlineMinutes: 0, nextItem: 1,
    order: [...DEFAULT_ORDER], running: null, bag: [],
    equipped: Object.fromEntries(slotKeys.map(slot => [slot, null])),
    levels: Object.fromEntries(slotKeys.map(slot => [slot, 0])),
  };
}

export function readSave(raw) {
  try {
    const data = JSON.parse(raw);
    if (data?.version !== SAVE_VERSION || !Number.isFinite(data.savedAt) ||
        !Array.isArray(data.bag) || !Array.isArray(data.order) || data.order.length !== 4 ||
        new Set(data.order).size !== 4 || !data.order.every(id => Object.hasOwn(SKILLS, id)) ||
        !slotKeys.every(slot => Number.isInteger(data.levels?.[slot]) && Object.hasOwn(data.equipped ?? {}, slot))) return null;
    return data;
  } catch {
    return null;
  }
}

export function affixChoices(slot, exclude) {
  return Object.keys(AFFIXES).filter(key => key !== exclude && AFFIXES[key].slots.includes(slot));
}

function roll(key, random) {
  const { min, max, step = 1 } = AFFIXES[key];
  return { key, value: min + step * integer(random, 0, (max - min) / step) };
}

export function addDrop(save, slot, random = Math.random) {
  const choices = affixChoices(slot);
  const first = choices.splice(integer(random, 0, choices.length - 1), 1)[0];
  const second = choices[integer(random, 0, choices.length - 1)];
  const item = {
    id: save.nextItem++, slot, flame: integer(random, 1, 3), locked: null,
    affixes: [roll(first, random), roll(second, random)],
  };
  if (save.bag.length >= 60) {
    save.dust += 2;
    return null;
  }
  save.bag.push(item);
  return item;
}

function rollItem(save, item, target, random) {
  const locked = item.affixes[item.locked ?? -1];
  const choices = affixChoices(item.slot, locked?.key);
  if (save.dust < 1 || (target && (save.pity < PITY || !choices.includes(target)))) return false;
  save.dust -= 1;
  const rolled = new Set(locked ? [locked.key] : []);
  item.affixes = item.affixes.map((affix, index) => {
    if (index === item.locked) return affix;
    let key = target;
    if (!key) {
      const available = choices.filter(option => !rolled.has(option));
      key = available[integer(random, 0, available.length - 1)];
    }
    target = null;
    rolled.add(key);
    return roll(key, random);
  });
  return true;
}

export function reroll(save, item, random = Math.random) {
  if (!rollItem(save, item, null, random)) return false;
  save.pity = Math.min(PITY, save.pity + 1);
  return true;
}

export function reforge(save, item, target, random = Math.random) {
  if (!target || !rollItem(save, item, target, random)) return false;
  save.pity = 0;
  return true;
}

export const upgradeCost = level => 20 + 12 * level;

export function stats(save) {
  const { weapon, shield, armor, charm } = save.levels;
  const result = { hp: 180 + 12 * armor, attack: 23 + 3 * weapon + 2 * charm, reduction: shield, haste: 0, expose: 0, prayer: 0 };
  for (const item of save.bag.filter(item => save.equipped[item.slot] === item.id)) {
    if (item.slot === 'weapon' || item.slot === 'charm') result.attack += item.flame;
    else result.hp += 5 * item.flame;
    for (const { key, value } of item.affixes) {
      const stat = { force: 'attack', vitality: 'hp', ward: 'reduction' }[key] ?? key;
      result[stat] += value;
    }
  }
  return result;
}

export function settleOffline(save, now, random = Math.random) {
  const minutes = Math.min(OFFLINE.minutes, Math.max(0, Math.floor((now - save.savedAt) / 60_000)));
  save.savedAt = Math.max(save.savedAt, now);
  if (!save.resident || save.best < 1 || minutes === 0) return null;
  const gold = minutes * OFFLINE.gold;
  const dust = minutes * OFFLINE.dust;
  save.gold += gold;
  save.dust += dust;
  save.offlineMinutes += minutes;
  const drops = Math.floor(save.offlineMinutes / OFFLINE.dropEvery);
  save.offlineMinutes %= OFFLINE.dropEvery;
  for (let i = 0; i < drops; i++) addDrop(save, slotKeys[integer(random, 0, slotKeys.length - 1)], random);
  return { minutes, gold, dust, drops };
}

export function startBattle(save, stage) {
  const config = STAGES[stage];
  const attributes = stats(save);
  return {
    stage, time: 0, nextAction: 0, nextSwing: 1, order: [...save.order], events: [], result: null,
    allies: [{ id: 'paladin', name: '聖騎士', kind: 'hero', maxHp: attributes.hp, hp: attributes.hp,
      shield: 0, shieldUntil: 0, attributes, cooldowns: Object.fromEntries(save.order.map(id => [id, 0])) }],
    enemies: config.enemies.map((name, index) => ({ id: `enemy-${index}`, name, hp: config.hp, maxHp: config.hp,
      attack: config.attack, boss: Boolean(config.boss), nextAttack: 2.5 + index * .25,
      nextCharge: config.boss ? 1 : Infinity, impact: null, exposedUntil: 0 })),
    orbit: null,
  };
}

function record(battle, kind, title, text, source, target) {
  battle.events.push({ time: battle.time, kind, title, text, source, target });
}

function damage(battle, unit, amount, title, source) {
  const hero = battle.allies.find(ally => ally.kind === 'hero');
  const multiplier = unit.exposedUntil > battle.time ? 1 + hero.attributes.expose / 100 : 1;
  const hit = Math.min(unit.hp, Math.max(1, Math.round(amount * multiplier)));
  unit.hp -= hit;
  record(battle, 'hit', `${title} −${hit}`, `${title}命中${unit.name}，造成 ${hit} 傷害${unit.hp === 0 ? '並擊破' : ''}`, source, unit.id);
}

function cast(battle, hero, enemies, id) {
  const time = battle.time;
  const attack = hero.attributes.attack;
  const skill = SKILLS[id];
  const target = enemies[0];
  record(battle, 'cast', skill.name, `施放 ${skill.name}`, id);
  switch (id) {
    case 'strike': damage(battle, target, attack * (hero.shield > 0 ? 2.7 : 1.9), skill.name, id); break;
    case 'sweep':
      for (const enemy of enemies) {
        damage(battle, enemy, attack * 1.1, skill.name, id);
        if (hero.attributes.expose > 0) enemy.exposedUntil = time + 4;
      }
      if (hero.attributes.expose > 0) record(battle, 'buff', '破防', `敵方受到傷害增加 ${hero.attributes.expose}%，持續 4 秒`, id);
      break;
    case 'guard':
      hero.shield = Math.round(hero.maxHp * .4);
      hero.shieldUntil = time + 4;
      record(battle, 'block', `護盾 +${hero.shield}`, `盾誓反擊獲得 ${hero.shield} 護盾，持續 4 秒`, id);
      break;
    case 'orbit':
      battle.orbit = { next: time + 1, remaining: 3 };
      record(battle, 'buff', skill.name, '聖鎚迴旋，每秒攻擊全場', id);
      break;
    case 'heal': {
      const recovered = Math.min(hero.maxHp - hero.hp, Math.round(hero.maxHp * (.29 + hero.attributes.prayer / 100)));
      hero.hp += recovered;
      record(battle, 'buff', `生命 +${recovered}`, `回生禱言回復 ${recovered} 生命`, id);
      break;
    }
    case 'break':
      damage(battle, target, attack * .95, skill.name, id);
      if (target.impact !== null && target.hp > 0) {
        target.impact = null;
        record(battle, 'ice', '蓄力打斷', `斷勢聖印打斷${target.name}重擊`, id, target.id);
      }
      break;
  }
  hero.cooldowns[id] = time + skill.cooldown - (id === 'guard' ? Math.min(2, hero.attributes.haste) : 0);
  battle.nextAction = time + .5;
}

function enemyHit(battle, enemy, heavy) {
  const ally = battle.allies.find(unit => unit.hp > 0);
  if (!ally) return;
  const raw = Math.max(1, (heavy ? 86 : enemy.attack) - (ally.attributes?.reduction ?? 0));
  const absorbed = Math.min(ally.shield ?? 0, raw);
  if (absorbed) ally.shield -= absorbed;
  const lost = Math.min(ally.hp, raw - absorbed);
  ally.hp -= lost;
  const attack = heavy ? '重擊' : '攻擊';
  record(battle, absorbed ? 'block' : 'hurt', absorbed ? `格擋 ${absorbed}` : `生命 −${lost}`, `${enemy.name}${attack}，${ally.name}承受 ${lost} 傷害${absorbed ? `，格擋 ${absorbed}` : ''}`);
  if (absorbed && ally.hp > 0 && ally.kind === 'hero') damage(battle, enemy, ally.attributes.attack * .65, '盾誓反擊', 'guard');
}

export function tick(battle) {
  if (battle.result) return battle.result;
  const hero = battle.allies.find(unit => unit.kind === 'hero');
  const time = battle.time;
  const living = () => battle.enemies.filter(enemy => enemy.hp > 0);
  if (hero.shieldUntil <= time) hero.shield = 0;

  for (const enemy of living()) {
    if (enemy.nextCharge <= time) {
      enemy.impact = time + 2;
      enemy.nextCharge = time + 6;
      record(battle, 'charge', '重擊蓄力', `${enemy.name}開始蓄力`, null, enemy.id);
    }
  }
  const ready = battle.order.find(id => hero.cooldowns[id] <= time);
  if (ready && battle.nextAction <= time && living().length) cast(battle, hero, living(), ready);
  if (battle.orbit?.remaining > 0 && battle.orbit.next <= time) {
    for (const enemy of living()) damage(battle, enemy, hero.attributes.attack * .45, '迴旋聖鎚', 'orbit');
    battle.orbit.remaining -= 1;
    battle.orbit.next += 1;
  }
  if (battle.nextSwing <= time && living().length) {
    damage(battle, living()[0], hero.attributes.attack * .62, '普攻');
    battle.nextSwing = time + 1.5;
  }
  for (const enemy of living()) {
    if (enemy.impact !== null && enemy.impact <= time) {
      enemy.impact = null;
      enemyHit(battle, enemy, true);
    }
    if (enemy.hp > 0 && enemy.nextAttack <= time) {
      enemy.nextAttack = time + (enemy.boss ? 2.5 : 3);
      enemyHit(battle, enemy, false);
    }
  }
  if (!living().length) battle.result = 'win';
  else if (hero.hp <= 0 || time >= 60) battle.result = 'loss';
  else battle.time += STEP;
  return battle.result;
}

export function finishBattle(save, battle, random = Math.random) {
  if (!battle.result || battle.finished) return null;
  battle.finished = true;
  const { stage, result } = battle;
  if (result === 'loss') {
    save.running = null;
    return { text: stage === 3 ? '挑戰失敗，可先刷關養成，再自行挑戰' : '推關失敗，可回前一關刷裝再試' };
  }
  const config = STAGES[stage];
  const mode = save.running.mode;
  const slot = mode === 'farm' ? slotKeys[integer(random, 0, slotKeys.length - 1)] : config.slot;
  const item = addDrop(save, slot, random);
  save.gold += config.gold;
  save.best = Math.max(save.best, stage + 1);
  if (stage === 0 && save.best === 1) save.resident = true;
  const text = `擊破${config.name}，金幣 +${config.gold}，${item ? `取得哨衛${SLOTS[item.slot]}` : '背包已滿，分解粉塵 +2'}`;
  save.running = null;
  if (stage === 2 && !save.firstBoss) {
    save.firstBoss = true;
    save.selected = 3;
    save.running = { stage: 3, mode: 'boss' };
  } else if (mode === 'push' && stage < 2) {
    save.selected = stage + 1;
    save.running = { stage: stage + 1, mode: 'push' };
  } else if (mode === 'farm') {
    save.running = { stage, mode };
  }
  return { text };
}
