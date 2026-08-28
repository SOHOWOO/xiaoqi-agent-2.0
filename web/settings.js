/* ═══════════════════════════════════════════════════
   小七 · 设置中心 / 首次启动
   API Key 只通过后端保存，绝不出现在前端内存返回
   ═══════════════════════════════════════════════════ */

const welcome = document.getElementById("welcome");
const settingsEl = document.getElementById("settings");

/* ---------- 首次启动检测 ---------- */

async function checkSetup() {
  try {
    const res = await fetch("/api/setup");
    const data = await res.json();

    if (!data.setup_complete) {
      welcome.classList.remove("hidden");
      return;
    }

    settingsEl.classList.remove("hidden");
    loadAll();
  } catch {
    settingsEl.classList.remove("hidden");
    loadAll();
  }
}

/* ---------- 导航 ---------- */

document.querySelectorAll(".sidebar nav button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".sidebar nav button").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    document.getElementById(`panel-${btn.dataset.section}`).classList.add("active");

    if (btn.dataset.section === "system") loadSystemStatus();
    if (btn.dataset.section === "relation") loadRelation();
    if (btn.dataset.section === "keys") loadKeyStatus();
  });
});

/* ---------- 通用 fetch ---------- */

async function api(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  return res.json();
}

function show(el, text, ok) {
  const node = document.getElementById(el);
  node.textContent = text;
  node.className = "result " + (ok ? "ok" : "err");
}

/* ---------- 加载配置 ---------- */

async function loadAll() {
  try {
    const cfg = await api("/api/config");

    document.getElementById("ai-provider").value = cfg.ai?.provider || "deepseek";
    document.getElementById("ai-base-url").value = cfg.ai?.base_url || "";
    document.getElementById("ai-model").value = cfg.ai?.model || "";
    document.getElementById("ai-temp").value = cfg.ai?.temperature ?? 0.7;
    document.getElementById("ai-max-tokens").value = cfg.ai?.max_tokens ?? 1024;

    document.getElementById("tts-model").value = cfg.tts?.model || "";
    document.getElementById("tts-language").value = cfg.tts?.language || "Chinese";
    document.getElementById("tts-region").value = cfg.tts?.region || "singapore";
    document.getElementById("stt-language").value = cfg.stt?.language || "zh-CN";

    document.getElementById("ui-proactive").checked = !!cfg.ui?.allow_proactive;
    document.getElementById("ui-hud").checked = !!cfg.ui?.show_hud;
    document.getElementById("proactive-toggle").checked = !!cfg.ui?.allow_proactive;
    document.getElementById("appearance-night").checked = !!cfg.ui?.night_mode;
    document.getElementById("appearance-sound").checked = !!cfg.ui?.sound;
    document.getElementById("life-speed").value = cfg.life?.sim_minutes_per_real_second || 60;
  } catch { /* 忽略 */ }

  loadKeyStatus();
  loadSystemStatus();
}

/* ---------- AI 保存 / 测试 ---------- */

document.getElementById("ai-save").addEventListener("click", async () => {
  await api("/api/config", {
    method: "POST",
    body: JSON.stringify({
      ai: {
        provider: document.getElementById("ai-provider").value,
        base_url: document.getElementById("ai-base-url").value,
        model: document.getElementById("ai-model").value,
        temperature: parseFloat(document.getElementById("ai-temp").value) || 0.7,
        max_tokens: parseInt(document.getElementById("ai-max-tokens").value) || 1024,
      },
    }),
  });
  show("ai-result", "已保存 ✓", true);
});

document.getElementById("ai-test").addEventListener("click", async () => {
  show("ai-result", "测试中…");
  const r = await api("/api/secrets", {
    method: "POST",
    body: JSON.stringify({ provider: "deepseek", action: "test" }),
  });
  show("ai-result", r.ok ? "连接成功 ✓" : `失败: ${r.error || ""}`, !!r.ok);
});

/* ---------- TTS ---------- */

document.getElementById("tts-save").addEventListener("click", async () => {
  await api("/api/config", {
    method: "POST",
    body: JSON.stringify({
      tts: {
        model: document.getElementById("tts-model").value,
        language: document.getElementById("tts-language").value,
        region: document.getElementById("tts-region").value,
      },
    }),
  });
  show("tts-result", "已保存 ✓", true);
});

