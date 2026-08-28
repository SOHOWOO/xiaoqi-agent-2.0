# Avatar 模型目录

此目录用于放置**拥有合法使用权**的「小七」VRM 模型。

## 使用方式

1. 将合法授权的 `.vrm` 模型文件放入本目录，命名为 `xiaoqi.vrm`：

   ```
   web/assets/avatar/xiaoqi.vrm
   ```

2. 启动 `python web_server.py`，系统自动检测并加载。

3. 也可通过全局变量配置模型地址（在 index.html 中）：

   ```html
   <script>window.AVATAR_MODEL_URL = "/assets/avatar/your_model.vrm";</script>
   ```

## 自动检测

启动后后端 `GET /api/vrm-status` 会返回结构化校验结果：

```json
{ "valid": true, "version": "1.0", "humanoid": true,
  "expression": true, "lookAt": true, "springBone": true }
```

缺失能力（如无 LookAt / 无口型）会安全降级，不会崩溃。

## 加载回退

- 模型存在 + 可解析 + 有 Humanoid → 加载真实 VRM
- 模型缺失 / 不兼容 / 加载失败 → 回退 `avatar_three.js`（Three.js 程序化 3D 小七）
- WebGL 不可用 → 回退 `avatar_2d.js`（CSS 2D 小七）

## 开发验证

```text
http://127.0.0.1:8000/avatar-test
```

可测试表情 / 口型 / 眨眼 / LookAt / 移动 / LifeLoop / 说话。

## 注意

请勿从互联网随意下载版权不明的模型。本项目不内置任何 VRM 模型文件。

制作流程见 `docs/avatar-development.md`。
