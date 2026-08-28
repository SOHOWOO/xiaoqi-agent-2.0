/* ═══════════════════════════════════════════════════
   小七 · 前端逻辑
   世界驱动 / 小七手机 / 心灵观察站
   ═══════════════════════════════════════════════════ */

const worldEl = document.getElementById("world");
const xiaoqiEl = document.getElementById("xiaoqi");
const bodyEl = document.body;

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

/* ─────────── 状态 → 表现映射 ─────────── */

const ACTIVITY_POSE = {
  sleep: "sleep",
  pre_sleep: "sit",
  morning_prep: "stand",
  commute: "leave",
  morning_clinic: "leave",
  afternoon_clinic: "leave",
  commute_grocery: "leave",
  lunch_break: "sit",
  cooking_dinner: "stand",
  home_leisure: "sit",
  home_rest: "sit",
};

const EMOTION_CLASS = {
  happy: "smile",
  excited: "excited",
  calm: "neutral",
  lonely: "sad",
  anxious: "worried",
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

  bodyEl.className = getPeriodClass(lifeState.current_time);

  const activity = lifeState.current_activity || "";
  const pose = ACTIVITY_POSE[activity] || "stand";

  xiaoqiEl.classList.remove(
    "stand", "sit", "sleep", "leave", "onphone",
    "slow", "smile", "sad", "angry", "excited", "worried", "neutral",
  );

  xiaoqiEl.classList.add(pose);

  if (activity === "home_leisure") {
    xiaoqiEl.classList.add("onphone");
  }

  const energy = lifeState.energy ?? 1;
  if (energy < 0.35) {
    xiaoqiEl.classList.add("slow");
  }

  const dominant = lifeState.dominant_emotion || "calm";
  xiaoqiEl.classList.add(EMOTION_CLASS[dominant] || "neutral");
}

/* ─────────── 聊天历史（localStorage） ─────────── */

const HISTORY_KEY = "xiaoqi_phone_history";
const MAX_HISTORY = 200;

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveHistory(history) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
}

function formatTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

