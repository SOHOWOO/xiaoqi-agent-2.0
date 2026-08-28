/* ═══════════════════════════════════════════════════
   小七 · VRM Avatar（即插即用）
   - 自动检测 web/assets/avatar/xiaoqi.vrm（经 /api/vrm-status）
   - 从 avatar_vrm_bundle.js（含 three + @pixiv/three-vrm）动态加载
   - VRM 1.0 优先，0.x 兼容
   - Expression / LookAt / 眨眼 / 嘴型 / 呼吸 / Idle / LifeLoop
   - 模型不存在 / 不兼容 / 加载失败 -> 抛出明确错误，上层 fallback
   ═══════════════════════════════════════════════════ */

const AVATAR_MODEL_URL =
  (globalThis.AVATAR_MODEL_URL || "") || "/assets/avatar/xiaoqi.vrm";

const POSITIONS = {
  center: { x: 0, z: 0 },
  sofa: { x: -1.5, z: 0.8 },
  desk: { x: 1.6, z: 0.4 },
  bed: { x: -1.2, z: -1.1 },
  window: { x: 0, z: 0.6 },
};

/* 情绪 -> VRM 表情（安全 fallback） */
const EMOTION_EXPRESSION = {
  happy: "happy",
  excited: "happy",
  calm: "neutral",
  lonely: "sad",
  sad: "sad",
  angry: "angry",
  surprised: "surprised",
  relaxed: "relaxed",
  tired: "relaxed",
  thinking: "neutral",
  sleeping: "relaxed",
  neutral: "neutral",
};

/* 口型 -> VRM 标准口型（aa/ih/ou/ee/oh），缺失时安全跳过 */
const VISEME_PRIORITY = ["aa", "ih", "ou", "ee", "oh", "mouth", "open"];

class AvatarVRM {
  constructor() {
    this.container = null;
    this._running = false;
    this._speaking = false;
    this._listening = false;
    this._lookTarget = null;
    this._targetPos = { x: 0, z: 0 };
    this._bubble = null;

    this._renderer = null;
    this._scene = null;
    this._camera = null;
    this._vrm = null;
    this._clock = null;
    this._lookYaw = 0;
    this._blinkTimer = 0;
    this._blinkInterval = 3 + Math.random() * 3;
    this._blinkState = 0;
    this._availableExpressions = new Set();
    this._availableVisemes = [];
    this._THREE = null;
    this._VRMLoaderPlugin = null;
  }

  /* ---------- 加载 ---------- */

  async init(container) {
    this.container = container;
    container.style.position = "absolute";
    container.style.inset = "0";

    const w = container.clientWidth || window.innerWidth;
    const h = container.clientHeight || window.innerHeight;

    // 动态加载自包含 bundle（含 three + @pixiv/three-vrm）
    const { THREE, VRMLoaderPlugin } = await this._loadBundle();
    this._THREE = THREE;
    this._VRMLoaderPlugin = VRMLoaderPlugin;

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

    const GLTFLoader = (await import("/vendor/three/jsm/loaders/GLTFLoader.js")).GLTFLoader;
    const loader = new GLTFLoader();
    loader.register((parser) => new VRMLoaderPlugin(parser));

    const gltf = await loader.loadAsync(AVATAR_MODEL_URL);
    const vrm = gltf.userData.vrm;

    if (!vrm) {
      throw new Error("VRM_INVALID: no VRM extension in model");
    }

    this._vrm = vrm;
    this._scene.add(vrm.scene);
    vrm.scene.position.y = 0;
    vrm.scene.position.x = 0;
    vrm.scene.position.z = 0;

    // 探测可用表情与口型
    this._collectExpressions();

    this._bubble = document.createElement("div");
    this._bubble.className = "avatar-bubble";
    this._bubble.style.display = "none";
    container.appendChild(this._bubble);

    this._clock = new THREE.Clock();
    this._running = true;
    this._renderer.setAnimationLoop(() => this._tick());

    return this;
  }

  async _loadBundle() {
    try {
      return await import("/avatar/avatar_vrm_bundle.js");
    } catch (error) {
      throw new Error("VRM_LOAD_FAILED: three-vrm bundle unavailable: " + error.message);
    }
  }

  _collectExpressions() {
    if (!this._vrm.expressionManager) return;
    const manager = this._vrm.expressionManager;
    const names = (manager.expressions || []).map((e) => e.expressionName);
    this._availableExpressions = new Set(names);
    this._availableVisemes = VISEME_PRIORITY.filter((v) => names.includes(v));
  }

  /* ---------- 状态 / 表情 ---------- */

  setState(state) {
    const expr = EMOTION_EXPRESSION[state] || "neutral";
    this.setExpression(expr);
    if (state === "sleeping") this._vrm.scene.rotation.z = -Math.PI / 2;
    else this._vrm.scene.rotation.z = 0;
    return this;
  }

  setExpression(name) {
    if (!this._vrm || !this._vrm.expressionManager) return this;
    const manager = this._vrm.expressionManager;
    if (!this._availableExpressions.has(name)) return this; // 安全 fallback
    manager.setValue(name, 1);
    return this;
  }

  /* ---------- 说话 / 嘴型 ---------- */

