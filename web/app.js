/* ═══════════════════════════════════════════════════
   小七 · 虚拟卧室 前端逻辑
   房间驱动 / 物件交互 / 气泡对话 / 主动行为 / HUD / 设置
   ═══════════════════════════════════════════════════ */

import AvatarAdapter from "./avatar/avatar_adapter.js";
import Avatar2D from "./avatar/avatar_2d.js";

/* 选择 2D 实现；未来切 avatar_vrm.js */
const avatar = new Avatar2D();

/* ─────────── 元素 ─────────── */
const bodyEl = document.body;
const roomEl = document.getElementById("room");
const avatarMount = document.getElementById("avatar-mount");
const interactTip = document.getElementById("interact-tip");

const hudEl = document.getElementById("hud");
const hudEmotion = document.getElementById("hud-emotion");
const hudEnergy = document.getElementById("hud-energy");
const hudFatigue = document.getElementById("hud-fatigue");
const hudActivity = document.getElementById("hud-activity");

const chatBtn = document.getElementById("chat-btn");
const relationBtn = document.getElementById("relation-btn");
const scheduleBtn = document.getElementById("schedule-btn");
const settingsBtn = document.getElementById("settings-btn");
const voiceBtn = document.getElementById("voice-btn");

const chatDrawer = document.getElementById("chat-drawer");
const chatHistory = document.getElementById("chat-history");
const chatInput = document.getElementById("chat-input");
const chatSend = document.getElementById("chat-send");
const chatClose = document.getElementById("chat-close");

const relationPanel = document.getElementById("relation-panel");
const relationContent = document.getElementById("relation-content");
const relationClose = document.getElementById("relation-close");

const schedulePanel = document.getElementById("schedule-panel");
const scheduleContent = document.getElementById("schedule-content");
const scheduleClose = document.getElementById("schedule-close");

const settingsPanel = document.getElementById("settings-panel");
const settingsClose = document.getElementById("settings-close");
const hudToggle = document.getElementById("hud-toggle");
const setSpeed = document.getElementById("set-speed");

/* ─────────── 设置（localStorage） ─────────── */
const SETTINGS_KEY = "xiaoqi_room_settings";

const defaultSettings = {
  name: "小七",
  user_name: "主人",
  show_hud: true,
  allow_proactive: true,
  night_mode: false,
  sound: false,
};

function loadSettings() {
  try {
    return { ...defaultSettings, ...JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}") };
  } catch {
    return { ...defaultSettings };
  }
}
const settings = loadSettings();

function saveSettings() {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
}

function applySettings() {
  document.getElementById("set-name").value = settings.name;
  document.getElementById("set-user-name").value = settings.user_name;
  document.getElementById("set-hud").checked = settings.show_hud;
  document.getElementById("set-proactive").checked = settings.allow_proactive;
  document.getElementById("set-night").checked = settings.night_mode;
  document.getElementById("set-sound").checked = settings.sound;

  hudEl.classList.toggle("hidden", !settings.show_hud);
  bodyEl.classList.toggle("night-mode", settings.night_mode);
}

/* ─────────── 状态 → 表现映射 ─────────── */

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

  const activity = lifeState.current_activity || "";

  avatar.setState(
    EMOTION_CLASS[lifeState.dominant_emotion] || "idle"
  );

  const state = ACTIVITY_AVATAR[activity];
  if (state) avatar.play(state);

  const pos = ACTIVITY_POSITION[activity];
  if (pos) avatar.moveTo(pos);

  const energy = lifeState.energy ?? 1;
  if (energy < 0.35) avatar.setState("tired");

  hudEmotion.textContent =
    { happy: "开心", calm: "平静", lonely: "孤独", excited: "兴奋", anxious: "焦虑", angry: "生气" }[lifeState.dominant_emotion]
    || lifeState.dominant_emotion || "-";
  hudEnergy.textContent = `${Math.round((energy ?? 0) * 100)}%`;
  hudFatigue.textContent = `${Math.round((lifeState.fatigue ?? 0) * 100)}%`;
  hudActivity.textContent = lifeState.current_activity || "-";
}

/* ─────────── 物件交互 → /api/action ─────────── */

function showTip(text) {
  interactTip.textContent = text;
  interactTip.classList.remove("hidden");
  clearTimeout(showTip._timer);
  showTip._timer = setTimeout(() => interactTip.classList.add("hidden"), 2600);
}

