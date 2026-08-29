/* ═══════════════════════════════════════════════════
   小七 · AI Companion 前端逻辑
   小家 / 聊天 / 语音 三视图 + 设置 + 状态轮询
   ═══════════════════════════════════════════════════ */

import Avatar2D from "./avatar/avatar_2d.js";

import AudioInputAdapter from "./voice/audio_input_adapter.js";
import VoicePipeline from "./voice/voice_pipeline.js";
import { BrowserSTT, ServerSTT } from "./voice/stt_adapter.js";
import { createTTSAdapter } from "./voice/tts_adapter.js";

/* ─────────── 诊断：全局错误 → 后端日志（fetch 信标，独立于 pywebview） ─────────── */
function _jsLog(level, msg) {
  try {
    fetch("/api/_jslog", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({level, msg: String(msg).slice(0,200)}) });
  } catch {}
  console.log(`[${level}]`, msg);
}
(function() {
  _jsLog("boot", "app.js module loaded");
  window.addEventListener("error", (e) => { _jsLog("error", e.message + " @ " + e.filename + ":" + e.lineno); });
  window.addEventListener("unhandledrejection", (e) => { _jsLog("unhandled", String(e.reason)); });
})();

/* ─────────── 元素 ─────────── */
const $ = (id) => document.getElementById(id);

const views = { home: $("view-home"), chat: $("view-chat"), voice: $("view-voice") };
const navBtns = { home: $("nav-home"), chat: $("nav-chat"), voice: $("nav-voice") };

const chatMessages = $("chat-messages");
const chatInput = $("chat-input");
const sendBtn = $("send-btn");
const micBtn = $("composer-mic") || $("mic-btn");
const statusText = $("status-text");
const timeDisplay = $("time-display");
const homeStatus = $("home-status");
const homeBubble = $("home-bubble");
const btnSettings = $("btn-settings");

/* ─────────── Avatar 选择（VRM → Three → 2D） ─────────── */
let avatar = null;
let avatarMode = "2d";

async function initAvatar() {
  // 尝试 VRM（动态 import，不阻塞主模块）
  try {
    const { default: AvatarVRM } = await import("./avatar/avatar_vrm.js");
    const vrm = new AvatarVRM();
    await vrm.init($("avatar-mount"));
    avatar = vrm;
    avatarMode = "vrm";
    _jsLog("boot", "avatar: VRM");
    return;
  } catch (e) { _jsLog("boot", `avatar: VRM unavailable (${e.message})`); }
  // 尝试 Three.js（动态 import）
  try {
    const { default: AvatarThree } = await import("./avatar/avatar_three.js");
    const three = new AvatarThree();
    await Promise.resolve(three.init($("avatar-mount")));
    avatar = three;
    avatarMode = "3d";
    _jsLog("boot", "avatar: Three.js");
  } catch (e) {
    _jsLog("boot", `avatar: 3D unavailable (${e.message}), fallback 2D`);
    avatar = new Avatar2D().init($("avatar-mount"));
    avatarMode = "2d";
  }
}

/* ─────────── 状态 → 表现 ─────────── */
const ACTIVITY_AVATAR = {
  sleep: "sleeping", pre_sleep: "relaxing", morning_prep: "idle",
  commute: "idle", morning_clinic: "idle", afternoon_clinic: "idle",
  commute_grocery: "idle", lunch_break: "relaxing", cooking_dinner: "idle",
  home_leisure: "relaxing", home_rest: "relaxing",
};
const ACTIVITY_POSITION = {
  sleep: "bed", pre_sleep: "sofa", morning_prep: "center", commute: "window",
  lunch_break: "sofa", cooking_dinner: "center", home_leisure: "sofa", home_rest: "sofa",
};
const EMOTION_CLASS = {
  happy: "happy", excited: "excited", calm: "idle",
  lonely: "sad", anxious: "think", angry: "angry",
};
const MOOD_LABEL = { happy: "开心", calm: "平静", lonely: "孤独", excited: "兴奋", anxious: "焦虑", angry: "生气" };

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
  document.body.className = getPeriodClass(lifeState.current_time);
  if (timeDisplay) timeDisplay.textContent = formatClock(lifeState.current_time);

  const activity = lifeState.current_activity || "";
  avatar.setState(EMOTION_CLASS[lifeState.dominant_emotion] || "idle");
  const st = ACTIVITY_AVATAR[activity];
  if (st) avatar.play(st);
  const pos = ACTIVITY_POSITION[activity];
  if (pos) avatar.moveTo(pos);
  if ((lifeState.energy ?? 1) < 0.35) avatar.setState("tired");

  $("st-mood").textContent = MOOD_LABEL[lifeState.dominant_emotion] || "-";
  $("st-energy").textContent = Math.round((lifeState.energy ?? 0) * 100) + "%";
  $("st-activity").textContent = lifeState.current_activity || "-";
}

