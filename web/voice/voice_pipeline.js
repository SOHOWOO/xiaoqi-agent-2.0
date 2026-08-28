/* ═══════════════════════════════════════════════════
   小七 · 语音编排 Pipeline
   麦克风 -> STT -> /api/chat -> TTS -> Avatar 嘴型
   ─────────────────────────────────────────────
   状态机：idle -> listening -> processing -> speaking -> idle
   ═══════════════════════════════════════════════════ */

import { VoiceStateMachine } from "./voice_state.js";

class VoicePipeline {
  constructor({ audioInput, stt, tts, api = {} }) {
    this.audioInput = audioInput;
    this.stt = stt;
    this.tts = tts;
    this.api = api; // { chat: async (text) => reply }

    this.state = new VoiceStateMachine();
    this.avatar = null;
    this.onBubble = null; // (text) => void，可选：把语音消息放入手机

    this._recording = false;
  }

  get ttsKind() { return this.tts ? this.tts.kind : "none"; }

  setAvatar(avatar) { this.avatar = avatar; return this; }

  /* 开始聆听（按住/点击 🎤） */
  async startListening() {
    if (this._recording) return;
    this._recording = true;

    try {
      await this.audioInput.start();
      this.state.toListening();
      if (this.avatar) {
        this.avatar.setListening(true);
      }

      /* 浏览器 STT 实时流 */
      if (this.stt && typeof this.stt.start === "function") {
        this.stt.onPartial(() => {});
        this.stt.onFinal(() => {});
        this.stt.onEnd(() => {});
      }
    } catch (error) {
      this._recording = false;
      throw error;
    }
  }

  /* 结束聆听并处理 */
  async stopListening() {
    if (!this._recording) return;
    this._recording = false;

    let text = "";

    try {
      const { blob } = await this.audioInput.stop();
      this.state.toProcessing();
      if (this.avatar) {
        this.avatar.setListening(false);
        this.avatar.setThinking(true);
      }

      /* STT：浏览器实时流优先；否则 server */
      if (this.stt && typeof this.stt.transcribe === "function") {
        text = await this.stt.transcribe(blob);
      } else if (this.stt) {
        /* browser STT 已经在 listen 阶段收集 final，这里取最近一次 */
        text = this._browserFinal || "";
      }
      this._browserFinal = "";
    } catch (error) {
      this.state.reset();
      if (this.avatar) { this.avatar.setThinking(false); this.avatar.setListening(false); }
      throw error;
    }

    if (!text || !text.trim()) {
      this.state.reset();
      if (this.avatar) this.avatar.setThinking(false);
      return "";
    }

    /* 进入 Core（与文字聊天共用 /api/chat） */
    let reply = "";
    try {
      reply = await this.api.chat(text);
    } finally {
      if (this.avatar) this.avatar.setThinking(false);
    }

    if (this.onBubble) this.onBubble(text, reply);

    await this.speak(reply);
    return reply;
  }

  /* 说一句话（TTS 为 null 时仅返回文字，不播放） */
  async speak(text) {
    if (!text) return;
    if (!this.tts) {
      // TTS unavailable：静默返回，避免崩溃
      this.state.reset();
      return;
    }
    this.state.toSpeaking();

    return new Promise((resolve) => {
      if (this.avatar) this.avatar.setSpeaking(true);

      this.tts.onStart(() => {});
      this.tts.onEnd(() => {
        this.state.reset();
        if (this.avatar) this.avatar.setSpeaking(false);
        resolve();
      });

      this.tts.onAudio((getAmp) => {
        this._amp = getAmp || null;
      });

      /* 嘴型循环：振幅 -> setMouthOpen */
      if (this._mouthLoop) clearInterval(this._mouthLoop);
      this._mouthLoop = setInterval(() => {
        if (this.avatar && this._amp) {
          this.avatar.setMouthOpen(this._amp());
        }
      }, 60);

      this.tts.speak(text).catch(() => {
        this.state.reset();
        if (this.avatar) this.avatar.setSpeaking(false);
        resolve();
      });
    });
  }

  stop() {
    if (this.tts) this.tts.stop();
    if (this._mouthLoop) clearInterval(this._mouthLoop);
    this.state.reset();
  }
}

export default VoicePipeline;
