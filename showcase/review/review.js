const DATA_URLS = {
  hero: "../data/hero_review.json",
  night_lord: "../data/night_lord_review.json"
};
const STORAGE_KEYS = {
  hero: "mapleIdle.review.hero.v1",
  night_lord: "mapleIdle.review.night_lord.v1"
};
const LEGACY_HERO_STORAGE_KEY = "mapleIdle.heroReview.v1";
const CLASS_LABELS = {
  hero: "英雄",
  night_lord: "夜使者"
};
const COPY_FIELDS = ["summary", "visualGoal", "identity", "expectedRhythm"];
const REVIEW_KEYS = ["overall", "identity", "burst", "sustain", "weight", "notes"];
const MODES = ["single", "compare", "focus"];

const CHECKLIST_ITEMS = [
  { id: "stable-rhythm", label: "穩定循環是否看起來最規律？" },
  { id: "sustain-feel", label: "持續輸出是否有明顯持續強化感？" },
  { id: "burst-peak", label: "爆發是否有明顯高峰？" },
  { id: "non-color-identity", label: "三套 Build 是否不用靠顏色也能分辨？" },
  { id: "sacred-weight", label: "聖劍降臨是否確實是最高視覺重量？" },
  { id: "aura-occlusion", label: "鬥氣本能 aura 是否會過度遮蔽角色？" },
  { id: "sword-occlusion", label: "燃燒靈魂之劍的 persistent sword 是否太搶畫面？" }
];

const app = document.querySelector("#app");
const classSelect = document.querySelector("#class-select");
const classEyebrow = document.querySelector("#class-eyebrow");
const pageTitle = document.querySelector(".header-inner h1");
const pageLede = document.querySelector(".header-inner .lede");
const modeSelect = document.querySelector("#mode-select");
const singleBuildControl = document.querySelector("#single-build-control");
const singleBuildSelect = document.querySelector("#single-build-select");
const focusBuildControls = document.querySelector("#focus-build-controls");
const focusASelect = document.querySelector("#focus-a-select");
const focusBSelect = document.querySelector("#focus-b-select");
const buildGrid = document.querySelector("#build-grid");
const observationPanel = document.querySelector("#comparison-observations");
const observationTitle = document.querySelector("#comparison-title");
const observationIntro = document.querySelector("#comparison-intro");
const observationGrid = document.querySelector("#observation-grid");
const buildsTitle = document.querySelector("#builds-title");
const checklistPanel = document.querySelector(".checklist-panel");
const checklist = document.querySelector("#checklist");
const statusMessage = document.querySelector("#status-message");
const viewSummary = document.querySelector("#view-summary");
const importFile = document.querySelector("#import-file");

const state = {
  classId: "hero",
  data: null,
  local: loadLocalState("hero"),
  mode: "single",
  selectedId: "",
  focusIds: ["", ""]
};

function emptyLocalState() {
  return { version: 1, reviews: {}, checklist: {}, copyOverrides: {} };
}

function loadLocalState(classId) {
  const keys = [STORAGE_KEYS[classId]];
  if (classId === "hero") keys.push(LEGACY_HERO_STORAGE_KEY);
  try {
    for (const key of keys) {
      const raw = window.localStorage.getItem(key);
      if (raw) return normaliseLocalState(JSON.parse(raw));
    }
  } catch (error) {
    return emptyLocalState();
  }
  return emptyLocalState();
}

function normaliseLocalState(value) {
  const source = value && typeof value === "object" ? value : {};
  const result = emptyLocalState();

  if (source.reviews && typeof source.reviews === "object") {
    for (const [entryId, review] of Object.entries(source.reviews)) {
      if (!review || typeof review !== "object") continue;
      result.reviews[entryId] = {};
      for (const key of REVIEW_KEYS) {
        if (key === "notes") {
          if (typeof review[key] === "string") result.reviews[entryId][key] = review[key].slice(0, 5000);
          continue;
        }
        const number = Number(review[key]);
        if (Number.isInteger(number) && number >= 1 && number <= 5) result.reviews[entryId][key] = number;
      }
    }
  }

  if (source.checklist && typeof source.checklist === "object") {
    for (const item of CHECKLIST_ITEMS) {
      if (source.checklist[item.id] === true) result.checklist[item.id] = true;
    }
  }

  if (source.copyOverrides && typeof source.copyOverrides === "object") {
    for (const [entryId, fields] of Object.entries(source.copyOverrides)) {
      if (!fields || typeof fields !== "object") continue;
      const allowed = {};
      for (const field of COPY_FIELDS) {
        if (typeof fields[field] === "string") allowed[field] = fields[field].slice(0, 5000);
      }
      if (Object.keys(allowed).length) result.copyOverrides[entryId] = allowed;
    }
  }

  return result;
}

