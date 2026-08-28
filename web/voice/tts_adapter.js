/* ═══════════════════════════════════════════════════
   小七 · TTS Adapter
   provider:
     - browser : SpeechSynthesis（开发 fallback，明确区分）
     - server  : voice_server.py TTS（GPT-SoVITS/CosyVoice/XTTS，预留）
   嘴型驱动：onAudio 回调提供 AudioNode / amplitude 来源。
   ═══════════════════════════════════════════════════ */

class BrowserTTS {
  constructor() {
    this._voice = null;
    this._onStart = null;
    this._onEnd = null;
    this._utterance = null;
    this._ctx = null;
    this._analyser = null;
    this._audioNode = null;
  }

  /* 返回 tts 类型标识，供 UI 区分 */
  get kind() { return "browser"; }

  async speak(text) {
    if (!("speechSynthesis" in window)) {
      throw new Error("此浏览器不支持 SpeechSynthesis");
    }
    this._ensureAudio();

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

  /* onAudio(analyser): 提供 AnalyserNode 供嘴型振幅采样 */
  onAudio(cb) { this._onAudio = cb; }
  onStart(cb) { this._onStart = cb; }
  onEnd(cb) { this._onEnd = cb; }

  _ensureAudio() {
    if (this._ctx) return;
    this._ctx = new (window.AudioContext || window.webkitAudioContext)();
    this._analyser = this._ctx.createAnalyser();
    this._analyser.fftSize = 256;
  }

  /* SpeechSynthesis 不暴露音频流，用模拟振幅驱动嘴型（自然张合） */
  _startAmplitude() {
    if (this._onAudio) this._onAudio(() => 0.5 + 0.5 * Math.sin(performance.now() / 120) * Math.sin(performance.now() / 61));
  }
  _stopAmplitude() {
    if (this._onAudio) this._onAudio(null);
  }
}

class ServerTTS {
  constructor(url) {
    this._url = url || "/api/tts";
    this._audio = null;
    this._onStart = null;
    this._onEnd = null;
    this._ctx = null;
    this._analyser = null;
    this._onAudio = null;
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
    const source = this._ctx.createBufferSource();
    source.buffer = audioBuf;

    this._analyser = this._ctx.createAnalyser();
    this._analyser.fftSize = 256;
    source.connect(this._analyser);
    this._analyser.connect(this._ctx.destination);

    if (this._onStart) this._onStart();
    source.start(0);
    if (this._onAudio) this._onAudio(this._getAmp());

    source.onended = () => {
      if (this._onAudio) this._onAudio(null);
      if (this._onEnd) this._onEnd();
    };
    this._audio = source;
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
    if (this._audio) { try { this._audio.stop(); } catch { /* ignore */ } }
    if (this._onAudio) this._onAudio(null);
  }
  onAudio(cb) { this._onAudio = cb; }
  onStart(cb) { this._onStart = cb; }
  onEnd(cb) { this._onEnd = cb; }
}

export { BrowserTTS, ServerTTS };
