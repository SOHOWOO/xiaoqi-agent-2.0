/* ═══════════════════════════════════════════════════
   小七 · Three.js 3D Avatar（程序化角色）
   真实 Three.js 渲染：卧室地面 + 光照 + 3D 小七。
   无 VRM 模型时的默认 3D 实现；有 VRM 时由 avatar_vrm.js 接管。
   ═══════════════════════════════════════════════════ */

import * as THREE from "/vendor/three/three.module.js";

const MOOD = {
  happy: { blush: 0.5, eye: 1.0, mouth: "smile" },
  sad: { blush: 0.1, eye: 0.7, mouth: "sad" },
  angry: { blush: 0.4, eye: 0.9, mouth: "angry" },
  excited: { blush: 0.6, eye: 1.3, mouth: "bigsmile" },
  neutral: { blush: 0.15, eye: 1.0, mouth: "neutral" },
  thinking: { blush: 0.15, eye: 0.8, mouth: "small" },
  tired: { blush: 0.1, eye: 0.5, mouth: "small" },
};

class AvatarThree {
  constructor() {
    this.container = null;
    this._running = false;
    this._state = "neutral";
    this._speaking = false;
    this._listening = false;
    this._mouthOpen = 0;
    this._lookTarget = null;
    this._targetPos = { x: 0, z: 0 };
    this._bubble = null;

    this._renderer = null;
    this._scene = null;
    this._camera = null;
    this._clock = new THREE.Clock();
    this._parts = {};
    this._groups = {};
  }

  /* ---------- 生命周期 ---------- */

  init(container) {
    this.container = container;
    container.style.position = "absolute";
    container.style.inset = "0";

    // Renderer（透明背景，覆盖在 CSS 房间之上）
    this._renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    this._renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this._renderer.setSize(container.clientWidth || window.innerWidth, container.clientHeight || window.innerHeight);
    container.appendChild(this._renderer.domElement);

    // Scene
    this._scene = new THREE.Scene();
    this._scene.fog = new THREE.Fog(0x1a1c22, 8, 24);

    // Camera
    this._camera = new THREE.PerspectiveCamera(45, (container.clientWidth || 1) / (container.clientHeight || 1), 0.1, 100);
    this._camera.position.set(0, 1.6, 4.2);
    this._camera.lookAt(0, 1.1, 0);

    // Lights
    this._scene.add(new THREE.AmbientLight(0xffe0c0, 0.5));
    const key = new THREE.DirectionalLight(0xffffff, 1.2);
    key.position.set(2, 4, 3);
    this._scene.add(key);
    this._keyLight = key;

    this._buildFloor();
    this._buildAvatar();

    // 气泡（HTML，覆盖在 3D 上）
    this._bubble = document.createElement("div");
    this._bubble.className = "avatar-bubble";
    this._bubble.style.display = "none";
    container.appendChild(this._bubble);

    this._running = true;
    this._renderer.setAnimationLoop(() => this._tick());

    return this;
  }

  _buildFloor() {
    const floor = new THREE.Mesh(
      new THREE.CircleGeometry(6, 48),
      new THREE.MeshStandardMaterial({ color: 0x7a5c46, roughness: 0.9 }),
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = 0;
    this._scene.add(floor);
    this._floor = floor;
  }

  _buildAvatar() {
    const skin = new THREE.MeshStandardMaterial({ color: 0xf4c9a8, roughness: 0.6 });
    const hair = new THREE.MeshStandardMaterial({ color: 0x3a2c22, roughness: 0.8 });
    const dress = new THREE.MeshStandardMaterial({ color: 0xe89474, roughness: 0.7 });
    const leg = new THREE.MeshStandardMaterial({ color: 0x7a5a4a, roughness: 0.8 });

    const root = new THREE.Group();
    root.position.y = 0;

    // 腿
    const legGeo = new THREE.CylinderGeometry(0.09, 0.09, 0.5, 12);
    const legL = new THREE.Mesh(legGeo, leg);
    legL.position.set(-0.12, 0.25, 0);
    const legR = legL.clone();
    legR.position.x = 0.12;
    root.add(legL, legR);

    // 身体
    const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.2, 0.25, 6, 12), dress);
    body.position.y = 0.65;
    root.add(body);

