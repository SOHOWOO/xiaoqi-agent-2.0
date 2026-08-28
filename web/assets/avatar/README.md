# Avatar 模型目录

此目录用于放置**拥有合法使用权**的「小七」VRM 模型。

## 使用方式

1. 将合法授权的 `.vrm` 模型文件放入本目录，命名为 `xiaoqi.vrm`：

   ```
   web/assets/avatar/xiaoqi.vrm
   ```

2. 前端 `avatar_vrm.js` 默认从 `/assets/avatar/xiaoqi.vrm` 加载。

3. 也可通过全局变量配置模型地址（在 index.html 中）：

   ```html
   <script>window.AVATAR_MODEL_URL = "/assets/avatar/your_model.vrm";</script>
   ```

## 加载回退

- 模型存在 + three-vrm 可用 → 加载真实 VRM
- 模型缺失 / 加载失败 → 回退 `avatar_three.js`（Three.js 程序化 3D 小七）
- WebGL 不可用 → 回退 `avatar_2d.js`（CSS 2D 小七）

## 注意

请勿从互联网随意下载版权不明的模型。本项目不内置任何 VRM 模型文件。
