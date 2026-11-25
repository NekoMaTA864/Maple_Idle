"use strict";

const palette = { ink:"#121921", silver:"#dce7e5", gold:"#e4b46a", ivory:"#fff0c3",
  wood:"#895736", mint:"#79b697", green:"#4b805d", blue:"#8ed0e6", frost:"#d9f3fa",
  amber:"#cd8248", plum:"#ad93d7", gray:"#65758a" };
const painters = {
  sword({line, box}) {
    line(5,20,19,5,4,"ink"); line(8,17,19,5,4,"silver"); line(9,15,19,5,1,"ivory");
    line(5,13,11,19,3,"gold"); line(3,21,7,17,3,"wood"); box(2,20,3,2,"gold");
  },
  staff({line,box}) {
    line(4,21,17,8,4,"wood"); line(5,20,17,8,1,"gold");
    box(13,3,7,7,"blue"); box(15,1,4,11,"blue"); box(16,3,3,5,"frost");
  },
  bow({line,box}) {
    line(3,4,12,5,3,"green"); line(12,5,19,11,3,"mint"); line(19,11,20,21,3,"green");
    line(3,4,20,21,1,"silver"); line(5,19,19,5,2,"ivory"); box(16,4,5,2,"mint"); box(19,5,2,4,"mint");
  },
  claw({line,box}) {
    line(4,18,17,4,3,"plum"); line(8,21,20,7,3,"silver"); line(3,16,9,22,3,"wood");
    line(2,5,8,11,2,"plum"); line(2,11,8,5,2,"silver"); box(4,7,3,3,"gray");
  },
  cannon({line,box}) {
    line(6,15,20,7,7,"gray"); line(5,12,9,18,4,"gold"); line(18,4,21,10,4,"gold");
    line(7,15,5,21,4,"wood"); box(20,5,3,4,"amber"); box(8,11,7,2,"silver");
  },
  slime({box}) {
    box(3,13,18,7,"green"); box(5,10,14,9,"green"); box(8,8,8,4,"mint"); box(6,11,12,4,"mint");
    box(7,14,2,3,"ink"); box(15,14,2,3,"ink"); box(11,17,2,1,"ivory"); box(5,20,14,1,"mint");
  },
  moth({line,box}) {
    for (const side of [-1,1]) {
      line(12,13,12+side*8,6,4,"ivory"); line(12,15,12+side*6,17,4,"silver");
      line(12,11,12+side*4,4,1,"gray"); box(11+side*5,9,2,2,"wood");
    }
    box(11,9,3,10,"gray"); box(11,8,3,2,"ivory");
  },
  beetle({line,box}) {
    for (const side of [-1,1]) {
      line(12,8,12+side*6,5,2,"amber"); line(12+side*6,5,12+side*5,2,2,"gold");
      line(12+side*2,12,12+side*8,10,2,"wood"); line(12+side*2,15,12+side*8,16,2,"wood");
      line(12+side*2,17,12+side*7,21,2,"wood");
    }
    box(7,8,11,5,"amber"); box(7,13,11,6,"gold"); box(9,19,7,2,"amber");
    box(12,13,1,7,"wood"); box(9,10,2,2,"ivory"); box(14,10,2,2,"ivory");
  },
  hit({line,box}) {
    line(5,19,20,4,3,"gold"); line(5,19,20,4,1,"ivory"); line(6,5,17,16,2,"ivory");
    box(3,10,2,2,"gold"); box(19,15,2,2,"gold");
  },
  block({box}) {
    [16,16,16,16,14,14,12,10,8,6,4,2].forEach((width, row)=>{
      box((24-width)/2,6+row,width,1,"ivory");
      if (row>0 && width>4) box((26-width)/2,6+row,width-2,1,"gold");
    });
    box(6,4,12,1,"ivory"); box(12,8,1,6,"wood");
  },
  impact({box,line}) {
    painters.block({box,line});
    for (const [x,y] of [[3,1],[6,3],[8,1],[16,1],[20,2]]) {
      box(x,y,2,1,"ivory");
    }
  },
  ice({line,box}) {
    for (const [x,y] of [[12,4],[19,8],[19,16],[12,20],[5,16],[5,8]]) {
      line(12,12,x,y,1,"frost"); box(x-1,y-1,3,3,"blue");
    }
    for (const x of [2,18]) for (const y of [2,18]) {
      box(x,y===2?y:y+3,4,1,"frost"); box(x===2?x:x+3,y,1,4,"frost");
    }
  }
};

