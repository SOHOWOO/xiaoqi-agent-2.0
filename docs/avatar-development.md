# 小七 VRM Avatar 开发指南

本阶段目标：让「小七 VRM 即插即用」。

> 把正式 VRM 放入 `web/assets/avatar/xiaoqi.vrm`，启动 `python web_server.py`，
> 系统自动：检测 VRM → 加载 → Humanoid → Expression → LookAt → 眨眼 →
> 嘴型 → LifeLoop → Voice。VRM 缺失/不兼容时自动回退 Three.js / 2D。

## 一、模型制作流程（未来）

从真实形象到可运行的 VRM 1.0：

```text
照片 / 视频
   ↓
AI 建模（照片重建 / 卡通化）
   ↓
3D 资产（FBX / glTF）
   ↓
Blender 整理拓扑与贴图
   ↓
Rig 骨骼绑定（Humanoid）
   ↓
导出 VRM 1.0（Blender VRM 插件）
   ↓
xiaoqi.vrm
   ↓
放入 web/assets/avatar/
   ↓
启动即用
```

### 建议工具

| 环节 | 工具 |
|------|------|
| 照片重建 | Tripo / Meshy / Rodin（或手工建模） |
| 建模/绑定 | Blender + VRM Addon |
| 表情/口型 | Blender 内建立 Blend Shapes（aa/ih/ou/ee/oh + 情绪） |
| 材质 | MToon（VRM 标准材质） |
| 测试 | 本项目的 `/avatar-test` 页面 |

### VRM 1.0 关键要求

- 需要 **Humanoid** 骨骼（auto 或手动指定）
- 需要 **Expression**（happy/sad/angry/surprised/relaxed/blink + 口型 aa/ih/ou/ee/oh）
- 可选 **LookAt**（眼睛注视）
- 可选 **SpringBone**（头发/裙摆物理）

缺少任一项，validator 会给出结构化报告，Avatar 仍能加载（缺失能力自动降级）。

## 二、项目内 VRM 校验

后端提供 `GET /api/vrm-status`，返回：

```json
{
  "valid": true,
  "version": "1.0",
  "humanoid": true,
  "expression": true,
  "lookAt": true,
  "springBone": true,
  "meta": { "name": "小七", "specVersion": "" }
}
```

错误码：

| 码 | 含义 |
|----|------|
| `VRM_NOT_FOUND` | 模型文件不存在 |
| `VRM_LOAD_FAILED` | 文件无法解析（非 GLB / 损坏） |
| `VRM_INVALID` | 合法 GLB 但无 VRM 扩展 |
| `VRM_NO_HUMANOID` | 缺 Humanoid 骨骼 |
| `VRM_UNSUPPORTED_VERSION` | 不支持的 VRM 版本 |

## 三、Avatar 自动选择

```text
启动
 ↓
检测 /api/vrm-status
 ↓
有合法 VRM？→ avatar_vrm.js（VRM）
 ↓ 否
Three.js 可用？→ avatar_three.js（程序化 3D）
 ↓ 否
avatar_2d.js（CSS 2D）
```

**永不白屏。**

## 四、开发测试

开发页面（不进入正式 ZERO UI）：

```text
http://127.0.0.1:8000/avatar-test
```

可测试：表情 / 口型 / 说话(TTS) / 眨眼 / LookAt / 移动 / LifeLoop 状态，并实时查看 VRM validator 结果。

## 五、接入点

- `web/avatar/avatar_adapter.js`：统一接口（上层不感知底层 2D/3D/VRM）
- `web/avatar/avatar_vrm.js`：VRM 加载与能力（Expression/LookAt/眨眼/嘴型/呼吸）
- `web/avatar/avatar_vrm_bundle.js`：自包含 bundle（three + @pixiv/three-vrm，离线可用）
- `vrm_validator.py`：后端 GLB/VRM 解析校验
- `web/app.js`：自动选择 Avatar
- `web/voice/voice_pipeline.js`：语音 → 嘴型联动