function saveLocalState() {
  try {
    window.localStorage.setItem(STORAGE_KEYS[state.classId], JSON.stringify(state.local));
    return true;
  } catch (error) {
    setStatus("瀏覽器無法寫入 localStorage，這次變更只會保留到頁面關閉。", true);
    return false;
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}

function setStatus(message, isWarning = false) {
  statusMessage.textContent = message;
  statusMessage.classList.toggle("status-warning", isWarning);
}

function isNightLord() {
  return state.classId === "night_lord";
}

function entries() {
  return state.data?.builds || state.data?.skills || [];
}

function entryById(id) {
  return entries().find((entry) => entry.id === id);
}

function validEntryId(id) {
  return Boolean(entryById(id));
}

function copyValue(entry, field) {
  return state.local.copyOverrides[entry.id]?.[field] ?? entry[field] ?? "";
}

function reviewValue(entryId, key) {
  return state.local.reviews[entryId]?.[key];
}

function assetUrl(value) {
  const path = String(value || "");
  if (!path || /^(?:https?:|data:|\/\/|\.|\/)/i.test(path)) return path;
  return `../${path}`;
}

function readUrlState() {
  const params = new URLSearchParams(window.location.search);
  const mode = params.get("mode");
  if (MODES.includes(mode)) state.mode = mode;

  const first = entries()[0]?.id || "";
  const second = entries()[1]?.id || first;
  const requestedEntry = params.get("build");
  const requestedA = params.get("a");
  const requestedB = params.get("b");

  state.selectedId = validEntryId(requestedEntry) ? requestedEntry : first;
  state.focusIds = [
    validEntryId(requestedA) ? requestedA : first,
    validEntryId(requestedB) && requestedB !== state.focusIds[0] ? requestedB : second
  ];
  ensureDistinctFocus(0);
}

function resetViewForData() {
  const first = entries()[0]?.id || "";
  const second = entries()[1]?.id || first;
  state.mode = "single";
  state.selectedId = first;
  state.focusIds = [first, second];
}

function writeUrlState() {
  const params = new URLSearchParams();
  params.set("class", state.classId);
  params.set("mode", state.mode);
  if (state.mode === "single") params.set("build", state.selectedId);
  if (state.mode === "focus") {
    params.set("a", state.focusIds[0]);
    params.set("b", state.focusIds[1]);
  }
  window.history.replaceState(null, "", `${window.location.pathname}?${params.toString()}`);
}

function optionMarkup(selectedId) {
  return entries().map((entry) => (
    `<option value="${escapeAttribute(entry.id)}" ${entry.id === selectedId ? "selected" : ""}>${escapeHtml(entry.name)}</option>`
  )).join("");
}

function renderControls() {
  classSelect.value = state.classId;
  modeSelect.innerHTML = isNightLord()
    ? `<option value="single">單招檢視</option><option value="compare">六招並排</option><option value="focus">雙招聚焦</option>`
    : `<option value="single">單一 Build 檢視</option><option value="compare">並排比較（三套）</option><option value="focus">焦點比較（兩套）</option>`;
  modeSelect.value = state.mode;
  singleBuildControl.querySelector("span").textContent = isNightLord() ? "檢視技能" : "檢視 Build";
  singleBuildSelect.innerHTML = optionMarkup(state.selectedId);
  focusASelect.innerHTML = optionMarkup(state.focusIds[0]);
  focusBSelect.innerHTML = optionMarkup(state.focusIds[1]);
  singleBuildControl.hidden = state.mode !== "single";
  focusBuildControls.hidden = state.mode !== "focus";
}

function renderHeader() {
  const label = CLASS_LABELS[state.classId];
  classEyebrow.textContent = `MAPLEIDLE / ${isNightLord() ? "NIGHT LORD" : "HERO"} REVIEW`;
  pageTitle.textContent = isNightLord() ? "夜使者技能視覺複核／設計頁" : "Hero Build 視覺複核／設計頁";
  pageLede.textContent = isNightLord()
    ? "用六招正式 presentation capture，檢查高速投擲、契約、旋轉、散射、殘影與起爆的差異。"
    : "用現有 capture 的 PNG／WebM，逐一檢查三套流派的節奏、辨識度、持續感與視覺重量。";
  document.title = `${label} VFX 視覺複核／設計頁`;
  buildsTitle.textContent = isNightLord() ? "夜使者六招預覽" : "Hero Build 預覽";
}

function renderObservations() {
  const observations = state.data.observations || entries();
  observationTitle.textContent = state.data.comparisonTitle || (isNightLord() ? "六招視覺語彙" : "比較觀察");
  observationIntro.textContent = state.data.comparisonIntro || (isNightLord()
    ? "先看六招的 silhouette、運動方式與節奏，再用本機 Review 欄位核對實際觀感。"
    : "先確認三套 Build 的設計意圖，再用影片與 review 欄位核對實際觀感。");
  observationGrid.innerHTML = observations.map((entry, index) => `
    <article class="observation-card">
      <span class="observation-label">${isNightLord() ? `技能 0${index + 1}` : `Build ${index + 1}`}</span>
      <h3>${escapeHtml(entry.name)}</h3>
      <p><span class="observation-label">設計目標</span>${escapeHtml(copyValue(entry, "visualGoal"))}</p>
      <p><span class="observation-label">應有節奏</span>${escapeHtml(copyValue(entry, "expectedRhythm"))}</p>
    </article>
  `).join("");
  observationPanel.hidden = observations.length === 0;
}

function selectedEntries() {
  if (state.mode === "compare") return entries();
  if (state.mode === "focus") return state.focusIds.map(entryById).filter(Boolean);
  return [entryById(state.selectedId)].filter(Boolean);
}

function renderBullets(items) {
  return (items || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function selectOptions(selected, includeEmpty = false) {
  const empty = includeEmpty ? `<option value="">尚未評分</option>` : "";
  const options = [1, 2, 3, 4, 5].map((value) => (
    `<option value="${value}" ${Number(selected) === value ? "selected" : ""}>${value} / 5</option>`
  )).join("");
  return empty + options;
}

function metricMarkup(entryId, key, label) {
  const saved = reviewValue(entryId, key);
  const value = saved || 3;
  return `
    <label class="review-field">
      <span>${label}</span>
      <span class="range-line">
        <input type="range" min="1" max="5" step="1" value="${value}" data-review-key="${key}" aria-label="${label}">
        <output class="range-value">${saved ? saved : "未填"}</output>
      </span>
    </label>
  `;
}

function renderMedia(entry) {
  const poster = assetUrl(entry.preview?.poster || entry.poster || "");
  const video = assetUrl(entry.video || "");
  const posterAlt = entry.preview?.alt || `${entry.name} 預覽圖`;
  if (!video && !poster) {
    return `<div class="preview-placeholder"><span>STATIC PREVIEW AREA</span></div>`;
  }
  if (!video) {
    return `<img class="poster-fallback poster-only" src="${escapeAttribute(poster)}" alt="${escapeAttribute(posterAlt)}">`;
  }
  return `
    <video class="build-video" autoplay muted loop playsinline preload="metadata" poster="${escapeAttribute(poster)}">
      <source src="${escapeAttribute(video)}" type="video/webm">
      您的瀏覽器不支援 WebM 影片。
    </video>
    <img class="poster-fallback" src="${escapeAttribute(poster)}" alt="${escapeAttribute(posterAlt)}" hidden>
    <div class="media-status" hidden>影片無法播放，現在顯示 PNG poster。</div>
  `;
}

function renderSkillList(entry) {
  const skills = entry.skills?.length ? entry.skills : [{
    slot: "技能",
    id: entry.id,
    name: entry.name,
    role: entry.identity,
    visualNote: entry.visualGoal
  }];
  return skills.map((skill) => `
    <li class="skill-item">
      <span class="skill-slot">${escapeHtml(skill.slot)}</span>
      <span>
        <span class="skill-name">${escapeHtml(skill.name)}</span>
        <span class="skill-role">${escapeHtml(skill.role)}</span>
        <small class="skill-id">${escapeHtml(skill.id)}</small>
      </span>
      <span class="skill-note">${escapeHtml(skill.visualNote)}</span>
    </li>
  `).join("");
}

function renderCard(entry, index) {
  const review = state.local.reviews[entry.id] || {};
  const fields = [
    ["summary", "摘要"],
    ["visualGoal", "視覺訴求"],
    ["identity", "辨識重點"],
    ["expectedRhythm", "預期節奏"]
  ];
  const typeLabel = isNightLord() ? "Night Lord Skill" : "Hero Build";

  return `
    <article class="build-card" data-build-id="${escapeAttribute(entry.id)}">
      <header class="build-card-header">
        <div>
          <span class="section-kicker">${typeLabel}</span>
          <h3>${escapeHtml(entry.name)}</h3>
          <p>${escapeHtml(entry.preview?.label || "視覺預覽")}</p>
        </div>
        <span class="build-index">0${index + 1}</span>
      </header>

      <div class="media-shell">
        ${renderMedia(entry)}
      </div>

      <div class="card-body">
        <section class="copy-section" aria-label="${escapeAttribute(entry.name)} 文案">
          ${fields.map(([field, label]) => `
            <p class="copy-block" data-copy-field="${field}">
              <strong>${label}</strong>
              <span class="copy-text">${escapeHtml(copyValue(entry, field))}</span>
            </p>
          `).join("")}
          <div class="copy-actions">
            <button class="button button-small" type="button" data-action="edit-copy">編輯文案</button>
            <span class="copy-edit-actions" hidden>
              <button class="button button-small button-primary" type="button" data-action="save-copy">儲存文案</button>
              <button class="button button-small" type="button" data-action="cancel-copy">取消</button>
            </span>
          </div>
        </section>

        <section class="skill-section" aria-labelledby="skills-${escapeAttribute(entry.id)}">
          <h4 id="skills-${escapeAttribute(entry.id)}" class="subheading">技能資訊</h4>
          <ul class="skill-list">${renderSkillList(entry)}</ul>
        </section>

        <section class="details-section" aria-label="${escapeAttribute(entry.name)} 視覺詳情">
          <div class="details-grid">
            <div class="detail-box">
              <span class="copy-label">優勢</span>
              <ul class="bullet-list">${renderBullets(entry.strengths)}</ul>
            </div>
            <div class="detail-box">
              <span class="copy-label">留意事項</span>
              <ul class="bullet-list">${renderBullets(entry.concerns)}</ul>
            </div>
          </div>
        </section>

        <section class="review-panel" aria-label="${escapeAttribute(entry.name)} Review">
          <h4 class="subheading">本機 Review</h4>
          <div class="review-grid">
            <label class="review-field">
              <span>整體評分</span>
              <select data-review-key="overall" aria-label="整體評分">${selectOptions(review.overall, true)}</select>
            </label>
            ${metricMarkup(entry.id, "identity", "識別度")}
            ${metricMarkup(entry.id, "burst", "爆發感")}
            ${metricMarkup(entry.id, "sustain", "持續感")}
            ${metricMarkup(entry.id, "weight", "視覺重量")}
            <label class="review-field review-field-wide">
              <span>備註文字</span>
              <textarea data-review-key="notes" maxlength="5000" placeholder="記下你看到的節奏、辨識度或需要調整的地方……">${escapeHtml(review.notes || "")}</textarea>
            </label>
          </div>
        </section>
      </div>
    </article>
  `;
}

function renderBuildGrid() {
  const visible = selectedEntries();
  buildGrid.className = `build-grid ${state.mode}`;
  if (!visible.length) {
    buildGrid.innerHTML = `<div class="error-state">找不到目前選擇的項目。</div>`;
    return;
  }
  buildGrid.innerHTML = visible.map(renderCard).join("");
  if (state.mode === "single") {
    viewSummary.textContent = `目前檢視：${visible[0].name}`;
  } else if (state.mode === "compare") {
    viewSummary.textContent = isNightLord() ? "六招技能並排檢視" : "三套 Build 並排檢視";
  } else {
    viewSummary.textContent = isNightLord() ? "兩招焦點比較" : "兩套 Build 焦點比較";
  }
  attachMediaFallbacks();
}

function renderChecklist() {
  checklistPanel.hidden = isNightLord();
  if (isNightLord()) {
    checklist.replaceChildren();
    return;
  }
  checklist.innerHTML = CHECKLIST_ITEMS.map((item) => `
    <label class="check-item">
      <input type="checkbox" data-checklist-id="${escapeAttribute(item.id)}" ${state.local.checklist[item.id] ? "checked" : ""}>
      <span>${escapeHtml(item.label)}</span>
    </label>
  `).join("");
}

function renderAll() {
  renderHeader();
  renderControls();
  renderObservations();
  renderBuildGrid();
  renderChecklist();
  app.setAttribute("aria-busy", "false");
}

function attachMediaFallbacks() {
  buildGrid.querySelectorAll(".build-video").forEach((video) => {
    const startPlayback = () => {
      video.muted = true;
      const playback = video.play();
      if (playback && typeof playback.catch === "function") playback.catch(() => {});
    };
    video.addEventListener("loadeddata", startPlayback, { once: true });
    startPlayback();
    video.addEventListener("error", () => {
      const shell = video.closest(".media-shell");
      const fallback = shell.querySelector(".poster-fallback");
      const status = shell.querySelector(".media-status");
      video.hidden = true;
      if (fallback) fallback.hidden = false;
      if (status) status.hidden = false;
    }, { once: true });
  });

  buildGrid.querySelectorAll(".poster-fallback").forEach((image) => {
    image.addEventListener("error", () => {
      const status = image.closest(".media-shell").querySelector(".media-status");
      if (status) {
        status.textContent = "影片與 PNG poster 都無法載入，請檢查素材路徑。";
        status.hidden = false;
      }
    }, { once: true });
  });
}

function reviewFor(entryId) {
  if (!state.local.reviews[entryId]) state.local.reviews[entryId] = {};
  return state.local.reviews[entryId];
}

function handleReviewChange(target) {
  const card = target.closest(".build-card");
  const key = target.dataset.reviewKey;
  if (!card || !key) return;
  const review = reviewFor(card.dataset.buildId);
  if (key === "notes") {
    review[key] = target.value.slice(0, 5000);
  } else {
    const value = Number(target.value);
    if (Number.isInteger(value) && value >= 1 && value <= 5) review[key] = value;
    else delete review[key];
  }
  if (target.matches("input[type=range]")) {
    target.closest(".range-line").querySelector("output").textContent = review[key] || "未填";
  }
  saveLocalState();
}

function editCopy(card) {
  card.querySelectorAll("[data-copy-field]").forEach((block) => {
    const text = block.querySelector(".copy-text");
    text.contentEditable = "true";
    text.spellcheck = true;
  });
  card.querySelector("[data-action=edit-copy]").hidden = true;
  card.querySelector(".copy-edit-actions").hidden = false;
  card.querySelector("[data-copy-field]").querySelector(".copy-text").focus();
}

function saveCopy(card) {
  const entryId = card.dataset.buildId;
  const values = {};
  card.querySelectorAll("[data-copy-field]").forEach((block) => {
    const text = block.querySelector(".copy-text").innerText.trim().slice(0, 5000);
    values[block.dataset.copyField] = text;
  });
  state.local.copyOverrides[entryId] = values;
  saveLocalState();
  renderAll();
  setStatus("文案已儲存到本機。分享網址不會包含這些本機內容，請用匯出 JSON 傳遞。 ");
}

function cancelCopy() {
  renderAll();
}

function ensureDistinctFocus(changed) {
  if (state.focusIds[0] !== state.focusIds[1]) return;
  const replacement = entries().find((entry) => entry.id !== state.focusIds[changed]);
  if (!replacement) return;
  state.focusIds[changed === 0 ? 1 : 0] = replacement.id;
}

function downloadJson(filename, value) {
  const blob = new Blob([JSON.stringify(value, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function exportReview() {
  const exported = {
    schemaVersion: 1,
    classId: state.classId,
    exportedAt: new Date().toISOString(),
    prototype: state.data.prototype,
    source: `${CLASS_LABELS[state.classId]} Review 本機複核頁`,
    reviews: state.local.reviews,
    checklist: state.local.checklist,
    copyOverrides: state.local.copyOverrides,
    view: {
      mode: state.mode,
      selectedId: state.selectedId,
      focusIds: state.focusIds
    }
  };
  const stamp = new Date().toISOString().slice(0, 10);
  downloadJson(`${state.classId}-review-${stamp}.json`, exported);
  setStatus("Review JSON 已匯出。文案與備註可透過這個檔案交給其他人匯入。 ");
}

async function importReview(file) {
  try {
    const parsed = JSON.parse(await file.text());
    if (!parsed || typeof parsed !== "object" || (!parsed.reviews && !parsed.checklist && !parsed.copyOverrides)) {
      throw new Error("格式不包含 Review 資料");
    }
    if (parsed.classId && parsed.classId !== state.classId) {
      throw new Error(`這份檔案屬於${CLASS_LABELS[parsed.classId] || parsed.classId}，請先切換職業`);
    }
    state.local = normaliseLocalState(parsed);
    if (parsed.view && MODES.includes(parsed.view.mode)) state.mode = parsed.view.mode;
    if (validEntryId(parsed.view?.selectedId)) state.selectedId = parsed.view.selectedId;
    if (Array.isArray(parsed.view?.focusIds)) {
      const ids = parsed.view.focusIds.filter(validEntryId).slice(0, 2);
      if (ids.length === 2 && ids[0] !== ids[1]) state.focusIds = ids;
    }
    saveLocalState();
    renderAll();
    writeUrlState();
    setStatus("Review JSON 已匯入並儲存到本機。 ");
  } catch (error) {
    setStatus(`匯入失敗：${error.message || "JSON 格式錯誤"}`, true);
  } finally {
    importFile.value = "";
  }
}

function resetReview() {
  if (!window.confirm(`確定要清除這個瀏覽器中的${CLASS_LABELS[state.classId]} Review、文案修改與備註嗎？`)) return;
  state.local = emptyLocalState();
  saveLocalState();
  renderAll();
  setStatus("本機 Review、文案修改與備註已清除。 ");
}

async function loadData(classId, fromUrl = false) {
  state.classId = classId;
  state.data = null;
  state.local = loadLocalState(classId);
  resetViewForData();
  app.setAttribute("aria-busy", "true");
  try {
    const response = await fetch(DATA_URLS[classId], { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.data = await response.json();
    if (!Array.isArray(state.data.builds || state.data.skills) || entries().length === 0) {
      throw new Error("視覺複核資料格式不正確");
    }
    if (fromUrl) readUrlState();
    renderAll();
    writeUrlState();
    setStatus(`${CLASS_LABELS[state.classId]}資料已載入；本機 Review 與其他職業分開保存。`);
  } catch (error) {
    app.setAttribute("aria-busy", "false");
    buildGrid.innerHTML = `<div class="error-state">${escapeHtml(CLASS_LABELS[classId])} Review 資料載入失敗：${escapeHtml(error.message)}</div>`;
    setStatus("請確認頁面是透過 HTTP 服務開啟，並且 showcase/data 資料存在。", true);
  }
}

classSelect.addEventListener("change", () => {
  saveLocalState();
  loadData(classSelect.value, false);
});

modeSelect.addEventListener("change", () => {
  state.mode = modeSelect.value;
  renderAll();
  writeUrlState();
});

singleBuildSelect.addEventListener("change", () => {
  state.selectedId = singleBuildSelect.value;
  renderAll();
  writeUrlState();
});

focusASelect.addEventListener("change", () => {
  state.focusIds[0] = focusASelect.value;
  ensureDistinctFocus(0);
  renderAll();
  writeUrlState();
});

focusBSelect.addEventListener("change", () => {
  state.focusIds[1] = focusBSelect.value;
  ensureDistinctFocus(1);
  renderAll();
  writeUrlState();
});

buildGrid.addEventListener("input", (event) => {
  if (event.target.dataset.reviewKey) handleReviewChange(event.target);
});

buildGrid.addEventListener("change", (event) => {
  if (event.target.dataset.reviewKey) handleReviewChange(event.target);
});

buildGrid.addEventListener("click", (event) => {
  const action = event.target.closest("[data-action]")?.dataset.action;
  const card = event.target.closest(".build-card");
  if (!action || !card) return;
  if (action === "edit-copy") editCopy(card);
  if (action === "save-copy") saveCopy(card);
  if (action === "cancel-copy") cancelCopy();
});

checklist.addEventListener("change", (event) => {
  const id = event.target.dataset.checklistId;
  if (!id) return;
  state.local.checklist[id] = event.target.checked;
  saveLocalState();
});

document.querySelector("#export-review").addEventListener("click", exportReview);
document.querySelector("#import-review").addEventListener("click", () => importFile.click());
document.querySelector("#reset-review").addEventListener("click", resetReview);
importFile.addEventListener("change", () => {
  if (importFile.files?.[0]) importReview(importFile.files[0]);
});

const initialParams = new URLSearchParams(window.location.search);
const initialClass = ["hero", "night_lord"].includes(initialParams.get("class"))
  ? initialParams.get("class")
  : "hero";
loadData(initialClass, true);
