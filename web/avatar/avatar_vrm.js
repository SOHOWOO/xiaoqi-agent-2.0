/* ═══════════════════════════════════════════════════
   小七 · VRM Avatar
   通过 AVATAR_MODEL_URL（或 import map）加载真实 VRM 模型。
   模型不存在 / 加载失败 / three-vrm 不可用 -> 抛出异常，
   由上层回退到 AvatarThree（程序化 3D）或 Avatar2D。
   ═══════════════════════════════════════════════════ */

import * as THREE from "/vendor/three/three.module.js";

const AVATAR_MODEL_URL =
  (globalThis.AVATAR_MODEL_URL || "") || "/assets/avatar/xiaoqi.vrm";

const POSITIONS = {
  center: { x: 0, z: 0 },
  sofa: { x: -1.5, z: 0.8 },
  desk: { x: 1.6, z: 0.4 },
  bed: { x: -1.2, z: -1.1 },
  window: { x: 0, z: 0.6 },
};

class AvatarVRM {
  constructor() {
    this.container = null;
    this._running = false;
    this._speaking = false;
    this._lookTarget = null;
    this._targetPos = { x: 0, z: 0 };
    this._bubble = null;

    this._renderer = null;
    this._scene = null;
    this._camera = null;
    this._vrm = null;
    this._clock = new THREE.Clock();
    this._blink = 0;
  }

  async init(container) {
    this.container = container;
    container.style.position = "absolute";
    container.style.inset = "0";

    const w = container.clientWidth || window.innerWidth;
    const h = container.clientHeight || window.innerHeight;

    this._renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    this._renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this._renderer.setSize(w, h);
    container.appendChild(this._renderer.domElement);

    this._scene = new THREE.Scene();
    this._camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 100);
    this._camera.position.set(0, 1.6, 4.2);
    this._camera.lookAt(0, 1.1, 0);

    this._scene.add(new THREE.AmbientLight(0xffe0c0, 0.6));
    const key = new THREE.DirectionalLight(0xffffff, 1.2);
    key.position.set(2, 4, 3);
    this._scene.add(key);
    this._keyLight = key;

    // 加载 VRM（失败则抛出，触发 fallback）
    let GLTFLoader;
    try {
      GLTFLoader = (await import("/vendor/three/jsm/loaders/GLTFLoader.js")).GLTFLoader;
    } catch {
      throw new Error("three-vrm loader unavailable");
    }

    let VRMLoaderPlugin;
    try {
      const mod = await import("/vendor/three-vrm/three-vrm.module.js");
      VRMLoaderPlugin = mod.VRMLoaderPlugin;
    } catch {
      throw new Error("three-vrm not vendored");
    }

    const loader = new GLTFLoader();
    loader.register((parser) => new VRMLoaderPlugin(parser));

    const gltf = await loader.loadAsync(AVATAR_MODEL_URL);
    this._vrm = gltf.userData.vrm;

    this._scene.add(this._vrm.scene);
    this._vrm.scene.position.y = 0;

    this._bubble = document.createElement("div");
    this._bubble.className = "avatar-bubble";
    this._bubble.style.display = "none";
    container.appendChild(this._bubble);

    this._running = true;
    this._renderer.setAnimationLoop(() => this._tick());
    return this;
  }

  setState(state) {
    const name = {
      happy: "happy",
      excited: "happy",
      calm: "neutral",
      lonely: "sad",
      sad: "sad",
      angry: "angry",
      tired: "neutral",
      sleeping: "relaxed",
      neutral: "neutral",
    }[state] || "neutral";

    this._setExpression(name);
    if (state === "sleeping") this._vrm.scene.rotation.z = -Math.PI / 2;
    else this._vrm.scene.rotation.z = 0;
    return this;
  }

  _setExpression(name) {
    if (!this._vrm || !this._vrm.expressionManager) return;
    const manager = this._vrm.expressionManager;
    const names = manager.expressions || [];
    names.forEach((e) => manager.setValue(e.expressionName, 0));
    if (names.some((e) => e.expressionName === name)) {
      manager.setValue(name, 1);
    }
  }

  talk() { this._speaking = true; return this; }
  stopTalking() { this._speaking = false; return this; }
  setSpeaking(speaking) { this._speaking = speaking; return this; }
  setMouthOpen(value) {
    if (this._vrm && this._vrm.expressionManager) {
      this._vrm.expressionManager.setValue("aa", Math.max(0, Math.min(1, value || 0)));
    }
    return this;
  }
  setViseme(_v) { return this; }
  setListening(l) { if (l) this.lookAtUser(); return this; }
  setThinking(t) { if (t) this.setState("thinking"); return this; }

  lookAtUser() { this._lookTarget = this._camera.position.clone(); return this; }
  lookAt(p) {
    this._lookTarget = p ? new THREE.Vector3(p.x || 0, p.y || 0, p.z || 0) : null;
    return this;
  }

  moveTo(target) {
    const p = POSITIONS[target] || POSITIONS.center;
    this._targetPos = p;
    return this;
  }

  play(animation) { if (animation) this.setState(animation); return this; }
  showBubble(text) { this._bubble.textContent = text; this._bubble.style.display = "block"; return this; }
  hideBubble() { this._bubble.style.display = "none"; return this; }

  setLighting(kind) {
    const intensity = { morning: 0.9, day: 1.2, evening: 0.7, night: 0.35, "deep-night": 0.2 }[kind] ?? 0.8;
    this._keyLight.intensity = intensity;
    return this;
  }

  _tick() {
    if (!this._running || !this._vrm) return;
    const dt = this._clock.getDelta();
    const t = this._clock.getElapsedTime();

    // 呼吸
    this._vrm.update(dt);

    // 眨眼
    this._blink += dt;
    if (this._blink > 3) {
      if (this._vrm.expressionManager) this._vrm.expressionManager.setValue("blink", 1);
      if (this._blink > 3.2) { this._vrm.expressionManager.setValue("blink", 0); this._blink = 0; }
    }

    // 说话嘴型
    if (this._speaking) {
      this.setMouthOpen(0.5 + 0.5 * Math.sin(t * 9) * Math.sin(t * 13.7));
    }

    // 移动
    this._vrm.scene.position.x += (this._targetPos.x - this._vrm.scene.position.x) * 0.04;
    this._vrm.scene.position.z += (this._targetPos.z - this._vrm.scene.position.z) * 0.04;

    // 视线
    if (this._lookTarget && this._vrm.lookAt) {
      this._vrm.lookAt.target = this._lookTarget;
    }

    this._renderer.render(this._scene, this._camera);
  }

  destroy() {
    this._running = false;
    if (this._renderer) {
      this._renderer.setAnimationLoop(null);
      this._renderer.dispose();
      if (this._renderer.domElement.parentNode) this._renderer.domElement.parentNode.removeChild(this._renderer.domElement);
    }
    if (this._bubble && this._bubble.parentNode) this._bubble.parentNode.removeChild(this._bubble);
  }
}

export default AvatarVRM;
