import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as sleep } from 'node:timers/promises';

const root = fileURLToPath(new URL('../showcase/', import.meta.url));
const screenshotDir = process.argv[2] && resolve(process.argv[2]);
const edge = process.env.MAPLE_EDGE_PATH ?? join(process.env['ProgramFiles(x86)'], 'Microsoft', 'Edge', 'Application', 'msedge.exe');
const key = 'maple-idle.paladin.v1.test';
const types = { html: 'text/html', css: 'text/css', svg: 'image/svg+xml', mjs: 'text/javascript' };
const server = createServer(async (request, response) => {
  const path = new URL(request.url, 'http://localhost').pathname;
  const local = resolve(root, '.' + path + (path.endsWith('/') ? 'index.html' : ''));
  if (!local.startsWith(resolve(root) + sep)) return response.writeHead(404).end();
  try {
    const buffer = await readFile(local);
    response.writeHead(200, { 'Content-Type': types[local.split('.').at(-1)] ?? 'application/octet-stream' }).end(buffer);
  } catch {
    response.writeHead(404).end();
  }
});
await new Promise((done, fail) => { server.on('error', fail); server.listen(0, '127.0.0.1', done); });
const preview = process.env.MAPLE_PREVIEW_URL ?? `http://127.0.0.1:${server.address().port}/play/`;
const profile = await mkdtemp(join(tmpdir(), 'maple-edge-'));
const browser = spawn(edge, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  '--remote-debugging-port=0', '--user-data-dir=' + profile, 'about:blank'], { stdio: ['ignore', 'ignore', 'pipe'] });
let browserError;
let diagnostics = '';
browser.on('error', error => { browserError = error; });
browser.stderr.on('data', chunk => { diagnostics = (diagnostics + chunk).slice(-1500); });

async function until(probe, description, ms = 20_000) {
  const deadline = Date.now() + ms;
  while (Date.now() < deadline) {
    const value = await probe();
    if (value) return value;
    await sleep(70);
  }
  throw new Error('Timed out: ' + description);
}

