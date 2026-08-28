/* ═══════════════════════════════════════════════════
   小七 · 语音状态机
   idle -> listening -> processing -> speaking -> idle
   ═══════════════════════════════════════════════════ */

const STATES = ["idle", "listening", "processing", "speaking"];

class VoiceStateMachine {
  constructor() {
    this._state = "idle";
    this._listeners = [];
  }

  get state() { return this._state; }

  onChange(cb) {
    this._listeners.push(cb);
    return () => {
      this._listeners = this._listeners.filter((f) => f !== cb);
    };
  }

  _set(state) {
    if (!STATES.includes(state)) throw new Error(`unknown voice state: ${state}`);
    if (this._state === state) return;
    this._state = state;
    this._listeners.forEach((cb) => cb(state));
  }

  reset() { this._set("idle"); }
  toListening() { this._set("listening"); }
  toProcessing() { this._set("processing"); }
  toSpeaking() { this._set("speaking"); }
}

export { VoiceStateMachine, STATES };