  talk() { this._speaking = true; return this; }
  stopTalking() { this._speaking = false; this.setMouthOpen(0); return this; }
  setSpeaking(speaking) {
    this._speaking = speaking;
    if (!speaking) this.setMouthOpen(0);
    return this;
  }

  setMouthOpen(value) {
    if (!this._vrm || !this._vrm.expressionManager) return this;
    const v = Math.max(0, Math.min(1, value || 0));
    const manager = this._vrm.expressionManager;
    // 用第一个可用口型（aa/ih/ou/ee/oh）
    const viseme = this._availableVisemes[0];
    if (viseme) manager.setValue(viseme, v);
    else if (this._availableExpressions.has("open")) manager.setValue("open", v);
    return this;
  }

  setViseme(name) {
    if (this._vrm && this._vrm.expressionManager) {
      const manager = this._vrm.expressionManager;
      VISEME_PRIORITY.forEach((v) => manager.setValue(v, 0));
      if (name && this._availableExpressions.has(name)) manager.setValue(name, 1);
    }
    return this;
  }

  /* ---------- 聆听 / 思考 ---------- */

  setListening(listening) {
    this._listening = listening;
    if (listening) this.lookAtUser();
    return this;
  }
  setThinking(thinking) {
    if (thinking) this.setState("thinking");
    return this;
  }

  /* ---------- 视线（平滑插值，不瞬间跳动） ---------- */

  lookAtUser() {
    this._lookTarget = this._camera.position.clone();
    return this;
  }
  lookAt(p) {
    this._lookTarget = p ? new THREE.Vector3(p.x || 0, p.y || 0, p.z || 0) : null;
    return this;
  }

  _updateLook(dt) {
    if (!this._vrm || !this._vrm.lookAt || !this._THREE) return;
    const T = this._THREE;
    const target = this._lookTarget || new T.Vector3(Math.sin(this._lookYaw) * 2, 1.1, 0);
    const blended = new T.Vector3().lerpVectors(
      target, new T.Vector3(0, 1.1, 0), 0.2,
    );
    this._vrm.lookAt.target = blended;
    return this;
  }

  /* ---------- 位置 / 动作 ---------- */

  moveTo(target) {
    const p = POSITIONS[target] || POSITIONS.center;
    this._targetPos = p;
    return this;
  }

  play(animation) {
    if (animation) this.setState(animation);
    return this;
  }

  /* ---------- 气泡 / 光照 ---------- */

  showBubble(text) { this._bubble.textContent = text; this._bubble.style.display = "block"; return this; }
  hideBubble() { this._bubble.style.display = "none"; return this; }

  setLighting(kind) {
    const intensity = { morning: 0.9, day: 1.2, evening: 0.7, night: 0.35, "deep-night": 0.2 }[kind] ?? 0.8;
    this._keyLight.intensity = intensity;
    return this;
  }

  /* ---------- 主循环（呼吸 / 眨眼 / 嘴型 / 移动 / 视线） ---------- */

  _tick() {
    if (!this._running || !this._vrm) return;
    const dt = this._clock.getDelta();
    const t = this._clock.getElapsedTime();

    this._vrm.update(dt);

    // 眨眼：随机间隔，左右同步为主
    if (this._vrm.expressionManager) {
      this._blinkTimer += dt;
      if (this._blinkTimer >= this._blinkInterval && this._blinkState === 0) {
        this._blinkState = 1;
        this._vrm.expressionManager.setValue("blink", 1);
        if (this._availableExpressions.has("blinkLeft")) this._vrm.expressionManager.setValue("blinkLeft", 1);
      }
      if (this._blinkState === 1) {
        if (this._blinkTimer >= this._blinkInterval + 0.12) {
          this._blinkState = 2;
          this._vrm.expressionManager.setValue("blink", 0);
          if (this._availableExpressions.has("blinkLeft")) this._vrm.expressionManager.setValue("blinkLeft", 0);
        }
      }
      if (this._blinkState === 2) {
        this._blinkTimer = 0;
        this._blinkInterval = 2.4 + Math.random() * 3.6;
        this._blinkState = 0;
      }
    }

    // 说话嘴型
    if (this._speaking) {
      this.setMouthOpen(0.5 + 0.5 * Math.sin(t * 9) * Math.sin(t * 13.7));
    }

    // 呼吸（VRM 自带动画 + 轻微身体起伏）
    const breath = 1 + Math.sin(t * 1.5) * 0.01;
    if (this._vrm.scene) this._vrm.scene.scale.y = breath;

    // 移动
    this._vrm.scene.position.x += (this._targetPos.x - this._vrm.scene.position.x) * 0.04;
    this._vrm.scene.position.z += (this._targetPos.z - this._vrm.scene.position.z) * 0.04;

    // 视线
    this._updateLook(dt);

    this._renderer.render(this._scene, this._camera);
  }

  update() { return this; }

  /* ---------- 清理 ---------- */

  dispose() { this.destroy(); }

  destroy() {
    this._running = false;
    if (this._renderer) {
      this._renderer.setAnimationLoop(null);
      this._renderer.dispose();
      if (this._renderer.domElement.parentNode) this._renderer.domElement.parentNode.removeChild(this._renderer.domElement);
    }
    if (this._bubble && this._bubble.parentNode) this._bubble.parentNode.removeChild(this._bubble);
    this._vrm = null;
  }
}

export default AvatarVRM;
