/* ═══════════════════════════════════════════════════
   小七 · Living World ZERO UI
   世界驱动（LifeLoop -> Avatar）+ 小七手机 + 心灵观察站
   房间纯视觉，无交互；聊天只在手机；信息只在 Observer。
   ═══════════════════════════════════════════════════ */

import Avatar2D from "./avatar/avatar_2d.js";

const avatar = new Avatar2D();

const bodyEl = document.body;
const avatarMount = document.getElementById("avatar-mount");

const phoneEntry = document.getElementById("phone-entry");
const phoneEl = document.getElementById("phone");
const phoneMessagesEl = document.getElementById("phone-messages");
const phoneInput = document.getElementById("phone-input");
const sendBtn = document.getElementById("send-btn");
const phoneStatusEl = document.getElementById("phone-status");
const phoneClose = document.getElementById("phone-close");

const observerEntry = document.getElementById("observer-entry");
const observerEl = document.getElementById("observer");
const observerContent = document.getElementById("observer-content");
const observerClose = document.getElementById("observer-close");

/* ─────────── 设置（localStorage，Observer 面板修改） ─────────── */
const SETTINGS_KEY = "xiaoqi_room_settings";
const defaultSettings = {
  name: "小七",
  user_name: "主人",
  allow_proactive: true,
  night_mode: false,
  sound: false,
};
let settings = { ...defaultSettings };
try {
  settings = { ...defaultSettings, ...JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}") };
} catch { /* ignore */ }

function saveSettings() {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
}

/* ─────────── 状态 → 表现（LifeLoop 驱动，非用户点击） ─────────── */

const ACTIVITY_AVATAR = {
  sleep: "sleeping",
  pre_sleep: "relaxing",
  morning_prep: "idle",
  commute: "idle",
  morning_clinic: "idle",
  afternoon_clinic: "idle",
  commute_grocery: "idle",
  lunch_break: "relaxing",
  cooking_dinner: "idle",
  home_leisure: "relaxing",
  home_rest: "relaxing",
};

const ACTIVITY_POSITION = {
  sleep: "bed",
  pre_sleep: "sofa",
  morning_prep: "center",
  commute: "window",
  lunch_break: "sofa",
  cooking_dinner: "center",
  home_leisure: "sofa",
  home_rest: "sofa",
};

const EMOTION_CLASS = {
  happy: "happy",
  excited: "excited",
  calm: "idle",
  lonely: "sad",
  anxious: "think",
  angry: "angry",
};

function getPeriodClass(timeStr) {
  if (!timeStr) return "day";
  const hour = new Date(timeStr).getHours();
  if (hour >= 5 && hour < 8) return "morning";
  if (hour >= 8 && hour < 17) return "day";
  if (hour >= 17 && hour < 19) return "evening";
  if (hour >= 19 && hour < 23) return "night";
  return "deep-night";
}

function applyWorldState(lifeState) {
  if (!lifeState) return;

  let period = getPeriodClass(lifeState.current_time);
  if (settings.night_mode && period === "day") period = "night";
  bodyEl.className = period;

  // 情绪 → 表情（Avatar2D）
  avatar.setState(EMOTION_CLASS[lifeState.dominant_emotion] || "idle");

  // 活动 → 动作 + 位置（LifeLoop 决定，小七自己生活）
  const activity = lifeState.current_activity || "";
  const state = ACTIVITY_AVATAR[activity];
  if (state) avatar.play(state);
  const pos = ACTIVITY_POSITION[activity];
  if (pos) avatar.moveTo(pos);

  // 疲劳 → 动作变慢
  if ((lifeState.energy ?? 1) < 0.35) avatar.setState("tired");
}

/* ─────────── 小七手机（聊天） ─────────── */

const HISTORY_KEY = "xiaoqi_phone_history";
function loadHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]"); }
  catch { return []; }
}
function saveHistory(h) { localStorage.setItem(HISTORY_KEY, JSON.stringify(h)); }
function formatTime(iso) {
  try { return new Date(iso).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }); }
  catch { return ""; }
}

