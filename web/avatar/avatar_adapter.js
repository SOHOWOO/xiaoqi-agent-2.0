/* ═══════════════════════════════════════════════════
   小七 · Avatar Adapter 统一接口
   avatar_2d.js / avatar_three.js / avatar_vrm.js 均实现此接口。
   上层业务不知道底层到底是 2D、Three.js 还是 VRM。
   ═══════════════════════════════════════════════════ */

const AvatarAdapter = {
  /* 初始化：返回 this（失败应抛出，由上层回退） */
  init(container) {
    throw new Error("AvatarAdapter.init not implemented");
  },

  /* 设置情绪状态：
     idle/happy/sad/angry/excited/sleeping/tired/hungry/
     thinking/proactive/onphone */
  setState(state) {
    throw new Error("AvatarAdapter.setState not implemented");
  },

  /* 说话（启动/停止） */
  talk() { throw new Error("AvatarAdapter.talk not implemented"); },
  stopTalking() { throw new Error("AvatarAdapter.stopTalking not implemented"); },
  setSpeaking(speaking) { throw new Error("AvatarAdapter.setSpeaking not implemented"); },

  /* 嘴型：mouthOpen 0~1 */
  setMouthOpen(value) { throw new Error("AvatarAdapter.setMouthOpen not implemented"); },
  setViseme(viseme) { throw new Error("AvatarAdapter.setViseme not implemented"); },

  /* 聆听 / 思考 */
  setListening(listening) { throw new Error("AvatarAdapter.setListening not implemented"); },
  setThinking(thinking) { throw new Error("AvatarAdapter.setThinking not implemented"); },

  /* 视线 */
  lookAtUser() { throw new Error("AvatarAdapter.lookAtUser not implemented"); },
  lookAt(point) { throw new Error("AvatarAdapter.lookAt not implemented"); },

  /* 位置（desk/sofa/bed/window/center） */
  moveTo(target) { throw new Error("AvatarAdapter.moveTo not implemented"); },

  /* 播放动作 */
  play(animation) { throw new Error("AvatarAdapter.play not implemented"); },

  /* 昼夜光照 */
  setLighting(kind) { throw new Error("AvatarAdapter.setLighting not implemented"); },

  /* 气泡 */
  showBubble(text) { throw new Error("AvatarAdapter.showBubble not implemented"); },
  hideBubble() { throw new Error("AvatarAdapter.hideBubble not implemented"); },

  destroy() { throw new Error("AvatarAdapter.destroy not implemented"); },
};

export default AvatarAdapter;
