"use strict";
const canvas = document.querySelector("canvas");
const ctx = canvas.getContext("2d");
const buttons = [...document.querySelectorAll(".effects button")];
const motion = document.querySelector("#motion");
let reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
let selected = 0;
let frame;
const samples = [
  ["短刃命中", "短刃橫掃，甲殼上亮起一束金色裂光。", "旅人揮動短刃。", "刀鋒命中甲殼，甲蟲受到 18 點傷害。"],
  ["架盾格擋", "方盾在旅人身前合攏，撞擊火星向外彈開。", "甲蟲壓低前角，向前衝撞。", "旅人架盾，吸收 18 點傷害。"],
  ["冰凍中斷", "冰晶自足底向上結成稜角，甲蟲的衝撞中斷。", "甲蟲開始蓄力。", "霜晶鎖住甲蟲，衝撞中斷。"]
];
function rect(x,y,w,h,color){ctx.fillStyle=color;ctx.fillRect(Math.round(x),Math.round(y),w,h);}
function sprite(x,y,rows,colors){
  rows.forEach((row,dy)=>[...row].forEach((c,dx)=>{if(colors[c])rect(x+dx,y+dy,1,1,colors[c]);}));
}
function pine(x,base,h,color){
  rect(x-1,base-h,2,h,color);
  for(let j=0;j<3;j++){const top=base-h+j*h*.19;
    for(let i=0;i<h*.44;i+=2){const w=Math.floor(i*.46);rect(x-w,top+i,2*w+1,2,color);}
  }
}
function woods(){
  rect(0,0,240,104,"#80958b");
  rect(0,29,240,22,"#aab3a0");
  rect(164,11,12,14,"#e7c884");rect(161,14,18,8,"#e7c884");
  for(let x=0;x<240;x+=2){const y=35+Math.floor(6*Math.sin(x*.064)+4*Math.cos(x*.111));rect(x,y,2,42,"#667d70");}
  for(let i=0;i<23;i++)pine(i*12-4,65,22+(i*17)%23,"#49675a");
  for(let i=0;i<12;i++)pine(i*23-7,78,26+(i*19)%30,"#304d42");
  rect(0,75,240,29,"#405547");rect(0,80,240,3,"#829076");rect(0,83,240,8,"#596453");
  rect(0,91,240,13,"#263c34");
  for(let i=0;i<116;i++){const x=(i*53)%240,y=76+(i*17)%28;rect(x,y,1+i%3,1,y<91?"#76876c":"#425c49");}
  pine(3,93,84,"#233c33");pine(235,94,84,"#233c33");
  rect(32,62,2,21,"#363c32");rect(29,61,10,2,"#63513c");rect(36,63,2,3,"#524530");rect(35,66,4,5,"#eac579");
}
const traveler=["....hhhh....","...hhhhh....","..hhhhhhh...","....ffkf....","....fff.....","...gggg.....","..ggttgg....",".gggtttf....","..ggttt.....","...bbbb.....","...bb.bb....","..kkk.kkk..."];
const beetle=[".........aa....","...aa...aaaa...","..aa..aaaooaa..",".aa.aaaaoooaaa.","..aaaaaaoooaaaa","..kakkkkoooook.","..kwwkkoooooak.","...kkkkkkkkkk..","..kk.k...k..kk."];
function draw(progress){
  woods();
  const impact = progress>.38 && progress<.91;
  const hx=70+(selected===0&&!reduced?Math.round(19*Math.sin(progress*Math.PI)):0);
  const bx=selected===1?145-Math.round(57*(reduced?.85:Math.sin(progress*Math.PI))):145;
  sprite(hx,68,traveler,{h:"#a66b47",f:"#e8be87",k:"#26332d",g:"#71ae92",t:"#cfab68",b:"#594838"});
  rect(hx+8,74,7,1,"#e5d9a9");
  sprite(bx,72,beetle,{a:"#dba45c",o:"#a45b3b",k:"#4b3930",w:"#fbe1a2"});
  if(!impact)return;
  if(selected===0){for(let i=0;i<18;i++){rect(bx-6+i,81-i,3,1,"#ffe6a4");}rect(bx+8,65,2,7,"#fff4ce");rect(bx+5,68,8,1,"#fff4ce");}
  if(selected===1){rect(hx+13,65,2,14,"#a6d6bd");rect(hx+15,67,2,10,"#d8f2cf");rect(hx+11,79,3,2,"#a6d6bd");rect(hx+18,67,3,1,"#f7d383");}
  if(selected===2){for(let i=0;i<4;i++){const x=bx-3+i*5;const h=6+i%3*3;rect(x,81-h,3,h,"#85bdd0");rect(x+1,79-h,1,h,"#d1f4ed");}}
}
function play(){
  cancelAnimationFrame(frame);
  motion.setAttribute("aria-pressed",String(reduced));
  const data=samples[selected];
  buttons.forEach((b,i)=>b.setAttribute("aria-pressed",String(i===selected)));
  document.querySelector("#desc").textContent=data[1];
  const log=document.querySelector("#log");log.replaceChildren();
  ["00.0","01.2"].forEach((stamp,i)=>{const row=document.createElement("li");const time=document.createElement("time");time.textContent=stamp+"s";row.append(time,document.createTextNode(data[i+2]));log.append(row);});
  if(reduced){draw(.64);return;}
  const start=performance.now();
  function tick(now){const p=Math.min(1,(now-start)/1450);draw(p);if(p<1)frame=requestAnimationFrame(tick);}
  frame=requestAnimationFrame(tick);
}
buttons.forEach((b,i)=>b.addEventListener("click",()=>{selected=i;play();}));
document.querySelector("#play").onclick=play;
motion.onclick=()=>{reduced=!reduced;play();};
play();