document.getElementById("tts-test").addEventListener("click", async () => {
  show("tts-result", "正在让小七说话…");
  try {
    const res = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: "你好，我是小七。" }),
    });
    if (!res.ok) {
      const err = await res.json();
      show("tts-result", `语音不可用：${err.error || res.status}`, false);
      return;
    }
    const buf = await res.arrayBuffer();
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const audio = await ctx.decodeAudioData(buf);
    const src = ctx.createBufferSource();
    src.buffer = audio;
    src.connect(ctx.destination);
    src.start(0);
    show("tts-result", "已播放 ✓", true);
  } catch (e) {
    show("tts-result", `失败：${e.message}`, false);
  }
});

/* ---------- STT ---------- */

document.getElementById("stt-save").addEventListener("click", async () => {
  await api("/api/config", {
    method: "POST",
    body: JSON.stringify({ stt: { language: document.getElementById("stt-language").value } }),
  });
  show("stt-result", "已保存 ✓", true);
});

document.getElementById("stt-test").addEventListener("click", async () => {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { show("stt-result", "此浏览器不支持语音识别", false); return; }
  const rec = new SR();
  rec.lang = document.getElementById("stt-language").value || "zh-CN";
  rec.onresult = (e) => show("stt-result", `识别到：${e.results[0][0].transcript} ✓`, true);
  rec.onerror = () => show("stt-result", "麦克风或识别失败", false);
  show("stt-result", "请说话…");
  rec.start();
});

/* ---------- 小家 / 主动 / 外观 ---------- */

function collectUi() {
  return {
    ui: {
      allow_proactive: document.getElementById("ui-proactive").checked,
      show_hud: document.getElementById("ui-hud").checked,
      night_mode: document.getElementById("appearance-night").checked,
      sound: document.getElementById("appearance-sound").checked,
    },
    life: { sim_minutes_per_real_second: parseInt(document.getElementById("life-speed").value) || 60 },
  };
}

document.getElementById("home-save").addEventListener("click", async () => {
  await api("/api/config", { method: "POST", body: JSON.stringify(collectUi()) });
  show("home-save", "", true);
  alert("已保存");
});
document.getElementById("proactive-save").addEventListener("click", async () => {
  await api("/api/config", {
    method: "POST",
    body: JSON.stringify({ ui: { allow_proactive: document.getElementById("proactive-toggle").checked } }),
  });
  alert("已保存");
});
document.getElementById("appearance-save").addEventListener("click", async () => {
  await api("/api/config", {
    method: "POST",
    body: JSON.stringify({
      ui: { night_mode: document.getElementById("appearance-night").checked, sound: document.getElementById("appearance-sound").checked },
    }),
  });
  alert("已保存");
});

/* ---------- API 密钥 ---------- */

async function loadKeyStatus() {
  const st = await api("/api/system/status");

  const ds = document.getElementById("deepseek-status");
  const al = document.getElementById("alibaba-status");

  ds.textContent = st.ai?.has_api_key ? "已配置 ✓" : "未配置";
  ds.className = st.ai?.has_api_key ? "ok" : "";
  al.textContent = st.tts?.has_api_key ? "已配置 ✓" : "未配置";
  al.className = st.tts?.has_api_key ? "ok" : "";
}

document.getElementById("key-deepseek-save").addEventListener("click", async () => {
  const v = document.getElementById("key-deepseek").value;
  if (!v) { alert("请输入 API Key"); return; }
  await api("/api/secrets", { method: "POST", body: JSON.stringify({ provider: "deepseek", value: v }) });
  document.getElementById("key-deepseek").value = "";
  alert("DeepSeek Key 已保存");
  loadKeyStatus();
});
document.getElementById("key-deepseek-test").addEventListener("click", async () => {
  const r = await api("/api/secrets", { method: "POST", body: JSON.stringify({ provider: "deepseek", action: "test" }) });
  alert(r.ok ? "连接成功 ✓" : `失败：${r.error || ""}`);
});
document.getElementById("key-deepseek-del").addEventListener("click", async () => {
  if (!confirm("删除 DeepSeek API Key？")) return;
  await api("/api/secrets", { method: "POST", body: JSON.stringify({ provider: "deepseek", action: "delete" }) });
  loadKeyStatus();
  alert("已删除");
});

