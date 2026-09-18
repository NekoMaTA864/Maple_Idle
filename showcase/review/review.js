const DATA_URL = "../data/hero_review.json";
const STORAGE_KEY = "mapleIdle.heroReview.v1";
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
const modeSelect = document.querySelector("#mode-select");
const singleBuildControl = document.querySelector("#single-build-control");
const singleBuildSelect = document.querySelector("#single-build-select");
const focusBuildControls = document.querySelector("#focus-build-controls");
const focusASelect = document.querySelector("#focus-a-select");
const focusBSelect = document.querySelector("#focus-b-select");
const buildGrid = document.querySelector("#build-grid");
const observationGrid = document.querySelector("#observation-grid");
const checklist = document.querySelector("#checklist");
const statusMessage = document.querySelector("#status-message");
const viewSummary = document.querySelector("#view-summary");
const importFile = document.querySelector("#import-file");

const state = {
  data: null,
  local: loadLocalState(),
  mode: "single",
  selectedId: "",
  focusIds: ["", ""]
};

function emptyLocalState() {
  return { version: 1, reviews: {}, checklist: {}, copyOverrides: {} };
}

function loadLocalState() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? normaliseLocalState(JSON.parse(raw)) : emptyLocalState();
  } catch (error) {
    return emptyLocalState();
  }
}

function normaliseLocalState(value) {
  const source = value && typeof value === "object" ? value : {};
  const result = emptyLocalState();
  result.version = 1;

  if (source.reviews && typeof source.reviews === "object") {
    for (const [buildId, review] of Object.entries(source.reviews)) {
      if (!review || typeof review !== "object") continue;
      result.reviews[buildId] = {};
      for (const key of REVIEW_KEYS) {
        if (key === "notes") {
          if (typeof review[key] === "string") result.reviews[buildId][key] = review[key].slice(0, 5000);
          continue;
        }
        const number = Number(review[key]);
        if (Number.isInteger(number) && number >= 1 && number <= 5) {
          result.reviews[buildId][key] = number;
        }
      }
    }
  }

  if (source.checklist && typeof source.checklist === "object") {
    for (const item of CHECKLIST_ITEMS) {
      if (source.checklist[item.id] === true) result.checklist[item.id] = true;
    }
  }

  if (source.copyOverrides && typeof source.copyOverrides === "object") {
    for (const [buildId, fields] of Object.entries(source.copyOverrides)) {
      if (!fields || typeof fields !== "object") continue;
      const allowed = {};
      for (const field of COPY_FIELDS) {
        if (typeof fields[field] === "string") allowed[field] = fields[field].slice(0, 5000);
      }
      if (Object.keys(allowed).length) result.copyOverrides[buildId] = allowed;
    }
  }

  return result;
}

function saveLocalState() {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state.local));
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

function builds() {
  return state.data?.builds || [];
}

function buildById(id) {
  return builds().find((build) => build.id === id);
}

function validBuildId(id) {
  return Boolean(buildById(id));
}

function copyValue(build, field) {
  return state.local.copyOverrides[build.id]?.[field] ?? build[field] ?? "";
}

function reviewValue(buildId, key) {
  return state.local.reviews[buildId]?.[key];
}

function readUrlState() {
  const params = new URLSearchParams(window.location.search);
  const mode = params.get("mode");
  if (MODES.includes(mode)) state.mode = mode;

  const first = builds()[0]?.id || "";
  const second = builds()[1]?.id || first;
  const requestedBuild = params.get("build");
  const requestedA = params.get("a");
  const requestedB = params.get("b");

  state.selectedId = validBuildId(requestedBuild) ? requestedBuild : first;
  state.focusIds = [
    validBuildId(requestedA) ? requestedA : first,
    validBuildId(requestedB) && requestedB !== state.focusIds[0] ? requestedB : second
  ];
  if (state.focusIds[0] === state.focusIds[1] && builds().length > 1) {
    state.focusIds[1] = builds().find((build) => build.id !== state.focusIds[0])?.id || second;
  }
}

function writeUrlState() {
  const params = new URLSearchParams();
  params.set("mode", state.mode);
  if (state.mode === "single") params.set("build", state.selectedId);
  if (state.mode === "focus") {
    params.set("a", state.focusIds[0]);
    params.set("b", state.focusIds[1]);
  }
  const query = params.toString();
  window.history.replaceState(null, "", `${window.location.pathname}?${query}`);
}

