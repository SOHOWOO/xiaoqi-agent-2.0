/* ═══════════════════════════════════════════════════
   小七 · 音频输入 Adapter
   麦克风捕获（getUserMedia + MediaRecorder）。
   ═══════════════════════════════════════════════════ */

class AudioInputAdapter {
  constructor() {
    this._stream = null;
    this._recorder = null;
    this._chunks = [];
    this._mimeType = "";
  }

  async start() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error("麦克风不可用：此浏览器不支持 getUserMedia");
    }

    this._stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    this._chunks = [];

    const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
    this._mimeType = candidates.find((t) => MediaRecorder.isTypeSupported(t)) || "";

    this._recorder = new MediaRecorder(this._stream, this._mimeType ? { mimeType: this._mimeType } : undefined);
    this._recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) this._chunks.push(e.data);
    };
    this._recorder.start();
  }

  /* 停止录音并返回 { blob, mimeType } */
  stop() {
    return new Promise((resolve, reject) => {
      if (!this._recorder) {
        reject(new Error("recorder not started"));
        return;
      }
      this._recorder.onstop = () => {
        const blob = new Blob(this._chunks, { type: this._mimeType || "audio/webm" });
        this._cleanup();
        resolve({ blob, mimeType: this._mimeType });
      };
      this._recorder.stop();
    });
  }

  async abort() {
    if (this._recorder && this._recorder.state !== "inactive") {
      try { this._recorder.stop(); } catch { /* ignore */ }
    }
    this._cleanup();
  }

  _cleanup() {
    if (this._stream) {
      this._stream.getTracks().forEach((t) => t.stop());
      this._stream = null;
    }
    this._recorder = null;
    this._chunks = [];
  }
}

export default AudioInputAdapter;
