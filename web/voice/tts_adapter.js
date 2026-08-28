/* ═══════════════════════════════════════════════════
   小七 · TTS Adapter
   engine 明确区分：
     - browser     : SpeechSynthesis（开发 fallback）
     - server      : voice_server.py /api/tts（CosyVoice）
     - unavailable : 无可用 TTS
   嘴型：onAudio 回调提供 amplitude 来源。
   ═══════════════════════════════════════════════════ */

class BrowserTTS {
  constructor() {
    this._voice = null;
    this._onStart = null;
    this._onEnd = null;
    this._utterance = null;
    this._onAudio = null;
  }

  get kind() { return "browser"; }

  async speak(text) {
    if (!("speechSynthesis" in window)) {
      throw new Error("此浏览器不支持 SpeechSynthesis");
    }

    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = "zh-CN";
    utter.rate = 1.0;
    utter.pitch = 1.05;

    if (!this._voice) {
      const voices = window.speechSynthesis.getVoices();
      this._voice =
        voices.find((v) => v.lang === "zh-CN") ||
        voices.find((v) => v.lang.startsWith("zh")) ||
        null;
    }
    if (this._voice) utter.voice = this._voice;

    utter.onstart = () => {
      if (this._onStart) this._onStart();
      this._startAmplitude();
    };
    utter.onend = () => {
      this._stopAmplitude();
      if (this._onEnd) this._onEnd();
    };
    utter.onerror = () => {
      this._stopAmplitude();
      if (this._onEnd) this._onEnd();
    };

    this._utterance = utter;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utter);
  }

  stop() {
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    this._stopAmplitude();
  }

  onAudio(cb) { this._onAudio = cb; }
  onStart(cb) { this._onStart = cb; }
  onEnd(cb) { this._onEnd = cb; }

  /* SpeechSynthesis 不暴露音频流，用模拟振幅驱动嘴型 */
  _startAmplitude() {
    if (this._onAudio) this._onAudio(() => 0.5 + 0.5 * Math.sin(performance.now() / 120) * Math.sin(performance.now() / 61));
  }
  _stopAmplitude() {
    if (this._onAudio) this._onAudio(null);
  }
}

/* 服务器 TTS：主 web_server /api/tts（后端代理 Alibaba Qwen3-TTS，
   API Key 绝不到浏览器）音频播放时用真实 Analyser 振幅驱动嘴型 */
class ServerTTS {
  constructor(url) {
    this._url = url || "/api/tts";
    this._audio = null;
    this._source = null;
    this._onStart = null;
    this._onEnd = null;
    this._onAudio = null;
    this._ctx = null;
    this._analyser = null;
    this._ampTimer = null;
  }

  get kind() { return "server"; }

  async speak(text) {
    const res = await fetch(this._url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error(`TTS HTTP ${res.status}`);

    const buf = await res.arrayBuffer();

    if (!this._ctx) this._ctx = new (window.AudioContext || window.webkitAudioContext)();
    const audioBuf = await this._ctx.decodeAudioData(buf);

    this._source = this._ctx.createBufferSource();
    this._source.buffer = audioBuf;

    this._analyser = this._ctx.createAnalyser();
    this._analyser.fftSize = 256;
    this._source.connect(this._analyser);
    this._analyser.connect(this._ctx.destination);

    if (this._onStart) this._onStart();
    this._source.start(0);

    // 真实振幅 -> 嘴型
    this._startAmpTimer();

    this._source.onended = () => {
      this._stopAmpTimer();
      if (this._onAudio) this._onAudio(null);
      if (this._onEnd) this._onEnd();
    };
  }

  _startAmpTimer() {
    this._stopAmpTimer();
    this._ampTimer = setInterval(() => {
      if (this._onAudio && this._analyser) {
        this._onAudio(this._getAmp());
      }
    }, 60);
  }
  _stopAmpTimer() {
    if (this._ampTimer) clearInterval(this._ampTimer);
    this._ampTimer = null;
  }

  _getAmp() {
    const data = new Uint8Array(this._analyser.frequencyBinCount);
    this._analyser.getByteTimeDomainData(data);
    let sum = 0;
    for (let i = 0; i < data.length; i++) {
      const v = (data[i] - 128) / 128;
      sum += v * v;
    }
    return Math.min(1, Math.sqrt(sum / data.length) * 3);
  }

  stop() {
    if (this._source) { try { this._source.stop(); } catch { /* ignore */ } }
    this._stopAmpTimer();
    if (this._onAudio) this._onAudio(null);
  }
  onAudio(cb) { this._onAudio = cb; }
  onStart(cb) { this._onStart = cb; }
  onEnd(cb) { this._onEnd = cb; }
}

/* 根据后端 /api/voice/status 选择合适的 TTS Adapter
   优先级：Alibaba Remote TTS -> Browser SpeechSynthesis -> null
   浏览器绝不知道 API Key；Alibaba 由后端 voice_server /tts 代理。 */
async function createTTSAdapter() {
  try {
    const res = await fetch("/api/voice/status");
    const status = await res.json();

    // 服务器 Alibaba 可用 -> 通过后端 /tts 代理（浏览器不接触 Key）
    if (status.tts && status.tts.provider === "alibaba" && status.tts.available) {
      return new ServerTTS();
    }
  } catch { /* 忽略 */ }

  // 浏览器 fallback
  if ("speechSynthesis" in window) {
    return new BrowserTTS();
  }

  return null;
}

export { BrowserTTS, ServerTTS, createTTSAdapter };