function formatClock(iso) {
  if (!iso) return "";
  try { return new Date(iso).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }); }
  catch { return ""; }
}

/* ─────────── 视图切换 ─────────── */
function switchView(name) {
  Object.values(views).forEach((v) => v.classList.remove("active"));
  Object.values(navBtns).forEach((b) => b.classList.remove("active"));
  views[name].classList.add("active");
  navBtns[name].classList.add("active");
  if (name === "chat") chatInput.focus();
}
function bind(id, event, fn, label) {
  const el = $(id);
  if (!el) { _jsLog("warn", `element #${id} not found, cannot bind ${label}`); return; }
  el.addEventListener(event, (e) => { _jsLog("click", label); fn(e); });
}
function bindNav(id, name) {
  const el = $(id);
  if (!el) { _jsLog("warn", `nav #${id} not found`); return; }
  el.addEventListener("click", () => { _jsLog("click", name); switchView(name); });
}
bindNav("nav-home", "home");
bindNav("nav-chat", "chat");
bindNav("nav-voice", "voice");
bind("btn-settings", "click", () => { window.location.href = "/settings"; }, "settings");
bind("btn-clear-chat", "click", () => {
  if (confirm("清空全部聊天记录？")) { saveHistory([]); renderHistory(); }
}, "clear_chat");
bind("send-btn", "click", submitChat, "send");
bind("chat-input", "keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); submitChat(); } }, "chat_input_key");

/* ─────────── 聊天 ─────────── */
const HISTORY_KEY = "xiaoqi_ai_chat";
function loadHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]"); }
  catch { return []; }
}
function saveHistory(h) {
  if (h.length > 200) h = h.slice(-200);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(h));
}
function appendMsg(role, text, time) {
  const h = loadHistory();
  h.push({ role, text, time: time || new Date().toISOString() });
  saveHistory(h);
  renderChatMessage({ role, text, time: time || new Date().toISOString() });
  scrollChat();
}
function renderChatMessage(m) {
  const w = document.createElement("div");
  w.className = `msg ${m.role}`;
  const b = document.createElement("div");
  b.className = "bubble";
  b.textContent = m.text;
  w.appendChild(b);
  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = formatClock(m.time);
  w.appendChild(meta);
  chatMessages.appendChild(w);
}
function scrollChat() { chatMessages.scrollTop = chatMessages.scrollHeight; }
function renderHistory() {
  chatMessages.innerHTML = "";
  loadHistory().forEach(renderChatMessage);
}

async function sendMessage(text) {
  sendBtn.disabled = true;
  appendMsg("user", text, new Date().toISOString());
  chatInput.value = "";

  const typing = document.createElement("div");
  typing.className = "msg assistant typing";
  typing.innerHTML = '<div class="bubble">小七正在思考…</div>';
  chatMessages.appendChild(typing);
  scrollChat();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    typing.remove();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);

    // 家中小七也说话（气泡）
    showHomeBubble(data.reply);

    appendMsg("assistant", data.reply, new Date().toISOString());
    if (data.life_state) applyWorldState(data.life_state);
    statusText.textContent = "在线";
  } catch (err) {
    typing.remove();
    const m = document.createElement("div");
    m.className = "msg assistant";
    m.innerHTML = `<div class="bubble">（小七暂时没回应：${err.message}）</div>`;
    chatMessages.appendChild(m);
    scrollChat();
  } finally {
    sendBtn.disabled = false;
    chatInput.focus();
  }
}
function submitChat() {
  const t = chatInput.value.trim();
  if (!t) return;
  sendMessage(t);
}