async function sendAction(name, target) {
  try {
    const res = await fetch("/api/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: name, target }),
    });
    const data = await res.json();

    if (target && target !== "lamp") {
      avatar.moveTo(target);
      avatar.play(data.behavior);
    }
    return data;
  } catch {
    return null;
  }
}

async function clickObject(target) {
  const labels = {
    bed: "让她去休息",
    desk: "让她去阅读",
    sofa: "让她去放松",
    window: "窗外",
    lamp: "台灯",
    xiaoqi: "小七",
  };

  if (target === "window") {
    showTip("窗外 · 时间与天气会随时间变化");
    return;
  }

  if (target === "lamp") {
    const night = bodyEl.classList.contains("night") || bodyEl.classList.contains("deep-night");
    showTip(night ? "台灯已关闭" : "台灯已打开");
    return;
  }

  await sendAction("move_to", target);
  showTip(`${labels[target]} · ${behText(target)}`);
}

function behText(target) {
  return {
    bed: "休息中", desk: "阅读中", sofa: "放松中",
  }[target] || "";
}

document.querySelectorAll(".obj[data-target]").forEach((el) => {
  el.addEventListener("click", () => clickObject(el.dataset.target));
});

avatarMount.addEventListener("click", async () => {
  await sendAction("interact", "xiaoqi");
  showTip("小七：来啦，怎么了？");
});

roomEl.addEventListener("click", (event) => {
  if (!event.target.closest(".obj") && !event.target.closest("#avatar-mount")) {
    avatar.moveTo("center");
  }
});

/* ─────────── 气泡对话 ─────────── */

const HISTORY_KEY = "xiaoqi_room_history";

function loadHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]"); }
  catch { return []; }
}
function saveHistory(h) { localStorage.setItem(HISTORY_KEY, JSON.stringify(h)); }

function formatTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  } catch { return ""; }
}

