/* ═══════════════════════════════════════════════════
   小七 · Avatar Adapter 统一接口
   未来接 VRM / Unity / WebGL 时只需实现同一接口，
   不必重写整个网页。
   ═══════════════════════════════════════════════════ */

const AvatarAdapter = {
  /* 初始化：传入挂载容器 */
  init(container) {
    throw new Error("AvatarAdapter.init not implemented");
  },

  /* 设置状态：happy/sad/angry/sleeping/idle/talking/
     reading/relaxing/thinking/tired/hungry/proactive */
  setState(state) {
    throw new Error("AvatarAdapter.setState not implemented");
  },

  /* 开始/停止说话（嘴型） */
  talk() {
    throw new Error("AvatarAdapter.talk not implemented");
  },
  stopTalking() {
    throw new Error("AvatarAdapter.stopTalking not implemented");
  },

  /* 看向用户 / 移动到目标（desk/sofa/bed/window） */
  lookAtUser() {
    throw new Error("AvatarAdapter.lookAtUser not implemented");
  },
  moveTo(target) {
    throw new Error("AvatarAdapter.moveTo not implemented");
  },

  /* 播放动作 */
  play(animation) {
    throw new Error("AvatarAdapter.play not implemented");
  },

  /* 显示/隐藏对话框气泡 */
  showBubble(text) {
    throw new Error("AvatarAdapter.showBubble not implemented");
  },
  hideBubble() {
    throw new Error("AvatarAdapter.hideBubble not implemented");
  },

  /* 清理 */
  destroy() {
    throw new Error("AvatarAdapter.destroy not implemented");
  },
};

export default AvatarAdapter;