    // 手臂
    const armGeo = new THREE.CylinderGeometry(0.05, 0.05, 0.45, 8);
    const armL = new THREE.Mesh(armGeo, skin);
    armL.position.set(-0.26, 0.75, 0);
    armL.rotation.z = 0.15;
    const armR = armL.clone();
    armR.position.x = 0.26;
    armR.rotation.z = -0.15;
    root.add(armL, armR);
    this._groups.armL = armL;
    this._groups.armR = armR;

    // 头
    const head = new THREE.Group();
    head.position.y = 1.32;
    const headMesh = new THREE.Mesh(new THREE.SphereGeometry(0.2, 24, 24), skin);
    head.add(headMesh);

    // 头发
    const hairMesh = new THREE.Mesh(new THREE.SphereGeometry(0.21, 24, 24, 0, Math.PI * 2, 0, Math.PI * 0.55), hair);
    hairMesh.position.y = 0.02;
    head.add(hairMesh);

    // 眼睛
    const eyeGeo = new THREE.SphereGeometry(0.035, 12, 12);
    const eyeMat = new THREE.MeshStandardMaterial({ color: 0x2b201a });
    const eyeL = new THREE.Mesh(eyeGeo, eyeMat);
    eyeL.position.set(-0.07, 0.03, 0.18);
    const eyeR = eyeL.clone();
    eyeR.position.x = 0.07;
    head.add(eyeL, eyeR);
    this._parts.eyeL = eyeL;
    this._parts.eyeR = eyeR;

    // 腮红
    const blushMat = new THREE.MeshStandardMaterial({ color: 0xf48b8b, transparent: true, opacity: 0.25 });
    const blushGeo = new THREE.SphereGeometry(0.04, 12, 12);
    const blushL = new THREE.Mesh(blushGeo, blushMat);
    blushL.position.set(-0.09, -0.04, 0.18);
    const blushR = blushL.clone();
    blushR.position.x = 0.09;
    head.add(blushL, blushR);
    this._parts.blushL = blushL;
    this._parts.blushR = blushR;

    // 嘴（下颌，用于口型开合）
    const mouth = new THREE.Group();
    mouth.position.set(0, -0.05, 0.19);
    const mouthGeo = new THREE.BoxGeometry(0.08, 0.02, 0.01);
    const mouthMesh = new THREE.Mesh(mouthGeo, new THREE.MeshStandardMaterial({ color: 0x8a5a44 }));
    mouth.add(mouthMesh);
    head.add(mouth);
    this._parts.mouth = mouth;
    this._parts.mouthMat = mouthMesh.material;

    root.add(head);
    this._groups.head = head;