function optionMarkup(selectedId) {
  return builds().map((build) => (
    `<option value="${escapeAttribute(build.id)}" ${build.id === selectedId ? "selected" : ""}>${escapeHtml(build.name)}</option>`
  )).join("");
}

function renderControls() {
  modeSelect.value = state.mode;
  singleBuildSelect.innerHTML = optionMarkup(state.selectedId);
  focusASelect.innerHTML = optionMarkup(state.focusIds[0]);
  focusBSelect.innerHTML = optionMarkup(state.focusIds[1]);
  singleBuildControl.hidden = state.mode !== "single";
  focusBuildControls.hidden = state.mode !== "focus";
}

function renderObservations() {
  observationGrid.innerHTML = builds().map((build, index) => `
    <article class="observation-card">
      <span class="observation-label">Build ${index + 1}</span>
      <h3>${escapeHtml(build.name)}</h3>
      <p><span class="observation-label">設計目標</span>${escapeHtml(copyValue(build, "visualGoal"))}</p>
      <p><span class="observation-label">應有節奏</span>${escapeHtml(copyValue(build, "expectedRhythm"))}</p>
    </article>
  `).join("");
}

function selectedBuilds() {
  if (state.mode === "compare") return builds();
  if (state.mode === "focus") return state.focusIds.map(buildById).filter(Boolean);
  return [buildById(state.selectedId)].filter(Boolean);
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

function metricMarkup(buildId, key, label) {
  const saved = reviewValue(buildId, key);
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

function renderCard(build, index) {
  const review = state.local.reviews[build.id] || {};
  const poster = build.preview?.poster || "";
  const posterAlt = build.preview?.alt || `${build.name} 預覽圖`;
  const fields = [
    ["summary", "摘要"],
    ["visualGoal", "視覺訴求"],
    ["identity", "辨識重點"],
    ["expectedRhythm", "預期節奏"]
  ];

  return `
    <article class="build-card" data-build-id="${escapeAttribute(build.id)}">
      <header class="build-card-header">
        <div>
          <span class="section-kicker">Hero Build</span>
          <h3>${escapeHtml(build.name)}</h3>
          <p>${escapeHtml(build.preview?.label || "視覺預覽")}</p>
        </div>
        <span class="build-index">0${index + 1}</span>
      </header>

      <div class="media-shell">
        <video class="build-video" autoplay muted loop playsinline preload="metadata" poster="${escapeAttribute(poster)}">
          <source src="${escapeAttribute(build.video || "")}" type="video/webm">
          您的瀏覽器不支援 WebM 影片。
        </video>
        <img class="poster-fallback" src="${escapeAttribute(poster)}" alt="${escapeAttribute(posterAlt)}" hidden>
        <div class="media-status" hidden>影片無法播放，現在顯示 PNG poster。</div>
      </div>

      <div class="card-body">
        <section class="copy-section" aria-label="${escapeAttribute(build.name)} 文案">
          ${fields.map(([field, label]) => `
            <p class="copy-block" data-copy-field="${field}">
              <strong>${label}</strong>
              <span class="copy-text">${escapeHtml(copyValue(build, field))}</span>
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

        <section class="skill-section" aria-labelledby="skills-${escapeAttribute(build.id)}">
          <h4 id="skills-${escapeAttribute(build.id)}" class="subheading">技能組</h4>
          <ul class="skill-list">
            ${(build.skills || []).map((skill) => `
              <li class="skill-item">
                <span class="skill-slot">${escapeHtml(skill.slot)}</span>
                <span>
                  <span class="skill-name">${escapeHtml(skill.name)}</span>
                  <span class="skill-role">${escapeHtml(skill.role)}</span>
                  <small class="skill-id">${escapeHtml(skill.id)}</small>
                </span>
                <span class="skill-note">${escapeHtml(skill.visualNote)}</span>
              </li>
            `).join("")}
          </ul>
        </section>

        <section class="details-section" aria-label="${escapeAttribute(build.name)} 視覺詳情">
          <div class="details-grid">
            <div class="detail-box">
              <span class="copy-label">優勢</span>
              <ul class="bullet-list">${renderBullets(build.strengths)}</ul>
            </div>
            <div class="detail-box">
              <span class="copy-label">留意事項</span>
              <ul class="bullet-list">${renderBullets(build.concerns)}</ul>
            </div>
          </div>
        </section>

        <section class="review-panel" aria-label="${escapeAttribute(build.name)} Review">
          <h4 class="subheading">本機 Review</h4>
          <div class="review-grid">
            <label class="review-field">
              <span>整體評分</span>
              <select data-review-key="overall" aria-label="整體評分">${selectOptions(review.overall, true)}</select>
            </label>
            ${metricMarkup(build.id, "identity", "識別度")}
            ${metricMarkup(build.id, "burst", "爆發感")}
            ${metricMarkup(build.id, "sustain", "持續感")}
            ${metricMarkup(build.id, "weight", "視覺重量")}
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
  const visible = selectedBuilds();
  buildGrid.className = `build-grid ${state.mode}`;
  if (!visible.length) {
    buildGrid.innerHTML = `<div class="error-state">找不到目前選擇的 Build。</div>`;
    return;
  }
  buildGrid.innerHTML = visible.map(renderCard).join("");
  viewSummary.textContent = state.mode === "single"
    ? `目前檢視：${visible[0].name}`
    : state.mode === "compare" ? "三套 Build 並排檢視" : "兩套 Build 焦點比較";
  attachMediaFallbacks();
}

function renderChecklist() {
  checklist.innerHTML = CHECKLIST_ITEMS.map((item) => `
    <label class="check-item">
      <input type="checkbox" data-checklist-id="${escapeAttribute(item.id)}" ${state.local.checklist[item.id] ? "checked" : ""}>
      <span>${escapeHtml(item.label)}</span>
    </label>
  `).join("");
}

function renderAll() {
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
      fallback.hidden = false;
      status.hidden = false;
    }, { once: true });
  });

  buildGrid.querySelectorAll(".poster-fallback").forEach((image) => {
    image.addEventListener("error", () => {
      const status = image.closest(".media-shell").querySelector(".media-status");
      status.textContent = "影片與 PNG poster 都無法載入，請檢查素材路徑。";
      status.hidden = false;
    }, { once: true });
  });
}