/* ─────────── 家中小七气泡 ─────────── */
function showHomeBubble(text) {
  homeBubble.textContent = text;
  homeBubble.classList.remove("hidden");
  if (avatar.talk) avatar.talk();
  clearTimeout(showHomeBubble._t);
  showHomeBubble._t = setTimeout(() => {
    homeBubble.classList.add("hidden");
    if (avatar.stopTalking) avatar.stopTalking();
  }, Math.min(3000 + text.length * 60, 8000));
}

/* ─────────── 语音 ─────────── */
let voicePipeline = null;
let voiceActive = false;

async function setupVoice() {
  try {
    const tts = await createTTSAdapter();
    const stt = new BrowserSTT();
    voicePipeline = new VoicePipeline({
      audioInput: new AudioInputAdapter(),
      stt,
      tts,
      api: {
        chat: async (text) => {
          const res = await fetch("/api/chat", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text }),
          });
          const data = await res.json();
          if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
          if (data.life_state) applyWorldState(data.life_state);
          return data.reply;
        },
      },
    });
    voicePipeline.setAvatar(avatar);
    voicePipeline.onBubble = (userText, replyText) => {
      appendMsg("user", userText, new Date().toISOString());
      appendMsg("assistant", replyText, new Date().toISOString());
      showHomeBubble(replyText);
    };

    const startListen = async (btn) => {
      if (voiceActive) return;
      voiceActive = true;
      btn.classList.add("listening");
      $("voice-orb").classList.add("listening");
      $("voice-hint").textContent = "正在聆听…";
      try { await voicePipeline.startListening(); }
      catch (e) { toast(`🎤 ${e.message}`); voiceActive = false; btn.classList.remove("listening"); $("voice-orb").classList.remove("listening"); $("voice-hint").textContent = "按住 🎙 说话"; }
    };
    const endListen = async (btn) => {
      if (!voiceActive) return;
      voiceActive = false;
      btn.classList.remove("listening");
      $("voice-orb").classList.remove("listening");
      $("voice-hint").textContent = "按住 🎙 说话";
      try { await voicePipeline.stopListening(); renderHistory(); }
      catch (e) { toast(`🎤 ${e.message}`); }
    };

    [micBtn, $("voice-btn")].forEach((btn) => {
      if (!btn) return;
      btn.disabled = false;
      btn.addEventListener("mousedown", () => startListen(btn));
      btn.addEventListener("mouseup", () => endListen(btn));
      btn.addEventListener("mouseleave", () => endListen(btn));
      btn.addEventListener("touchend", () => endListen(btn));
    });

    if ($("voice-note")) {
      const st = await fetch("/api/voice/status").then(r => r.json()).catch(() => null);
      if (st) {
        const ttsKind = st.tts?.available ? (st.tts.provider || "alibaba") : "browser";
        $("voice-note").textContent = `语音输出：${ttsKind} · 语音输入：浏览器识别`;
      }
    }
  } catch (e) {
    console.warn("[voice] setup failed:", e);
  }
}

/* ─────────── Toast ─────────── */
let toastTimer;
function toast(text) {
  const t = $("toast");
  t.textContent = text;
  t.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.add("hidden"), 4000);
}

/* ─────────── 设置已在顶部 bind() 中绑定 ─────────── */

/* ─────────── 主动消息 ─────────── */
async function pollProactive() {
  try {
    const res = await fetch("/api/proactive");
    if (!res.ok) return;
    const data = await res.json();
    (data.messages || []).forEach((m) => {
      if (m.content) { showHomeBubble(m.content); appendMsg("assistant", m.content, new Date().toISOString()); }
    });
  } catch { /* 静默 */ }
}

/* ─────────── 状态轮询 ─────────── */
async function loadStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    applyWorldState(data.life_state);
    statusText.textContent = "在线";
    $("chat-status").textContent = "在线";
  } catch { statusText.textContent = "离线"; $("chat-status").textContent = "离线"; }
}

/* ─────────── 启动 ─────────── */
async function boot() {
  await initAvatar();
  renderHistory();
  switchView("home");
  await setupVoice();
  loadStatus();
  setInterval(loadStatus, 5000);
  setInterval(pollProactive, 8000);
  setTimeout(() => showHomeBubble("你来啦～我在家呢，今天过得怎么样？"), 800);
}
boot();