let socket;
try {
  const port = await until(async () => {
    if (browserError) throw browserError;
    if (browser.exitCode) throw new Error('Browser exited ' + browser.exitCode + '\n' + diagnostics);
    try { return (await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0].trim(); }
    catch { return null; }
  }, 'Edge DevTools');
  const pages = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  socket = new WebSocket(pages.find(page => page.type === 'page').webSocketDebuggerUrl);
  await new Promise((done, fail) => { socket.addEventListener('open', done, { once: true }); socket.addEventListener('error', fail, { once: true }); });
  const requests = new Map();
  const pageErrors = [];
  let seq = 0;
  socket.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (message.method === 'Runtime.exceptionThrown') pageErrors.push(message.params.exceptionDetails);
    if (message.id) {
      const { resolve: done, reject: fail } = requests.get(message.id);
      requests.delete(message.id);
      if (message.error) fail(new Error(message.error.message));
      else done(message.result);
    }
  });
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++seq;
    requests.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
  const evaluate = async expression => {
    const result = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description ?? result.exceptionDetails.text);
    return result.result.value;
  };
  const load = async () => {
    const previous = await evaluate('performance.timeOrigin');
    await send('Page.navigate', { url: preview + '?test=1' });
    await until(async () => {
      try { return await evaluate(`performance.timeOrigin !== ${previous} && location.search === '?test=1' && document.readyState === 'complete' && document.querySelectorAll('.allies .slot').length === 5`); }
      catch { return false; }
    }, 'trial is ready');
  };
  const click = selector => evaluate(`(() => {
    const element = document.querySelector(${JSON.stringify(selector)});
    if (!element || element.disabled) throw new Error('Cannot click ' + ${JSON.stringify(selector)});
    element.click();
  })()`);
  const saved = () => evaluate(`JSON.parse(localStorage.getItem('${key}'))`);
  const text = selector => evaluate(`document.querySelector(${JSON.stringify(selector)}).textContent`);
  const change = (selector, value) => evaluate(`(() => {
    const input = document.querySelector(${JSON.stringify(selector)});
    input.value = ${JSON.stringify(String(value))};
    input.dispatchEvent(new Event('change', { bubbles: true }));
  })()`);
  const open = name => click(`[data-panel="${name}"]`);
  const close = () => click('#panel form button');
  const fit = async (width, height) => {
    await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false });
    assert.equal(await evaluate('document.documentElement.scrollWidth <= innerWidth'), true);
    const fieldShare = await evaluate('document.querySelector(".field").offsetHeight / document.querySelector(".game").offsetHeight');
    assert.ok(fieldShare >= .4 && fieldShare <= .45, fieldShare);
  };
  const shot = async name => {
    if (!screenshotDir) return;
    await mkdir(screenshotDir, { recursive: true });
    const { data } = await send('Page.captureScreenshot', { format: 'png' });
    await writeFile(join(screenshotDir, name), Buffer.from(data, 'base64'));
  };

  await send('Page.enable');
  await send('Runtime.enable');
  await send('Page.addScriptToEvaluateOnNewDocument', { source: 'Math.random = () => 0.38' });
  await load();
  await fit(390, 844);
  assert.equal(await evaluate("document.querySelector('link[rel=preload][as=image]').href.endsWith('/assets/tombstone.svg')"),true);
  await click('#speed');
  await click('#action');
  await until(() => evaluate("document.querySelector('.top-band .tone-hit') !== null"), 'live outgoing hit');
  await shot('390x844-4x-hit.png');
  await until(() => evaluate("!!document.querySelector('[data-kind=sweep]')"), 'live horizontal sweep');
  await sleep(90);
  await shot('390x844-4x-sweep.png');
  await until(() => evaluate("!!document.querySelector('[data-kind=orbit-track] image')"), 'live orbiting hammer');
  await shot('390x844-4x-orbit.png');
  await until(() => evaluate("document.querySelectorAll('.enemy').length > 0 && !document.querySelector('.enemy:not(.fallen)')"), 'wave cleared');
  await sleep(520);
  assert.equal(await evaluate("document.querySelectorAll('.vfx-stage > g,.callout').length"),0);
  await until(async () => {
    const state = await saved();
    return state.firstBoss && state.best === 3 && state.running === null;
  }, '3 stages and a failed automatic first boss');
  assert.match(await text('#report-text'), /挑戰失敗/);
  assert.deepEqual((await saved()).bag.map(item => item.slot), ['weapon', 'shield', 'armor']);
  console.log('PASS 390×844, automatic stages and boss, drops, combat log');

  await open('character');
  await click('[data-op="upgrade"][data-value="shield"]');
  await close();
  await open('bag');
  const oldShield = (await saved()).bag.find(item => item.slot === 'shield');
  await change('#pick-item', oldShield.id);
  await click('[data-op="equip"]');
  await close();
  await open('map');
  assert.match(await text('.log-list'), /首次自動挑戰/);
  await click('[data-op="clock"][data-value="15"]');
  const accrued = await saved();
  assert.match(await text('#notice'), /金幣 \+30、粉塵 \+15、掉落 1 件/);
  const newShield = accrued.bag.at(-1);
  assert.equal(newShield.slot, 'shield');
  await load();
  assert.equal((await saved()).gold, accrued.gold);
  assert.equal((await saved()).dust, accrued.dust);
  assert.equal(await evaluate('localStorage.getItem("maple-idle.paladin.v1")'), null);
  await open('bag');
  await change('#pick-item', newShield.id);
  await click('[data-op="equip"]');
  assert.equal((await saved()).equipped.shield, newShield.id);
  assert.equal((await saved()).levels.shield, 1);
  await change('#pick-item', oldShield.id);
  await click('[data-op="salvage"]');
  assert.equal((await saved()).dust, 17);
  await change('#pick-item', newShield.id);
  await click('[data-op="lock"][data-value="0"]');
  for (let i = 0; i < 3; i++) await click('[data-op="reroll"]');
  assert.equal((await saved()).pity, 3);
  await change('#target', 'haste');
  await click('[data-op="reforge"]');
  const modified = await saved();
  assert.equal(modified.pity, 0);
  assert.deepEqual(modified.bag.at(-1).affixes[0], newShield.affixes[0]);
  assert.equal(modified.bag.at(-1).affixes[1].key, 'haste');
  await close();
  console.log('PASS slot upgrade carries to replacement, salvage, lock, three rolls and exact pity');

  await open('map');
  await click('[data-op="clock"][data-value="180"]');
  assert.match(await text('#notice'), /離線 120 分鐘/);
  await close();
  await open('skills');
  await click('[data-op="preset"][data-value="boss"]');
  await click('[data-op="up"][data-value="1"]');
  assert.deepEqual((await saved()).order.slice(0, 2), ['strike', 'guard']);
  await click('[data-op="down"][data-value="0"]');
  await close();
  await click('#action');
  const visible = selector => evaluate(`Boolean(document.querySelector(${JSON.stringify(selector)}))`);
  await until(() => visible('.tone-interrupt'), 'visible boss interrupt');
  await sleep(190);
  await shot('390x844-1x-interrupt.png');
  await fit(1280, 800);
  await click('#motion');
  await click('#gray');
  await until(() => visible('.tone-counter'), 'static grayscale counter');
  await shot('1280x800-1x-gray-reduced-counter.png');

  await load();
  assert.equal((await saved()).running.mode, 'boss');
  await click('#speed');
  await until(async () => (await saved()).best === 4, 'manual boss victory after resuming the encounter');
  assert.match(await text('#report-text'), /擊破灰角守衛/);
  assert.equal((await saved()).bag.at(-1).slot, 'charm');
  assert.deepEqual((await saved()).order, ['guard', 'strike', 'break', 'heal']);
  // Exercise the real renderer with a deterministic four-enemy beat, including
  // combinations that the first three stages do not naturally produce.
  await load();
  await evaluate(`(async () => {
    const field = document.querySelector('#field');
    window.fxTest = (await import('./effects.mjs')).createEffects(field);
    document.querySelector('#field-note').style.display = 'none';
    field.querySelector('.field-note').hidden = true;
    const template = document.querySelector('#enemy-0');
    document.querySelector('#enemies').replaceChildren(...Array.from({ length: 4 }, (_, i) => {
      const card = template.cloneNode(true);
      card.id = 'enemy-' + i;
      return card;
    }));
  })()`);
  const verifyGeometry = () => evaluate(`(() => {
    const badges = [...document.querySelectorAll('.callout')];
    const protectedNodes = [...document.querySelectorAll('.slot-name,.slot-hp,.meter,.slot-cd,.report')];
    const overlaps = (a,b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
    return badges.length > 0 && badges.every((badge,i) => {
      const r = badge.getBoundingClientRect(), band = badge.parentElement.getBoundingClientRect();
      return r.width > 0 && r.left >= band.left - 0.5 && r.right <= band.right + 0.5 &&
        r.top >= band.top - 0.5 && r.bottom <= band.bottom + 0.5 &&
        ![...protectedNodes, ...badges.slice(i+1)].some(n => overlaps(r,n.getBoundingClientRect()));
    });
  })()`);
  for (const [width,height] of [[390,844],[1280,800]]) {
    await fit(width,height);
    await sleep(80);
    for (const speed of [1,4]) for (const reduced of [false,true]) for (const gray of [false,true]) {
      await evaluate(`(() => {
        fxTest.clear();
        document.querySelector('#speed').textContent = '${speed}×';
        document.body.classList.toggle('reduce', ${reduced});
        document.body.classList.toggle('gray', ${gray});
        const hits = Array.from({length:4}, (_,i) => ({kind:'hit', source:'sweep', target:'enemy-'+i, amount:125}));
        fxTest.play([...hits,{kind:'hurt',source:'enemy-1',raw:20,lost:20},
          {kind:'block',source:'enemy-2',heavy:true,raw:86,absorbed:86,lost:0},
          {kind:'buff',source:'heal',amount:55}], ${speed}, ${reduced});
      })()`);
      await until(() => visible('.tone-block'), 'impact');
      await sleep(35);
      assert.equal(await verifyGeometry(), true, `geometry ${width} ${speed} ${gray} ${reduced}`);
      assert.equal(await evaluate("document.querySelectorAll('[data-kind=incoming]').length"), 1);
      assert.equal(await evaluate("document.querySelector('[data-kind=incoming]').dataset.source"), 'enemy-2');
      assert.equal(await evaluate("document.querySelectorAll('[data-kind=sweep]').length"), 1);
      assert.equal(await evaluate("[...document.querySelectorAll('.top-band .callout')].every(n => n.textContent === '▲ −125') && document.querySelectorAll('.top-band .callout').length === 4"), true);
      assert.equal(await evaluate("document.querySelectorAll('.fx-anim-draw').length === 0"), reduced);
      assert.equal(await evaluate(`(() => {
        const box = q => document.querySelector(q).getBoundingClientRect();
        const halo = box('[data-kind=heal]'), shield = box('[data-kind=shield]'), label = box('.tone-heal');
        const delta = Math.abs((halo.left+halo.right-label.left-label.right)/2);
        return halo.left > shield.right && delta < 1 && [...document.querySelectorAll('.vfx-stage > g')].every(g => {
          const r = g.getBoundingClientRect();
          return r.top >= box('.top-band').bottom-.5 && r.bottom <= box('.bottom-band').top+.5 &&
            r.left >= box('#field').left && r.right <= box('#field').right;
        });
      })()`),true,'glyph safety and recovery alignment');
      if (width === 390 && gray && reduced && speed === 4) await shot('390x844-4x-gray-reduced-four-target-test.png');
    }
  }
  await evaluate(`fxTest.clear(); fxTest.play([{kind:'block',source:'enemy-2',heavy:true,raw:86,absorbed:86,lost:0},
    {kind:'hit',source:'guard',target:'enemy-2',amount:15}],4,false)`);
  assert.equal(await visible('[data-kind=counter]'),false);
  await until(() => visible('[data-kind=counter]'), 'counter follows contact');
  assert.equal(await evaluate("document.querySelector('[data-kind=incoming]').getAttribute('opacity')"), '0.3');
  assert.equal(await evaluate("document.querySelector('[data-kind=counter]').dataset.target"), 'enemy-2');
  assert.equal(await visible('[data-kind=shield] line'),true);
  await evaluate(`fxTest.clear(); fxTest.play([{kind:'block',source:'enemy-2',raw:86,absorbed:86,lost:0},
    {kind:'hit',source:'guard',target:'enemy-2',amount:15}],4,false);
    fxTest.clear();`);
  await sleep(240);
  assert.equal(await visible('.vfx-stage > g,.callout'),false,'clear cancels delayed effects');
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await until(() => evaluate("document.querySelector('#motion').getAttribute('aria-pressed') === 'true'"),'system reduced motion applied');
  await evaluate(`fxTest.play([{kind:'hit',source:'strike',target:'enemy-2',amount:50,shieldBonus:true}],1,false)`);
  assert.equal(await evaluate("document.querySelector('[data-kind=strike]').dataset.bend"),'44');
  assert.equal(await visible('[data-kind=strike] circle'),true);
  await evaluate(`fxTest.play([{kind:'hit',source:'break',target:'enemy-2',amount:12},{kind:'ice',target:'enemy-2'}],1,false)`);
  assert.equal(await visible('[data-kind=strike]'),false);
  assert.equal(await visible('[data-kind=break]'),true);
  await evaluate(`fxTest.play([{kind:'hit',target:'enemy-2',amount:5}],1,false)`);
  assert.equal(await visible('[data-kind=basic]'),false,'ordinary swing respects interrupt priority');
  for (const [speed, expectedTtl] of [[1,420],[4,220]]) {
    const check = await evaluate(`(async () => {
      fxTest.clear();
      fxTest.play([{kind:'hit',target:'enemy-1',amount:8}],${speed},true);
      const slash = document.querySelector('[data-kind=basic]');
      const box = slash.getBoundingClientRect();
      const field = document.querySelector('#field');
      const safe = box.top > field.querySelector('.top-band').getBoundingClientRect().bottom &&
        box.bottom < field.querySelector('.bottom-band').getBoundingClientRect().top;
      await new Promise(done => setTimeout(done, ${expectedTtl}+30));
      return [slash.dataset.bend, slash.querySelectorAll('path').length, safe, slash.isConnected];
    })()`);
    assert.deepEqual(check,['25',1,true,false]);
  }
  await evaluate(`fxTest.clear(); fxTest.syncOrbit(true,1,true)`);
  assert.equal(await visible('[data-kind=orbit-track] ellipse'),true);
  assert.equal(await visible('[data-kind=orbit-track] animateMotion'),false);
  await evaluate(`fxTest.syncOrbit(false,1,true)`);
  assert.equal(await visible('[data-kind=orbit-track]'),false);
  await send('Emulation.setEmulatedMedia',{features:[]});
  console.log('PASS 16 geometry configurations, four-way AOE, two incoming enemies, healing, shield contact and counter target');
  assert.deepEqual(pageErrors, []);
  console.log('PASS 1280×800, reorder, boss interrupt, motion/grayscale, reload during combat and victory');
} catch (error) {
  if (diagnostics) console.error(diagnostics);
  throw error;
} finally {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ id: 0, method: 'Browser.close' }));
    socket.close();
  }
  browser.stderr.destroy();
  if (browser.exitCode === null && browser.pid) {
    browser.kill();
    await Promise.race([new Promise(done => browser.once('exit', done)), sleep(1500)]);
  }
  server.closeAllConnections();
  server.close();
  await rm(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 100 }).catch(() => {});
}
