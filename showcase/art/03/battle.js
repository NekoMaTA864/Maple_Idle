"use strict";

const icons = {
  grave: '<path d="M10 35V17a10 10 0 0 1 20 0v18M7 36h26M15 19h10m-9 4h8m-9 4h6M7 34l-3-3m29 3 3-4"/>',
  golem: '<path d="m14 6 8-3 7 7-3 8-13 1-4-7Zm-2 14 16-1 4 9-7 6-13-3-4-6Zm-3 0-4 2-3 9 5 3 4-3m19-11 6 3 2 7-5 4-4-3m-16 1-2 6h7l2-5m5 0 1 5h7l-3-6M16 11h1m6-1h1m-7 5 5-1"/>',
  demon: '<path d="M13 13Q8 9 8 3L4 7l1 8 5 5-6-1 5 7 5 2 1 6 5 3 5-3 1-6 5-2 5-7-6 1 5-5 1-8-4-4q0 6-5 10l-4-2-3 3-3-3ZM11 21l7 3-3 2Zm18 0-7 3 3 2ZM16 31l4-2 4 2m-6 1 2 2 2-2"/>',
  bat: '<path d="M20 16c-5 0-7-7-11-8L2 9l5 5 2 10 5-2 4 6 2-4 2 4 4-6 5 2 2-10 5-5-7-1c-4 1-6 8-11 8Zm-4-3 2 4m6-4-2 4m-4 3h.4m3.2 0h.4"/>',
  hammer: '<path d="m17 15 6-10 14 8-6 11ZM20 10l14 8m-18-1-12 17 4 3 14-17m-14 10 4 3m-2-6 4 3m11-18-4 7m1-6 6 4"/>',
  sanctuary: '<path d="m16 13 7-9 12 8-7 10Zm4 5-15 17 4 3 15-17M5 12l7 2m-5-8 7 4m21 14 3 4m-10-3 1 8"/>',
  shield: '<path d="M20 4q6 4 14 5l-2 13q-3 8-12 13-9-5-12-13L6 9q8-1 14-5Zm0 4q5 3 10 4l-2 10q-2 6-8 9-6-3-8-9l-2-10q5-1 10-4Zm0 5v13m-5-8h10"/>',
  snow: '<path d="M20 4v32M6 12l28 16M6 28l28-16M16 7l4 4 4-4m-8 26 4-4 4 4M7 17l6-1-1-6m21 13-6 1 1 6M7 23l6 1-1 6m21-13-6-1 1-6"/>',
  star: '<path d="m20 4 4 12 12 4-12 4-4 12-4-12-12-4 12-4Zm-9 7 3 3m15-3-3 3m3 15-3-3m-15 3 3-3"/>'
};

const encounters = {
  hit: { time:"24.6", clock:"00:24", label:"聖域 −1420", detail:"", state:"聖域命中", hp:10980, shield:230, report:"聖域命中炎魔，造成 1420 傷" },
  block: { time:"24.0", clock:"00:24", label:"格擋 0 傷", detail:"護盾 +90", state:"重擊攔截", hp:12400, shield:320, report:"十字聖盾擋下炎魔重擊，吸收 420 傷" },
  ice: { time:"23.8", clock:"00:23", label:"冰凍打斷", detail:"", state:"蓄力已打斷", hp:12400, shield:230, report:"壓制術冰凍炎魔，打斷重擊蓄力" },
  buff: { time:"23.2", clock:"00:23", label:"防禦 +30%", detail:"", state:"蓄力中", hp:12400, shield:230, report:"神聖結合生效，提升防禦 30%" }
};

const get = id => document.getElementById(id);
const skills = [...document.querySelectorAll("[data-skill]")];
const field = get("field");
const boss = get("boss");
const motionPreference = matchMedia("(prefers-reduced-motion: reduce)");
let selected = "block";
let reduced = motionPreference.matches;
let fast = false;
let animationFrame;
let automatic;

for (const icon of document.querySelectorAll("[data-icon]")) {
  icon.innerHTML = '<svg viewBox="0 0 40 40" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round">' + icons[icon.dataset.icon] + '</svg>';
}

function show(name, animate = true) {
  selected = name;
  const event = encounters[name];
  cancelAnimationFrame(animationFrame);
  field.classList.remove("play");
  field.dataset.event = name;
  boss.classList.toggle("hit", name === "hit");
  boss.classList.toggle("frozen", name === "ice");
  get("core").classList.toggle("emphasis", name === "buff" || name === "hit");
  get("effect-label").textContent = event.label;
  get("effect-detail").textContent = event.detail;
  get("clock").textContent = event.clock;
  get("boss-state").textContent = event.state;
  get("boss-hp").textContent = "HP " + event.hp;
  get("boss-meter").style.setProperty("--fill", (event.hp / 124) + "%");
  get("shield-value").textContent = event.shield;
  get("shield-meter").style.setProperty("--fill", (event.shield / 11) + "%");
  get("report-time").textContent = event.time + " 秒";
  get("report-text").textContent = event.report;
  for (const skill of skills) {
    const active = skill.dataset.skill === name;
    skill.setAttribute("aria-pressed", String(active));
    skill.querySelector("small").textContent = active ? "生效中" : skill.dataset.skill === "hit" && name === "block" ? "冷卻 3s" : "就緒";
  }
  if (animate && !reduced) {
    animationFrame = requestAnimationFrame(() => {
      animationFrame = requestAnimationFrame(() => field.classList.add("play"));
    });
  }
}

function scheduleAuto() {
  clearInterval(automatic);
  if (get("auto").getAttribute("aria-pressed") !== "true") return;
  const cycle = Object.keys(encounters);
  automatic = setInterval(() => show(cycle[(cycle.indexOf(selected) + 1) % cycle.length]), fast ? 1500 : 3000);
}

skills.forEach(skill => { skill.onclick = () => show(skill.dataset.skill); });
get("replay").onclick = () => show(selected);
get("motion").setAttribute("aria-pressed", String(reduced));
get("motion").onclick = () => {
  reduced = !reduced;
  get("motion").setAttribute("aria-pressed", String(reduced));
  show(selected, false);
};
get("gray").onclick = () => {
  const gray = document.body.classList.toggle("gray");
  get("gray").setAttribute("aria-pressed", String(gray));
};
get("speed").onclick = () => {
  fast = !fast;
  field.classList.toggle("fast", fast);
  get("speed").setAttribute("aria-pressed", String(fast));
  scheduleAuto();
};
get("auto").onclick = () => {
  const auto = get("auto");
  auto.setAttribute("aria-pressed", String(auto.getAttribute("aria-pressed") !== "true"));
  scheduleAuto();
};

const summaries = {
  角色: "60級 聖騎士。生命 4820。",
  背包: "當前武器為聖鎚・審判。",
  地圖: "第 10 層。挑戰目標為炎魔。",
  技能: "點擊戰鬥畫面上的聖域、十字聖盾、壓制術或神聖結合試招。"
};
for (const button of document.querySelectorAll("[data-page]")) {
  button.onclick = () => {
    const title = button.dataset.page;
    if (title === "戰鬥") return;
    get("preview-title").textContent = title;
    get("preview-text").textContent = summaries[title];
    get("preview").showModal();
  };
}
show(selected, false);
