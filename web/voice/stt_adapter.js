/* ═══════════════════════════════════════════════════
   小七 · STT Adapter
   provider:
     - browser: Web Speech API（实时，内置 VAD，Chrome/Edge）
     - server : WebSocket -> voice_server.py（faster-whisper，可选）
   ═══════════════════════════════════════════════════ */

class BrowserSTT {
  constructor() {
    this._recognition = null;
    this._onPartial = null;
    this._onFinal = null;
    this._onEnd = null;
    this._running = false;
  }

  start() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) throw new Error("此浏览器不支持 Web Speech 识别");

    this._recognition = new SR();
    this._recognition.lang = "zh-CN";
    this._recognition.interimResults = true;
    this._recognition.continuous = false;

    this._recognition.onresult = (e) => {
      let interim = "";
      let final = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const text = e.results[i][0].transcript;
        if (e.results[i].isFinal) final += text;
        else interim += text;
      }
      if (interim && this._onPartial) this._onPartial(interim);
      if (final && this._onFinal) this._onFinal(final);
    };
    this._recognition.onerror = () => this._end();
    this._recognition.onend = () => this._end();

    this._running = true;
    this._recognition.start();
  }

  stop() {
    if (this._recognition && this._running) {
      this._recognition.stop();
    }
    this._running = false;
  }

  _end() {
    if (!this._running) return;
    this._running = false;
    if (this._onEnd) this._onEnd();
  }

  onPartial(cb) { this._onPartial = cb; }
  onFinal(cb) { this._onFinal = cb; }
  onEnd(cb) { this._onEnd = cb; }
}

class ServerSTT {
  constructor(url) {
    this._url = url || "ws://127.0.0.1:8769";
    this._ws = null;
    this._onPartial = null;
    this._onFinal = null;
    this._onEnd = null;
    this._running = false;
  }

  start() { /* 由 pipeline 在录音结束后发送，这里仅标记 */ this._running = true; }

  async transcribe(blob) {
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(this._url);
      const timer = setTimeout(() => {
        ws.close();
        reject(new Error("voice server timeout"));
      }, 15000);

      ws.onopen = () => {
        ws.send(blob);
      };
      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.error) {
            clearTimeout(timer);
            ws.close();
            reject(new Error(data.error));
            return;
          }
          if (data.text) {
            if (this._onPartial) this._onPartial(data.text);
            if (this._onFinal) this._onFinal(data.text);
          }
          clearTimeout(timer);
          ws.close();
          resolve(data.text || "");
        } catch {
          clearTimeout(timer);
          ws.close();
          reject(new Error("bad voice server response"));
        }
      };
      ws.onerror = () => {
        clearTimeout(timer);
        reject(new Error("voice server unavailable"));
      };
    });
  }

  stop() { this._running = false; }
  onPartial(cb) { this._onPartial = cb; }
  onFinal(cb) { this._onFinal = cb; }
  onEnd(cb) { this._onEnd = cb; }
}

export { BrowserSTT, ServerSTT };