    // 手机（onphone 状态）
    const phone = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.14, 0.01), new THREE.MeshStandardMaterial({ color: 0x222222 }));
    phone.position.set(0.28, 0.9, 0.1);
    phone.visible = false;
    root.add(phone);
    this._parts.phone = phone;

    this._scene.add(root);
    this._root = root;
    this._groups.body = body;
  }

  /* ---------- 状态 ---------- */

  setState(state) {
    this._state = state;

    const mood = MOOD[state] || MOOD.neutral;

    // 腮红
    this._parts.blushL.material.opacity = mood.blush;
    this._parts.blushR.material.opacity = mood.blush;

    // 眼睛大小（眨眼/状态）
    const eyeScale = mood.eye;
    this._parts.eyeL.scale.set(1, eyeScale, 1);
    this._parts.eyeR.scale.set(1, eyeScale, 1);

    // 嘴型
    this._applyMouth(mood.mouth);

    // 手机
    this._parts.phone.visible = state === "proactive" || state === "onphone";

    // 睡觉躺下
    if (state === "sleeping") {
      this._root.rotation.z = -Math.PI / 2;
      this._root.position.z = -1.1;
    } else {
      this._root.rotation.z = 0;
      this._root.position.z = 0;
    }

    return this;
  }

  _applyMouth(kind) {
    const m = this._parts.mouth;
    const mat = this._parts.mouthMat;
    m.rotation.z = 0;
    mat.scale.set(1, 1, 1);

    if (kind === "smile") { m.position.y = -0.06; mat.color.setHex(0x8a5a44); }
    else if (kind === "bigsmile") { m.position.y = -0.08; mat.color.setHex(0x8a5a44); }
    else if (kind === "sad") { m.rotation.z = Math.PI; m.position.y = -0.03; }
    else if (kind === "angry") { mat.color.setHex(0x6b3a2a); }
    else if (kind === "small") { mat.scale.set(0.6, 0.6, 1); }
    else { m.position.y = -0.05; } // neutral
  }

  /* ---------- 说话 / 口型 ---------- */

  talk() { this._speaking = true; return this; }
  stopTalking() { this._speaking = false; this.setMouthOpen(0); return this; }

  setSpeaking(speaking) {
    this._speaking = speaking;
    if (!speaking) this.setMouthOpen(0);
    return this;
  }

  /* mouthOpen: 0.0 ~ 1.0，嘴型开合 */
  setMouthOpen(value) {
    this._mouthOpen = Math.max(0, Math.min(1, value || 0));
    const m = this._parts.mouth;
    m.scale.set(1, 0.6 + this._mouthOpen * 1.6, 1);
    return this;
  }

  setViseme(_viseme) { return this; }

  /* ---------- 视线 / 位置 ---------- */

  lookAtUser() {
    this._lookTarget = this._camera.position.clone();
    return this;
  }
  lookAt(point) {
    this._lookTarget = point ? new THREE.Vector3(point.x || 0, point.y || 0, point.z || 0) : null;
    return this;
  }
  setListening(listening) {
    this._listening = listening;
    if (listening) this.lookAtUser();
    return this;
  }
  setThinking(thinking) {
    if (thinking) this.setState("thinking");
    return this;
  }

  moveTo(target) {
    const positions = {
      center: { x: 0, z: 0 },
      sofa: { x: -1.5, z: 0.8 },
      desk: { x: 1.6, z: 0.4 },
      bed: { x: -1.2, z: -1.1 },
      window: { x: 0, z: 0.6 },
    };
    const p = positions[target] || positions.center;
    this._targetPos = p;
    return this;
  }

  play(animation) {
    if (animation && MOOD[animation]) this.setState(animation);
    return this;
  }

  /* ---------- 气泡 ---------- */

  showBubble(text) {
    this._bubble.textContent = text;
    this._bubble.style.display = "block";
    return this;
  }
  hideBubble() {
    this._bubble.style.display = "none";
    return this;
  }

  /* ---------- 主循环 ---------- */

  _tick() {
    if (!this._running) return;
    const t = this._clock.getElapsedTime();
    const dt = this._clock.getDelta();

    // 呼吸
    const breath = 1 + Math.sin(t * 1.6) * 0.015;
    this._groups.body.scale.set(1, breath, 1);

    // 说话嘴型（带自然抖动）
    if (this._speaking) {
      const amp = 0.5 + 0.5 * Math.sin(t * 9) * Math.sin(t * 13.7);
      this.setMouthOpen(amp);
    }

    // 眨眼
    if (Math.sin(t * 0.7) > 0.985) {
      this._parts.eyeL.scale.y = 0.1;
      this._parts.eyeR.scale.y = 0.1;
    } else {
      const mood = MOOD[this._state] || MOOD.neutral;
      this._parts.eyeL.scale.y = mood.eye;
      this._parts.eyeR.scale.y = mood.eye;
    }

    // 看向用户
    if (this._lookTarget) {
      const head = this._groups.head;
      head.rotation.y += (Math.atan2(this._lookTarget.x - head.position.x, this._lookTarget.z - head.position.z) - head.rotation.y) * 0.1;
    }

    // 移动到目标位置
    const target = new THREE.Vector3(this._targetPos.x, 0, this._targetPos.z);
    this._root.position.x += (target.x - this._root.position.x) * 0.04;
    this._root.position.z += (target.z - this._root.position.z) * 0.04;

    // 光影（跟随昼夜由外部 setLighting 控制）
    this._renderer.render(this._scene, this._camera);
  }

  /* 昼夜光照（由外部周期驱动） */
  setLighting(kind) {
    const intensity = { morning: 0.9, day: 1.2, evening: 0.7, night: 0.35, "deep-night": 0.2 }[kind] ?? 0.8;
    this._keyLight.intensity = intensity;
    return this;
  }

  destroy() {
    this._running = false;
    if (this._renderer) {
      this._renderer.setAnimationLoop(null);
      this._renderer.dispose();
      if (this._renderer.domElement.parentNode) {
        this._renderer.domElement.parentNode.removeChild(this._renderer.domElement);
      }
    }
    if (this._bubble && this._bubble.parentNode) {
      this._bubble.parentNode.removeChild(this._bubble);
    }
  }
}

export default AvatarThree;