document.getElementById("key-alibaba-save").addEventListener("click", async () => {
  const k = document.getElementById("key-alibaba").value;
  const vid = document.getElementById("voice-id-input").value;
  if (k) await api("/api/secrets", { method: "POST", body: JSON.stringify({ provider: "alibaba", value: k }) });
  if (vid) await api("/api/config", { method: "POST", body: JSON.stringify({ tts: { voice_id: vid } }) });
  document.getElementById("key-alibaba").value = "";
  document.getElementById("voice-id-input").value = "";
  alert("已保存");
  loadKeyStatus();
});
document.getElementById("key-alibaba-del").addEventListener("click", async () => {
  if (!confirm("删除阿里云 API Key？")) return;
  await api("/api/secrets", { method: "POST", body: JSON.stringify({ provider: "alibaba", action: "delete" }) });
  loadKeyStatus();
  alert("已删除");
});

/* ---------- 记忆 ---------- */

document.getElementById("memory-export").addEventListener("click", () => {
  show("memory-result", "记忆导出：请从数据目录复制 xiaoqi_memory.db", true);
});
document.getElementById("memory-clear").addEventListener("click", async () => {
  if (!confirm("确定清空全部记忆？此操作不可恢复！")) return;
  if (!confirm("再次确认：清空记忆？")) return;
  show("memory-result", "请从设置-系统执行数据清理", false);
});

/* ---------- 系统状态 / 关系 ---------- */

async function loadSystemStatus() {
  try {
    const st = await api("/api/system/status");
    const items = [
      ["Core", st.core],
      ["Memory", st.memory],
      ["LifeLoop", st.life_loop],
      ["Database", st.database],
      ["DeepSeek", st.ai?.has_api_key],
      ["Alibaba TTS", st.tts?.has_api_key],
      ["STT faster-whisper", st.stt?.available],
      ["Three.js Avatar", true],
    ];
    document.getElementById("system-status").innerHTML =
      items.map(([name, ok]) =>
        `<div class="obs-row"><span>${name}</span><b>${ok ? "✓" : "⚠ 未配置"}</b></div>`
      ).join("");
    document.getElementById("mini-core").textContent = `Core ${st.core ? "✓" : "✗"}`;
    document.getElementById("mini-ai").textContent = `AI ${st.ai?.has_api_key ? "✓" : "未配"}`;
    document.getElementById("mini-tts").textContent = `TTS ${st.tts?.has_api_key ? "✓" : "未配"}`;
    document.getElementById("mini-stt").textContent = `STT ${st.stt?.available ? "✓" : "未配"}`;
  } catch { /* 忽略 */ }
}

async function loadRelation() {
  try {
    const st = await api("/api/observer");
    const r = st.relationship;
    document.getElementById("relation-view").innerHTML =
      `<div class="obs-row"><span>信任</span><b>${Math.round((r.trust || 0) * 100)}%</b></div>
       <div class="obs-row"><span>依恋</span><b>${Math.round((r.attachment || 0) * 100)}%</b></div>
       <div class="obs-row"><span>阶段</span><b>${r.stage || "陌生"}</b></div>`;
  } catch { /* 忽略 */ }
}

/* ---------- 首次启动流程 ---------- */

document.getElementById("setup-test").addEventListener("click", async () => {
  const key = document.getElementById("setup-deepseek-key").value;
  if (!key) { show("setup-test-result", "请输入 API Key", false); return; }
  await api("/api/secrets", { method: "POST", body: JSON.stringify({ provider: "deepseek", value: key }) });
  const r = await api("/api/secrets", { method: "POST", body: JSON.stringify({ provider: "deepseek", action: "test" }) });
  show("setup-test-result", r.ok ? "连接成功 ✓" : `失败：${r.error || ""}`, !!r.ok);
});

document.getElementById("setup-next").addEventListener("click", () => {
  document.getElementById("setup-step-1").classList.add("hidden");
  document.getElementById("setup-step-2").classList.remove("hidden");
});

document.getElementById("setup-done").addEventListener("click", async () => {
  const k = document.getElementById("setup-alibaba-key").value;
  const vid = document.getElementById("setup-voice-id").value;
  if (k) await api("/api/secrets", { method: "POST", body: JSON.stringify({ provider: "alibaba", value: k }) });
  if (vid) await api("/api/config", { method: "POST", body: JSON.stringify({ tts: { voice_id: vid } }) });
  await api("/api/setup", { method: "POST", body: "{}" });
  welcome.classList.add("hidden");
  settingsEl.classList.remove("hidden");
  loadAll();
});

document.getElementById("setup-skip").addEventListener("click", async () => {
  await api("/api/setup", { method: "POST", body: "{}" });
  welcome.classList.add("hidden");
  settingsEl.classList.remove("hidden");
  loadAll();
});

/* ---------- 启动 ---------- */

checkSetup();