function renderMessage(msg) {
  const wrapper = document.createElement("div");
  wrapper.className = `phone-msg ${msg.role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = msg.text;
  wrapper.appendChild(bubble);

  const meta = document.createElement("div");
  meta.className = "meta";
  meta.innerHTML =
    `<span>${formatTime(msg.time)}</span>` +
    (msg.role === "user"
      ? '<span class="read">已读 ✓</span>'
      : "");

  wrapper.appendChild(meta);
  phoneMessagesEl.appendChild(wrapper);
}

function renderHistory() {
  phoneMessagesEl.innerHTML = "";
  loadHistory().forEach(renderMessage);
  scrollPhone();
}

function scrollPhone() {
  phoneMessagesEl.scrollTop = phoneMessagesEl.scrollHeight;
}

function appendChat(role, text, time) {
  const history = loadHistory();
  history.push({
    role,
    text,
    time: time || new Date().toISOString(),
  });
  if (history.length > MAX_HISTORY) history.splice(0, history.length - MAX_HISTORY);
  saveHistory(history);
  renderMessage({ role, text, time: time || new Date().toISOString() });
  scrollPhone();
}

/* ─────────── 主动消息 → 手机通知 ─────────── */

let unreadCount = 0;

function notifyProactive(content) {
  unreadCount += 1;
  phoneEntry.querySelector(".entry-dot").classList.add("unread");

  if (phoneEl.classList.contains("hidden")) {
    return;
  }
  appendChat("assistant", content, new Date().toISOString());
}

/* ─────────── API ─────────── */

async function loadStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    applyWorldState(data.life_state);
    phoneStatusEl.textContent = "在线";
  } catch {
    phoneStatusEl.textContent = "离线";
  }
}

async function loadProactive() {
  try {
    const res = await fetch("/api/proactive");
    if (!res.ok) return;
    const data = await res.json();
    (data.messages || []).forEach((msg) => {
      if (msg.content) notifyProactive(msg.content);
    });
  } catch {
    /* 静默 */
  }
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
    if (!res.ok) {
      throw new Error(data.error || `HTTP ${res.status}`);
    }
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

/* ─────────── 心灵观察站 ─────────── */

let observerData = null;

async function loadObserver() {
  try {
    const res = await fetch("/api/observer");
    if (!res.ok) return;
    observerData = await res.json();
    renderObserverView("emotion");
  } catch {
    observerContent.innerHTML =
      '<div class="obs-empty">暂时无法连接小七的心灵</div>';
  }
}

function pct(value) {
  return Math.round((value ?? 0) * 100);
}

function bar(value, label) {
  return (
    `<div class="obs-row"><span>${label}</span><b>${pct(value)}%</b></div>` +
    `<div class="obs-bar"><i style="width:${pct(value)}%"></i></div>`
  );
}

function renderObserverView(view) {
  if (!observerData) return;
  const d = observerData;
  let html = "";

  if (view === "emotion") {
    const e = d.emotion.current;
    const moodLabel = {
      happy: "开心", calm: "平静", lonely: "孤独",
      excited: "兴奋", anxious: "焦虑", angry: "生气",
    }[d.emotion.dominant] || d.emotion.dominant;

    html += `<div class="obs-card"><h4>💗 当前情绪 · ${moodLabel}</h4>`;
    for (const [k, v] of Object.entries(e)) {
      const label = { happy: "开心", calm: "平静", lonely: "孤独", excited: "兴奋", anxious: "焦虑", angry: "生气" }[k] || k;
      html += bar(v, label);
    }
    html += "</div>";

    html += `<div class="obs-card"><h4>🧪 神经化学</h4>`;
    const neuroLabel = { dopamine: "多巴胺", serotonin: "血清素", oxytocin: "催产素", cortisol: "皮质醇", endorphin: "内啡肽", noradrenaline: "去甲肾上腺素" };
    for (const [k, v] of Object.entries(d.neurochemical)) {
      html += bar(v, neuroLabel[k] || k);
    }
    html += "</div>";
  }

  if (view === "relation") {
    const r = d.relationship;
    html += `<div class="obs-card"><h4>❤️ 与小七的关系</h4>`;
    html += bar(r.trust, "信任");
    html += bar(r.attachment, "依恋");
    html += bar(r.familiarity, "熟悉");
    html += bar(r.shared_experience, "共同经历");
    html += `<div class="obs-row"><span>阶段</span><b>${
      r.stage ?? "陌生"
    }</b></div>`;
    html += `<div class="obs-row"><span>互动次数</span><b>${r.interaction_count ?? 0}</b></div>`;
    html += "</div>";
  }

  if (view === "diary") {
    if (!d.diaries.length) {
      html = '<div class="obs-empty">小七还没有写下日记</div>';
    } else {
      html = d.diaries.map((entry) =>
        `<div class="obs-diary">
           <div class="date">📖 ${entry.date} · ${
             (entry.mood_tags || []).join(" / ") || "平静"
           }</div>
           <div>${escapeHtml(entry.content)}</div>
         </div>`
      ).join("");
    }
  }

  if (view === "memory") {
    if (!d.memories.length) {
      html = '<div class="obs-empty">还没有共同的回忆</div>';
    } else {
      html = d.memories.map((m) =>
        `<div class="obs-memory">
           <span class="tag">${typeLabel(m.type)}</span>
           <div>${escapeHtml(m.content)}</div>
         </div>`
      ).join("");
    }
  }

  if (view === "schedule") {
    const s = d.schedule;
    html += `<div class="obs-card"><h4>📅 她的日程</h4>`;
    html += `<div class="obs-row"><span>当前</span><b>${
      s.current_activity || "—"
    }</b></div>`;
    html += "</div>";
    html += (s.today || []).map((slot) =>
      `<div class="obs-row"><span>${slot.start} - ${slot.end}</span><b>${slot.name}</b></div>`
    ).join("");
  }

  observerContent.innerHTML = html;
}

function typeLabel(type) {
  return {
    canonical: "真实记忆",
    interaction: "互动",
    virtual_life: "生活",
    episodic: "情景",
    semantic: "事实",
    relationship: "关系",
    diary: "日记",
  }[type] || type;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

/* ─────────── 事件绑定 ─────────── */

phoneEntry.addEventListener("click", () => {
  phoneEl.classList.remove("hidden");
  unreadCount = 0;
  phoneEntry.querySelector(".entry-dot").classList.remove("unread");
  renderHistory();
  phoneInput.focus();
});

phoneClose.addEventListener("click", () => {
  phoneEl.classList.add("hidden");
});

phoneEl.addEventListener("click", (event) => {
  if (event.target === phoneEl) phoneEl.classList.add("hidden");
});

observerEntry.addEventListener("click", () => {
  observerEl.classList.remove("hidden");
  loadObserver();
});

observerClose.addEventListener("click", () => {
  observerEl.classList.add("hidden");
});

observerEl.addEventListener("click", (event) => {
  if (event.target === observerEl) observerEl.classList.add("hidden");
});

document.querySelectorAll(".observer-nav button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".observer-nav button").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    renderObserverView(btn.dataset.view);
  });
});

function submitMessage() {
  const text = phoneInput.value.trim();
  if (!text) return;
  appendChat("user", text, new Date().toISOString());
  phoneInput.value = "";
  sendMessage(text);
}

sendBtn.addEventListener("click", submitMessage);

phoneInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    submitMessage();
  }
});

/* ─────────── 启动 ─────────── */

appendChat(
  "assistant",
  "你来啦。我在家呢，今天过得怎么样？",
  new Date().toISOString(),
);

renderHistory();
loadStatus();
loadProactive();

setInterval(loadStatus, 5000);
setInterval(loadProactive, 6000);