function reviewFor(buildId) {
  if (!state.local.reviews[buildId]) state.local.reviews[buildId] = {};
  return state.local.reviews[buildId];
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
  const buildId = card.dataset.buildId;
  const values = {};
  card.querySelectorAll("[data-copy-field]").forEach((block) => {
    const text = block.querySelector(".copy-text").innerText.trim().slice(0, 5000);
    values[block.dataset.copyField] = text;
  });
  state.local.copyOverrides[buildId] = values;
  saveLocalState();
  renderAll();
  setStatus("文案已儲存到本機。分享網址不會包含這些本機內容，請用匯出 JSON 傳遞。 ");
}

function cancelCopy() {
  renderAll();
}

function ensureDistinctFocus(changed) {
  if (state.focusIds[0] !== state.focusIds[1]) return;
  const replacement = builds().find((build) => build.id !== state.focusIds[changed]);
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
    exportedAt: new Date().toISOString(),
    prototype: state.data.prototype,
    source: "Hero Review 本機複核頁",
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
  downloadJson(`hero-review-${stamp}.json`, exported);
  setStatus("Review JSON 已匯出。文案與備註可透過這個檔案交給其他人匯入。 ");
}

async function importReview(file) {
  try {
    const parsed = JSON.parse(await file.text());
    if (!parsed || typeof parsed !== "object" || (!parsed.reviews && !parsed.checklist && !parsed.copyOverrides)) {
      throw new Error("格式不包含 Review 資料");
    }
    state.local = normaliseLocalState(parsed);
    if (parsed.view && MODES.includes(parsed.view.mode)) state.mode = parsed.view.mode;
    if (validBuildId(parsed.view?.selectedId)) state.selectedId = parsed.view.selectedId;
    if (Array.isArray(parsed.view?.focusIds)) {
      const ids = parsed.view.focusIds.filter(validBuildId).slice(0, 2);
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
  if (!window.confirm("確定要清除這個瀏覽器中的 Hero Review、文案修改與 checklist 嗎？")) return;
  state.local = emptyLocalState();
  saveLocalState();
  renderAll();
  setStatus("本機 Review、文案修改與 checklist 已清除。 ");
}

async function loadData() {
  try {
    const response = await fetch(DATA_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.data = await response.json();
    if (!Array.isArray(state.data.builds) || state.data.builds.length !== 3) {
      throw new Error("Hero Build 資料數量不正確");
    }
    readUrlState();
    renderAll();
    writeUrlState();
  } catch (error) {
    app.setAttribute("aria-busy", "false");
    buildGrid.innerHTML = `<div class="error-state">Hero Review 資料載入失敗：${escapeHtml(error.message)}</div>`;
    setStatus("請確認頁面是透過 HTTP 服務開啟，並且 data/hero_review.json 存在。", true);
  }
}

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

loadData();
