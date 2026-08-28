/* ═══════════════════════════════════════════════════
   小七 · 2D Avatar（CSS 角色实现）
   3D 不可用时的 fallback；支持嘴型 / 表情 / 位置
   ═══════════════════════════════════════════════════ */

const STATE_CLASS = {
  idle: "idle",
  happy: "smile",
  sad: "sad",
  angry: "angry",
  excited: "excited",
  sleeping: "sleep",
  talking: "talk",
  reading: "read",
  relaxing: "relax",
  thinking: "think",
  tired: "slow",
  hungry: "slow",
  proactive: "onphone",
  onphone: "onphone",
};

const MOVE_CLASS = {
  desk: "at-desk",
  sofa: "at-sofa",
  bed: "at-bed",
  window: "at-window",
  center: "at-center",
};

class Avatar2D {
  constructor() {
    this.el = null;
    this.container = null;
    this.bubble = null;
    this._state = "idle";
    this._speaking = false;
    this._mouthEl = null;
    this._mouthTimer = null;
  }

  init(container) {
    this.container = container;

    this.el = document.createElement("div");
    this.el.id = "xiaoqi";
    this.el.className = "xiaoqi idle neutral at-center";

    this.el.innerHTML = `
      <div class="shadow"></div>
      <div class="figure">
        <div class="head">
          <div class="hair"></div>
          <div class="face">
            <span class="eye left"></span>
            <span class="eye right"></span>
            <span class="mouth"></span>
            <span class="blush left"></span>
            <span class="blush right"></span>
          </div>
        </div>
        <div class="body"></div>
        <div class="arm left"></div>
        <div class="arm right"></div>
        <div class="leg left"></div>
        <div class="leg right"></div>
      </div>
      <div class="phone-in-hand"></div>
    `;

    this.bubble = document.createElement("div");
    this.bubble.className = "avatar-bubble";
    this.bubble.style.display = "none";
    this.el.appendChild(this.bubble);

    this._mouthEl = this.el.querySelector(".mouth");

    container.appendChild(this.el);
    return this;
  }

  setState(state) {
    this._state = state;
    const cls = STATE_CLASS[state] || "idle";
    const moodCls = ["smile", "sad", "angry", "excited"].includes(cls) ? cls : "neutral";

    this.el.classList.remove(
      "idle", "smile", "sad", "angry", "excited",
      "sleep", "talk", "read", "relax", "think", "slow", "onphone",
      "neutral", "listen",
    );
    this.el.classList.add(cls, moodCls);
    return this;
  }

  talk() { this.el.classList.add("talk"); this._speaking = true; return this; }
  stopTalking() { this.el.classList.remove("talk"); this._speaking = false; this._stopMouth(); return this; }

  setSpeaking(speaking) {
    this._speaking = speaking;
    if (speaking) this.el.classList.add("talk");
    else { this.el.classList.remove("talk"); this._stopMouth(); }
    return this;
  }

  /* 嘴型：mouthOpen 0~1，用 mouth 高度模拟开合 */
  setMouthOpen(value) {
    if (!this._mouthEl) return this;
    const v = Math.max(0, Math.min(1, value || 0));
    this._mouthEl.style.height = `${8 + v * 18}px`;
    this._mouthEl.style.borderRadius = v > 0.2 ? "50%" : "";
    return this;
  }
  setViseme(_v) { return this; }

  /* 聆听：看向用户（轻微转头） */
  setListening(listening) {
    if (listening) {
      this.el.classList.add("listen");
      this.el.querySelector(".head").style.transform = "translateX(-50%) rotate(6deg)";
    } else {
      this.el.classList.remove("listen");
      this.el.querySelector(".head").style.transform = "";
    }
    return this;
  }
  setThinking(thinking) {
    if (thinking) this.setState("thinking");
    return this;
  }

  lookAtUser() { return this; }
  lookAt(_p) { return this; }

  moveTo(target) {
    const cls = MOVE_CLASS[target] || "at-center";
    this.el.classList.remove("at-desk", "at-sofa", "at-bed", "at-window", "at-center");
    this.el.classList.add(cls);
    return this;
  }

  play(animation) {
    if (animation && STATE_CLASS[animation]) this.setState(animation);
    return this;
  }

  showBubble(text) {
    this.bubble.textContent = text;
    this.bubble.style.display = "block";
    this.bubble.classList.remove("fade");
    return this;
  }
  hideBubble() {
    this.bubble.classList.add("fade");
    setTimeout(() => { this.bubble.style.display = "none"; this.bubble.classList.remove("fade"); }, 400);
    return this;
  }

  _stopMouth() {
    if (this._mouthEl) {
      this._mouthEl.style.height = "";
      this._mouthEl.style.borderRadius = "";
    }
  }

  destroy() {
    if (this.el && this.el.parentNode) this.el.parentNode.removeChild(this.el);
  }
}

export default Avatar2D;
