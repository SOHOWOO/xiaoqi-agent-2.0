/* ═══════════════════════════════════════════════════
   小七 · 2D Avatar（CSS 角色实现）
   第一版用 CSS 人物占位，未来可切换 avatar_vrm.js
   ═══════════════════════════════════════════════════ */

import AvatarAdapter from "./avatar_adapter.js";

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
    this.overlay = null;
    this.bubble = null;
    this._state = "idle";
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

    container.appendChild(this.el);

    return this;
  }

  setState(state) {
    this._state = state;
    const cls = STATE_CLASS[state] || "idle";
    const moodCls = ["smile", "sad", "angry", "excited"].includes(cls)
      ? cls
      : "neutral";

    this.el.classList.remove(
      "idle", "smile", "sad", "angry", "excited",
      "sleep", "talk", "read", "relax", "think", "slow", "onphone",
      "neutral",
    );
    this.el.classList.add(cls, moodCls);
    return this;
  }

  talk() {
    this.el.classList.add("talk");
  }

  stopTalking() {
    this.el.classList.remove("talk");
  }

  lookAtUser() {
    this.el.classList.add("look");
  }

  moveTo(target) {
    const cls = MOVE_CLASS[target] || "at-center";
    this.el.classList.remove(
      "at-desk", "at-sofa", "at-bed", "at-window", "at-center",
    );
    this.el.classList.add(cls);
    return this;
  }

  play(animation) {
    if (animation && STATE_CLASS[animation]) {
      this.setState(animation);
    }
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
    setTimeout(() => {
      this.bubble.style.display = "none";
      this.bubble.classList.remove("fade");
    }, 400);
    return this;
  }

  destroy() {
    if (this.el && this.el.parentNode) {
      this.el.parentNode.removeChild(this.el);
    }
  }
}

export default Avatar2D;