function renderDrawerMessage(msg) {
  const wrapper = document.createElement("div");
  wrapper.className = `chat-msg ${msg.role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = msg.text;
  wrapper.appendChild(bubble);
  const meta = document.createElement("div");
  meta.className = "meta";
  meta.innerHTML = `<span>${formatTime(msg.time)}</span>` + (msg.role === "user" ? '<span class="read">已读 ✓</span>' : "");
  wrapper.appendChild(meta);
  chatHistory.appendChild(wrapper);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

function renderHistory() {
  chatHistory.innerHTML = "";
  loadHistory().forEach(renderDrawerMessage);
}

function appendMessage(role, text, time) {
  const history = loadHistory();
  history.push({ role, text, time: time || new Date().toISOString() });
  if (history.length > 200) history.splice(0, history.length - 200);
  saveHistory(history);
  renderDrawerMessage({ role, text, time: time || new Date().toISOString() });
}

/* ─────────── 小七说话（气泡 + 抽屉） ─────────── */

function xiaoqiSpeak(text) {
  avatar.talk();
  avatar.showBubble(text);
  appendMessage("assistant", text, new Date().toISOString());
  setTimeout(() => { avatar.stopTalking(); }, Math.min(text.length * 120, 6000));
  setTimeout(() => avatar.hideBubble(), Math.min(text.length * 120, 6000) + 2500);
}

/* ─────────── 主动行为 ─────────── */

async function pollProactive() {
  if (!settings.allow_proactive) return;
  try {
    const res = await fetch("/api/proactive");
    if (!res.ok) return;
    const data = await res.json();
    (data.messages || []).forEach((msg) => {
      if (msg.content) {
        avatar.setState("proactive");
        setTimeout(() => xiaoqiSpeak(msg.content), 500);
      }
    });
  } catch { /* 静默 */ }
}

/* ─────────── 发送消息 ─────────── */

async function sendMessage(text) {
  chatSend.disabled = true;
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    xiaoqiSpeak(data.reply);
    if (data.life_state) applyWorldState(data.life_state);
  } catch (error) {
    xiaoqiSpeak(`（小七暂时没回应：${error.message}）`);
  } finally {
    chatSend.disabled = false;
    chatInput.focus();
  }
}

function submitChat() {
  const text = chatInput.value.trim();
  if (!text) return;
  appendMessage("user", text, new Date().toISOString());
  chatInput.value = "";
  sendMessage(text);
}

/* ─────────── 面板数据（真实 API） ─────────── */

function pct(v) { return Math.round((v ?? 0) * 100); }
function bar(v, label) {
  return `<div class="obs-row"><span>${label}</span><b>${pct(v)}%</b></div><div class="obs-bar"><i style="width:${pct(v)}%"></i></div>`;
}

async function openRelation() {
  relationPanel.classList.remove("hidden");
  try {
    const res = await fetch("/api/observer");
    const d = await res.json();
    const r = d.relationship;
    relationContent.innerHTML =
      `<div class="obs-row"><span>信任</span><b>${pct(r.trust)}%</b></div><div class="obs-bar"><i style="width:${pct(r.trust)}%"></i></div>` +
      `<div class="obs-row"><span>依恋</span><b>${pct(r.attachment)}%</b></div><div class="obs-bar"><i style="width:${pct(r.attachment)}%"></i></div>` +
      `<div class="obs-row"><span>熟悉</span><b>${pct(r.familiarity)}%</b></div><div class="obs-bar"><i style="width:${pct(r.familiarity)}%"></i></div>` +
      `<div class="obs-row"><span>共同经历</span><b>${pct(r.shared_experience)}%</b></div><div class="obs-bar"><i style="width:${pct(r.shared_experience)}%"></i></div>` +
      `<div class="obs-row"><span>阶段</span><b>${r.stage || "陌生"}</b></div>` +
      `<div class="obs-row"><span>互动次数</span><b>${r.interaction_count || 0}</b></div>`;
  } catch {
    relationContent.innerHTML = '<div class="obs-row">无法连接</div>';
  }
}

async function openSchedule() {
  schedulePanel.classList.remove("hidden");
  try {
    const res = await fetch("/api/schedule");
    const d = await res.json();
    const slots = d.today || [];
    scheduleContent.innerHTML =
      `<div class="obs-row"><span>当前</span><b>${d.current_activity || "—"}</b></div>` +
      slots.map((s) => `<div class="obs-row"><span>${s.start} - ${s.end}</span><b>${s.name}</b></div>`).join("");
  } catch {
    scheduleContent.innerHTML = '<div class="obs-row">无法连接</div>';
  }
}

async function loadSettingsBackend() {
  try {
    const res = await fetch("/api/settings");
    const d = await res.json();
    setSpeed.textContent = d.simulation_minutes_per_real_second ?? "-";
  } catch { /* 忽略 */ }
}

/* ─────────── 状态轮询 ─────────── */

async function loadStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    applyWorldState(data.life_state);
  } catch { /* 忽略 */ }
}

/* ─────────── 事件绑定 ─────────── */

chatBtn.addEventListener("click", () => {
  chatDrawer.classList.toggle("hidden");
  if (!chatDrawer.classList.contains("hidden")) { renderHistory(); chatInput.focus(); }
});
chatClose.addEventListener("click", () => chatDrawer.classList.add("hidden"));
chatSend.addEventListener("click", submitChat);
chatInput.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); submitChat(); } });

relationBtn.addEventListener("click", () => { relationPanel.classList.toggle("hidden"); if (!relationPanel.classList.contains("hidden")) openRelation(); });
relationClose.addEventListener("click", () => relationPanel.classList.add("hidden"));

scheduleBtn.addEventListener("click", () => { schedulePanel.classList.toggle("hidden"); if (!schedulePanel.classList.contains("hidden")) openSchedule(); });
scheduleClose.addEventListener("click", () => schedulePanel.classList.add("hidden"));

settingsBtn.addEventListener("click", () => settingsPanel.classList.toggle("hidden"));
settingsClose.addEventListener("click", () => settingsPanel.classList.add("hidden"));

voiceBtn.addEventListener("click", () => showTip("🎤 语音功能即将接入"));

hudToggle.addEventListener("click", () => {
  const body = hudEl.querySelector(".hud-body");
  body.style.display = body.style.display === "none" ? "block" : "none";
});

["set-name", "set-user-name", "set-hud", "set-proactive", "set-night", "set-sound"].forEach((id) => {
  const el = document.getElementById(id);
  el.addEventListener("change", () => {
    if (id === "set-name") settings.name = el.value;
    if (id === "set-user-name") settings.user_name = el.value;
    if (id === "set-hud") settings.show_hud = el.checked;
    if (id === "set-proactive") settings.allow_proactive = el.checked;
    if (id === "set-night") settings.night_mode = el.checked;
    if (id === "set-sound") settings.sound = el.checked;
    saveSettings();
    applySettings();
  });
});

/* ─────────── 启动 ─────────── */

avatar.init(avatarMount);
applySettings();

xiaoqiSpeak("你来啦～欢迎回到我的房间。");

renderHistory();
loadStatus();
loadSettingsBackend();

setInterval(loadStatus, 5000);
setInterval(pollProactive, 6000);
