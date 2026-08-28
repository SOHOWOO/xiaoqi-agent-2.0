/* ═══════════════════════════════════════════════════
   小七 · VRM Avatar 占位桩
   未来接真正 VRM 模型时实现 avatar_adapter.js 接口
   ═══════════════════════════════════════════════════ */

import AvatarAdapter from "./avatar_adapter.js";

class AvatarVRM {
  constructor() {
    this.container = null;
    this._state = "idle";
    this._target = null;
    this._bubble = null;
  }

  init(container) {
    this.container = container;
    const placeholder = document.createElement("div");
    placeholder.style.cssText =
      "width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:14px;";
    placeholder.textContent = "🦋 VRM Avatar · 开发中";
    container.appendChild(placeholder);
    return this;
  }

  setState(state) { this._state = state; return this; }
  talk() { return this; }
  stopTalking() { return this; }
  lookAtUser() { return this; }
  moveTo(target) { this._target = target; return this; }
  play(animation) { return this; }
  showBubble(text) { return this; }
  hideBubble() { return this; }
  destroy() { return this; }
}

export default AvatarVRM;