function renderPhoneMessage(msg) {
  const wrapper = document.createElement("div");
  wrapper.className = `phone-msg ${msg.role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = msg.text;
  wrapper.appendChild(bubble);
  const meta = document.createElement("div");
  meta.className = "meta";
  meta.innerHTML = `<span>${formatTime(msg.time)}</span>` + (msg.role === "user" ? '<span class="read">已读 ✓</span>' : "");
  wrapper.appendChild(meta);
  phoneMessagesEl.appendChild(wrapper);
  phoneMessagesEl.scrollTop = phoneMessagesEl.scrollHeight;
}

function renderHistory() {
  phoneMessagesEl.innerHTML = "";
  loadHistory().forEach(renderPhoneMessage);
}

function appendChat(role, text, time) {
  const history = loadHistory();
  history.push({ role, text, time: time || new Date().toISOString() });
  if (history.length > 200) history.splice(0, history.length - 200);
  saveHistory(history);
  renderPhoneMessage({ role, text, time: time || new Date().toISOString() });
}

/* ─────────── 主动消息 → 手机未读红点 ─────────── */

function notifyProactive(content) {
  phoneEntry.querySelector(".entry-dot").classList.add("unread");
  // 主动消息只进入手机，不在房间气泡显示
  if (phoneEl.classList.contains("hidden")) return;
  appendChat("assistant", content, new Date().toISOString());
}

/* ─────────── API ─────────── */

async function loadStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    applyWorldState(data.life_state);
    phoneStatusEl.textContent = "在线";
  } catch { phoneStatusEl.textContent = "离线"; }
}

async function pollProactive() {
  if (!settings.allow_proactive) return;
  try {
    const res = await fetch("/api/proactive");
    if (!res.ok) return;
    const data = await res.json();
    (data.messages || []).forEach((msg) => {
      if (msg.content) notifyProactive(msg.content);
    });
  } catch { /* 静默 */ }
}

async function sendMessage(text) {
  sendBtn.disabled = true;
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    appendChat("assistant", data.reply, new Date().toISOString());
    if (data.life_state) applyWorldState(data.life_state);
    phoneStatusEl.textContent = "在线";
  } catch (error) {
    appendChat("assistant", `（小七暂时没回应：${error.message}）`);
  } finally {
    sendBtn.disabled = false;
    phoneInput.focus();
  }
}

/* ─────────── Observer（信息 / 设置） ─────────── */

let observerData = null;

async function loadObserver() {
  try {
    const res = await fetch("/api/observer");
    if (!res.ok) return;
    observerData = await res.json();
    renderObserverView("emotion");
  } catch {
    observerContent.innerHTML = '<div class="obs-empty">暂时无法连接小七的心灵</div>';
  }
}

function pct(v) { return Math.round((v ?? 0) * 100); }
function bar(v, label) {
  return `<div class="obs-row"><span>${label}</span><b>${pct(v)}%</b></div><div class="obs-bar"><i style="width:${pct(v)}%"></i></div>`;
}

const MOOD_LABEL = { happy: "开心", calm: "平静", lonely: "孤独", excited: "兴奋", anxious: "焦虑", angry: "生气" };
const NEURO_LABEL = { dopamine: "多巴胺", serotonin: "血清素", oxytocin: "催产素", cortisol: "皮质醇", endorphin: "内啡肽", noradrenaline: "去甲肾上腺素" };
const TYPE_LABEL = { canonical: "真实记忆", interaction: "互动", virtual_life: "生活", episodic: "情景", semantic: "事实", relationship: "关系", diary: "日记" };

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function renderObserverView(view) {
  const d = observerData;
  let html = "";

  if (view === "emotion" && d) {
    html += `<div class="obs-card"><h4>💗 当前情绪 · ${MOOD_LABEL[d.emotion.dominant] || d.emotion.dominant}</h4>`;
    for (const [k, v] of Object.entries(d.emotion.current)) html += bar(v, MOOD_LABEL[k] || k);
    html += "</div>";
    html += `<div class="obs-card"><h4>🧪 神经化学</h4>`;
    for (const [k, v] of Object.entries(d.neurochemical)) html += bar(v, NEURO_LABEL[k] || k);
    html += "</div>";
  }

  if (view === "relation" && d) {
    const r = d.relationship;
    html += `<div class="obs-card"><h4>❤️ 与小七的关系</h4>`;
    html += bar(r.trust, "信任");
    html += bar(r.attachment, "依恋");
    html += bar(r.familiarity, "熟悉");
    html += bar(r.shared_experience, "共同经历");
    html += `<div class="obs-row"><span>阶段</span><b>${r.stage ?? "陌生"}</b></div>`;
    html += `<div class="obs-row"><span>互动次数</span><b>${r.interaction_count ?? 0}</b></div>`;
    html += "</div>";
  }

  if (view === "diary" && d) {
    if (!d.diaries.length) {
      html = '<div class="obs-empty">小七还没有写下日记</div>';
    } else {
      html = d.diaries.map((e) =>
        `<div class="obs-diary"><div class="date">📖 ${e.date} · ${(e.mood_tags || []).join(" / ") || "平静"}</div><div>${escapeHtml(e.content)}</div></div>`
      ).join("");
    }
  }

  if (view === "memory" && d) {
    if (!d.memories.length) {
      html = '<div class="obs-empty">还没有共同的回忆</div>';
    } else {
      html = d.memories.map((m) =>
        `<div class="obs-memory"><span class="tag">${TYPE_LABEL[m.type] || m.type}</span><div>${escapeHtml(m.content)}</div></div>`
      ).join("");
    }
  }

  if (view === "schedule" && d) {
    const s = d.schedule;
    html += `<div class="obs-card"><h4>📅 她的日程</h4>`;
    html += `<div class="obs-row"><span>当前</span><b>${s.current_activity || "—"}</b></div>`;
    html += "</div>";
    html += (s.today || []).map((slot) =>
      `<div class="obs-row"><span>${slot.start} - ${slot.end}</span><b>${slot.name}</b></div>`
    ).join("");
  }

  if (view === "settings") {
    html = `<div class="obs-card"><h4>⚙️ 设置</h4></div>`;
    html += `<div class="obs-card settings">`;
    html += `<label>小七名字<input id="set-name" type="text" value="${escapeHtml(settings.name)}"></label>`;
    html += `<label>用户称呼<input id="set-user-name" type="text" value="${escapeHtml(settings.user_name)}"></label>`;
    html += `<label class="switch"><span>允许主动消息</span><input id="set-proactive" type="checkbox" ${settings.allow_proactive ? "checked" : ""}></label>`;
    html += `<label class="switch"><span>夜间模式</span><input id="set-night" type="checkbox" ${settings.night_mode ? "checked" : ""}></label>`;
    html += `<label class="switch"><span>音效</span><input id="set-sound" type="checkbox" ${settings.sound ? "checked" : ""}></label>`;
    html += `<p class="settings-note">模拟速度：<b id="set-speed">-</b> 分钟/秒</p>`;
    html += `<p class="settings-note voice-note">🎤 语音功能即将接入（WebRTC / VAD / Whisper / TTS）</p>`;
    html += `</div>`;
  }

  observerContent.innerHTML = html;
  bindSettings();
}

function bindSettings() {
  const bind = (id, key, type) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener(type === "checkbox" ? "change" : "change", () => {
      settings[key] = type === "checkbox" ? el.checked : el.value.trim() || settings[key];
      saveSettings();
      applySettings();
    });
  };
  bind("set-name", "name", "text");
  bind("set-user-name", "user_name", "text");
  bind("set-proactive", "allow_proactive", "checkbox");
  bind("set-night", "night_mode", "checkbox");
  bind("set-sound", "sound", "checkbox");
}

async function loadSettingsBackend() {
  try {
    const res = await fetch("/api/settings");
    const d = await res.json();
    const el = document.getElementById("set-speed");
    if (el) el.textContent = d.simulation_minutes_per_real_second ?? "-";
  } catch { /* 忽略 */ }
}

function applySettings() {
  bodyEl.classList.toggle("night-mode", settings.night_mode);
}

/* ─────────── 入口：极简 / 自动隐藏 ─────────── */

function revealUi() {
  bodyEl.classList.add("reveal-ui");
  clearTimeout(revealUi._t);
  revealUi._t = setTimeout(() => bodyEl.classList.remove("reveal-ui"), 2500);
}
document.addEventListener("mousemove", (e) => {
  if (e.clientX > innerWidth - 60 || e.clientX < 60 || e.clientY > innerHeight - 60) revealUi();
});

phoneEntry.addEventListener("click", () => {
  phoneEl.classList.remove("hidden");
  phoneEntry.querySelector(".entry-dot").classList.remove("unread");
  renderHistory();
  phoneInput.focus();
});
phoneClose.addEventListener("click", () => phoneEl.classList.add("hidden"));
phoneEl.addEventListener("click", (e) => { if (e.target === phoneEl) phoneEl.classList.add("hidden"); });

observerEntry.addEventListener("click", () => {
  observerEl.classList.remove("hidden");
  loadObserver();
});
observerClose.addEventListener("click", () => observerEl.classList.add("hidden"));
observerEl.addEventListener("click", (e) => { if (e.target === observerEl) observerEl.classList.add("hidden"); });

document.querySelectorAll(".observer-nav button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".observer-nav button").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    renderObserverView(btn.dataset.view);
    if (btn.dataset.view === "settings") loadSettingsBackend();
  });
});

/* 手机聊天发送 */
function submitMessage() {
  const text = phoneInput.value.trim();
  if (!text) return;
  appendChat("user", text, new Date().toISOString());
  phoneInput.value = "";
  sendMessage(text);
}
sendBtn.addEventListener("click", submitMessage);
phoneInput.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); submitMessage(); } });

/* ─────────── 启动 ─────────── */

avatar.init(avatarMount);
applySettings();
renderHistory();
loadStatus();

setInterval(loadStatus, 5000);
setInterval(pollProactive, 6000);