function paint(canvas, name) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0,0,24,24);
  function box(x,y,w,h,color) {
    ctx.fillStyle = palette[color];
    ctx.fillRect(x,y,w,h);
  }
  function line(x,y,toX,toY,width,color) {
    const length = Math.max(Math.abs(toX-x),Math.abs(toY-y));
    const offset = Math.floor(width/2);
    for(let step=0;step<=length;step++){
      const t=step/length;
      box(Math.round(x+(toX-x)*t)-offset,Math.round(y+(toY-y)*t)-offset,width,width,color);
    }
  }
  painters[name]({box,line});
}

const weapons = [
  ["sword","劍士","巡誓大劍"],["staff","法師","霜芯法杖"],["bow","弓箭手","青梢長弓"],
  ["claw","盜賊","暮影雙爪"],["cannon","海盜","燼口重砲"]
];
const events = {
  hit: {tag:"命中 −18", time:"04.2s", report:name=>name+"命中甲蟲，造成 18 點傷害。"},
  block: {tag:"格擋 0 傷", time:"12.0s", report:()=>"架盾擋下甲蟲衝撞，吸收 18 點傷害。"},
  ice: {tag:"冰凍打斷", time:"10.8s", report:()=>"冰輪凍住甲蟲，中斷衝撞蓄力。"}
};
const get = id=>document.getElementById(id);
const sources = { hit:get("weaponSource"), block:get("blockSource"), ice:get("iceSource") };
let weapon = weapons[0];
let event = "hit";
let reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
let pending;

function render(animate = true) {
  clearTimeout(pending);
  const sample = events[event];
  const lane = get("lane");
  const boss = get("boss");
  paint(get("weapon"),weapon[0]);
  get("weaponName").textContent = weapon[2];
  document.querySelectorAll("[data-weapon]").forEach(button=>{
    button.setAttribute("aria-pressed", String(button.dataset.weapon === weapon[0]));
  });
  document.querySelectorAll("[data-event]").forEach(button=>{
    button.setAttribute("aria-pressed", String(button.dataset.event === event));
  });
  function reveal() {
    lane.dataset.effect = event;
    get("tag").textContent = sample.tag;
    get("tag").parentElement.dataset.label = sample.tag;
    paint(get("effect"),event==="block"?"impact":event);
    sources[event].classList.add("source-active");
    sources.hit.classList.toggle("protected",event==="block");
    boss.classList.toggle("hit-target",event==="hit");
    boss.classList.toggle("frozen",event==="ice");
    get("charge").textContent = {hit:"衝撞蓄力",block:"衝撞已攔截",ice:"蓄力已打斷"}[event];
    get("chargeBar").style.setProperty("--fill",event==="hit"?"74%":"0%");
    const hp = event==="hit"?82:100;
    get("bossHp").style.setProperty("--fill",hp+"%");
    get("bossHp").setAttribute("aria-valuenow",String(hp));
    get("time").textContent = sample.time;
    get("report").textContent = sample.report(weapon[2]);
    lane.classList.toggle("playing",animate && !reduced);
  }
  lane.classList.remove("playing");
  Object.values(sources).forEach(card=>card.classList.remove("source-active"));
  sources.hit.classList.remove("protected");
  boss.classList.remove("frozen","hit-target");
  if (reduced || !animate) { reveal(); return; }
  lane.dataset.effect = "";
  get("tag").textContent = "準備";
  get("effect").getContext("2d").clearRect(0,0,24,24);
  get("bossHp").style.setProperty("--fill","100%");
  get("bossHp").setAttribute("aria-valuenow","100");
  get("charge").textContent = "衝撞蓄力";
  get("chargeBar").style.setProperty("--fill","74%");
  get("report").textContent = "等待招式落地。";
  get("time").textContent = "";
  pending = setTimeout(reveal,270);
}

document.querySelectorAll("[data-art]").forEach(canvas=>paint(canvas,canvas.dataset.art));
for (const choice of weapons) {
  const button = document.createElement("button");
  const icon = document.createElement("canvas");
  icon.width = icon.height = 24;
  icon.setAttribute("aria-hidden","true");
  paint(icon,choice[0]);
  button.dataset.weapon = choice[0];
  button.append(icon,choice[1]);
  button.onclick = ()=>{ weapon=choice; render(false); };
  get("weapons").append(button);
}
document.querySelectorAll("[data-event]").forEach(button=>{
  button.onclick=()=>{event=button.dataset.event;render();};
});
get("replay").onclick=()=>render();
get("motion").setAttribute("aria-pressed",String(reduced));
get("motion").onclick=()=>{
  reduced=!reduced;
  get("motion").setAttribute("aria-pressed",String(reduced));
  render(false);
};
get("gray").onclick=()=>{
  const gray=document.body.classList.toggle("gray");
  get("gray").setAttribute("aria-pressed",String(gray));
};
render(false);
