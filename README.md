# xiaoqi-agent-2.0

小七 —— 拥有身体、感知、记忆、情绪、关系、主动行为和长期成长能力的 AI 生命体核心。

> **打开小七，不是打开一个 AI，而是推门走进她的生活。**

## 产品形态（Web UI）

小七是一款 **AI 女友软件**，不是聊天机器人。打开页面 = **推门走进小七的房间**。

| 界面 | 说明 |
|------|------|
| 🏠 **虚拟卧室** | 全屏沉浸房间：墙壁/地板/窗户/床/书桌/沙发/台灯/植物/书架。**时间真实改变房间**（昼夜光线、台灯自动开关），小七由 LifeLoop 驱动生活（起床→上班→回家→做饭→沙发→睡觉） |
| 🧍 **3D Avatar** | **Three.js 真实 3D 渲染**（`avatar_three.js`）：程序化 3D 小七 + 表情/嘴型/lookAt/呼吸/眨眼/移动。有 VRM 模型则走 `avatar_vrm.js`（`web/assets/avatar/xiaoqi.vrm`）。WebGL 不可用 → 回退 CSS 2D。统一 `AvatarAdapter` 接口 |
| 🎙️ **实时语音** | 手机界面 🎤 按住说话：麦克风 → STT → 同一 `/api/chat`/Core → TTS → 播放 + **Avatar 嘴型同步**。语音与文字共用 Core（记忆/情绪/关系一致）。STT：浏览器 Web Speech（默认）/ `voice_server.py` faster-whisper（可选）；TTS：浏览器 SpeechSynthesis（开发 fallback，明确区分，未来 GPT-SoVITS/CosyVoice/XTTS） |
| 📱 **小七手机** | 右下角低调入口 → 拟真微信式聊天（气泡/时间/已读/主动消息未读红点/语音按钮） |
| 🧠 **心灵观察站** | 左边缘入口 → 情绪/神经化学/关系/日记/回忆/日程/设置（真实数据） |
| ✨ **主动行为** | 小七主动找你 → 手机收到消息（未读红点），不进房间气泡 |

核心原则：**Avatar（房间表现）不是大脑，只表达不解释**；房间 ZERO UI 不可互动；聊天只在手机；信息只在 Observer。3D/语音不可用时**优雅降级**，App 永不白屏。

## 架构

```
用户 → Web UI(房间+3D Avatar+语音) → Web Server(/api/*) → WebRuntime → xiaoqi-bus → 小七核心
                                                     ├── LifeLoop
                                                     ├── Memory 2.0
                                                     ├── Emotion / Neurochemical
                                                     ├── Relationship / Motivation
                                                     ├── Diary / Schedule
                                                     └── Proactive
  语音：麦克风 → STT(voice_server/浏览器) → /api/chat → TTS → Avatar 嘴型
  3D：Three.js(avatar_three) ← VRM(avatar_vrm) ← 2D fallback(avatar_2d)
```

## 3D Avatar 与 VRM（即插即用）

- **Three.js 3D**（`avatar_three.js`）：程序化 3D 小七（表情/嘴型/呼吸/眨眼/lookAt/移动/昼夜），始终可用
- **VRM 即插即用**（`avatar_vrm.js` + `avatar_vrm_bundle.js`）：把 `web/assets/avatar/xiaoqi.vrm` 放进去 → 自动检测/加载/Humanoid/Expression/LookAt/眨眼/嘴型/LifeLoop/Voice
- **自动选择**：VRM → Three.js → 2D，**永不白屏**，VRM 缺失/不兼容明确记录原因并降级
- **校验**：`GET /api/vrm-status` 结构化检测（`VRM_NOT_FOUND` / `VRM_INVALID` / `VRM_NO_HUMANOID`…）
- **开发测试**：`http://127.0.0.1:8000/avatar-test`（表情/口型/眨眼/LookAt/移动/LifeLoop/说话）
- 制作流程见 `docs/avatar-development.md`

## 语音（Voice）

### 架构

```text
麦克风 → AudioInputAdapter → VAD(BrowserSpeech) → STT → /api/chat → Core → TTS → 音频播放 → 嘴型同步
```

- **STT**：faster-whisper（`voice_server.py`，可选依赖，未安装返回 clear `unavailable`） / 浏览器 Web Speech API（fallback）
- **TTS**：**阿里云 Model Studio Qwen3-TTS**（云端，`voice/providers/alibaba_tts.py`）/ 浏览器 SpeechSynthesis（fallback）
- **VoiceProfile**：`voice/profiles/xiaoqi/profile.json`（provider/voice_id/语速/音调/情绪），voice_id 从环境变量读取，真人素材不入库
- **状态**：`GET /api/voice/status` 返回真实状态（API Key + Voice ID 都配置才 available，不写死）
- **语音与文字共用 Core**（`/api/chat`），记忆/情绪/关系一致
- 语音不可用时自动降级文字聊天，永不崩溃

### 阿里云 Qwen3-TTS（云端语音）

**无需本地模型/GPU**，只需阿里云 Model Studio API Key。

```bash
# 1. 配置（复制 .env.example 为 .env）
XIAOQI_TTS_PROVIDER=alibaba
XIAOQI_ALIBABA_API_KEY=sk-xxx        # 只由后端读取，绝不进 JS/Git
XIAOQI_ALIBABA_MODEL=qwen3-tts-flash
XIAOQI_ALIBABA_VOICE_ID=xxx          # 见下方"声音克隆"
XIAOQI_ALIBABA_REGION=singapore      # 默认新加坡
XIAOQI_ALIBABA_WORKSPACE_ID=xxx      # 创建声音克隆时用

# 2. 查看语音状态
curl http://127.0.0.1:8000/api/voice/status
# 预期：stt.available=?, tts.available=true(配置齐全后), voice_clone.configured=?

# 3. 真实 TTS 测试（配置齐全后）
python -m voice.test_tts "小七今天下班回来啦。"
# 输出保存到 tmp/voice_test/test_tts.wav
```

### 声音克隆（创建小七的 Voice ID）

```bash
# 1. 把参考音频（10s 内清晰人声）放入：
#    voice/profiles/xiaoqi/reference.wav  （已 gitignore）

# 2. 检查音频格式（不自动上传）
python -m voice.clone check

# 3. 显式创建 Voice ID（此刻才上传音频到阿里云）
python -m voice.clone create xiaoqi
# 输出 Voice ID → 填入 .env 的 XIAOQI_ALIBABA_VOICE_ID

# 4. 查询音色
python -m voice.clone list
```

### 安装 faster-whisper（本地 STT）

```bash
pip install faster-whisper
export HF_ENDPOINT=https://hf-mirror.com   # 国内下载模型
python voice_server.py                     # ws://127.0.0.1:8769
```

### 安全

- API Key 只由后端读取（`XIAOQI_ALIBABA_API_KEY` 环境变量），浏览器经 `/api/tts` 后端代理，绝不下发 Key
- `.env`、`voice/profiles/*/reference.wav`、`tmp/` 均在 `.gitignore`
- 未配置时 `/api/voice/status` 明确显示 `unavailable / configured=false`，不伪造

## 启动

```bash
pip install -r requirements.txt
python web_server.py          # Web: http://127.0.0.1:8000
python voice_server.py        # 语音服务(可选, faster-whisper): ws://127.0.0.1:8769
```

- 3D：打开页面即渲染（Three.js 已 vendor 到 `web/vendor/`，离线可用）
- 语音：浏览器内点手机 🎤 按住说话（默认浏览器 STT+TTS，零依赖）
- 想用本地 faster-whisper：`pip install faster-whisper` 后启动 `voice_server.py`，并在 `.env` 设 `STT_PROVIDER=faster-whisper`
- VRM 模型：把合法授权的 `xiaoqi.vrm` 放入 `web/assets/avatar/`（见其 README）

## API

| 端点 | 说明 |
|------|------|
| `GET /api/status` | 生活状态 + 记忆计数 |
| `GET /api/observer` | 综合：情绪/神经化学/关系/日记/回忆/日程 |
| `GET /api/schedule` / `/api/memory` / `/api/settings` | 真实日程/记忆/设置 |
| `GET /api/proactive` | 主动消息 |
| `POST /api/chat` | 对话（文字与语音共用） |
| `voice_server.py` | WebSocket：音频 → STT → 文本（faster-whisper 可选） |

## 架构

```
用户 → 小七手机(Web API) → WebRuntime → xiaoqi-bus → 小七核心
                                                    ├── LifeLoop
                                                    ├── Memory 2.0
                                                    ├── Emotion / Neurochemical
                                                    ├── Relationship / Motivation
                                                    ├── Diary / Schedule
                                                    └── Proactive
                                        ↓ AvatarEvent (WebSocket, 可选)
                              Soul-of-Waifu / Live2D / VRM
```

## 测试

```bash
python -m pytest            # 302 passed
python -m life_lab.runner   # Life Lab 离线生命实验（001-004, 008-010）
```

## 3.0.1 稳定化（核心生命系统重构）

在阶段1生命核心基础上，依据"状态连续 / 时间自洽 / 关系自演化 / 记忆长期稳定 / 系统高容错"原则完成稳定化：

| Commit | 内容 |
|--------|------|
| **A 时间基座** | 移除 LifeLoop 启动立即持久化（启动只读）；Simulator 一次计算生活事件 + 引擎按 `MAX_TICK_STEP=15min` 子步积分（两个时间尺度）；全局注入模拟时间（消除子模块 `datetime.now()` 混用）；神经化学/情绪改为**时间绑定指数衰减 EMA**（大步长与小步长演化数学一致） |
| **B 关系 2.0** | 多维关系模型（Trust/Attachment/Familiarity/SharedExperience）+ 事件驱动（互动/互助/冲突/安慰）+ 时间衰减；接入 LifeLoop 主循环 + SQLite 持久化 |
| **C 数值稳定** | 全局 clamp + 指数衰减 + EMA 平滑 |
| **D 动机层** | `core/motivation/`：`State → Motivation → Action Planner → Proactive`，提炼高阶动机（渴望联系/想安慰/想分享/想提醒/想玩耍） |
| **E 记忆生命周期** | `core/motivation/lifecycle`：定期巩固（短期→语义）+ 沉淀降权（软遗忘，不硬删） |
| **F 工程稳定** | SQLite WAL 模式；运行时状态版本号（`STATE_VERSION=3.0` + 旧库自动迁移）；LLM 优雅降级（Diary 异常→模板 + 重试标记） |
| **G xiaoqi-bus** | `core/bus/` 非阻塞内存事件总线，发布规范化核心事件（user_interaction/emotion_change/state_update/proactive_triggered/diary_written/memory_consolidated） |

### 核心机制（参考 Soul-of-Waifu / Open-LLM-VTuber 设计）

- **四层认知记忆**：Episodic（事件）/ Semantic（事实）/ Relationship（关系）/ Diary（日记）
- **记忆压缩**：相似记忆自动聚类归纳为长期语义记忆
- **冲突解决**：新旧矛盾不覆盖，生成带时间上下文的演变记忆（如"过去喜欢咖啡，现在已减少"）
- **崩溃安全写入**：SQLite 事务原子持久化 + WAL
- **行为能量成本**：说话/思考消耗能量，能量低时减少主动
- **睡眠状态机**：精力阈值驱动睡眠/唤醒，睡眠时不打扰
- **EMA 情绪平滑**：时间绑定指数衰减，步长不变
- **动机驱动行为**：底层状态 → 高阶动机 → 行为规划 → 主动消息

## 目录结构

```
xiaoqi-agent/
├── core/
│   ├── bus/               # xiaoqi-bus 事件总线（Pub/Sub）
│   ├── neurochemical/     # 神经化学引擎（时间绑定 EMA）
│   ├── emotion/           # 情绪引擎
│   ├── memory/            # 记忆系统（四层 + 巩固 + 冲突 + 生命周期）
│   ├── diary/             # 日记引擎（LLM 优雅降级）
│   ├── motivation/        # 动机层（Desire → Planner）
│   ├── proactive/         # 主动行为引擎（门控/冷却/睡眠保护）
│   ├── relationship/      # 多维关系引擎（Trust/Attachment/...）
│   ├── life_loop.py       # 持续生命循环（双时间尺度积分 + 事件发布）
│   ├── config.py          # 统一配置
│   ├── ...                # 2.0 原有：simulator/energy/schedule/events 等
├── web_runtime.py         # 网页运行时（SQLite 持久化 + 引擎恢复）
├── web_server.py          # HTTP 服务器
├── tests/                 # 测试（232+ 通过）
└── requirements.txt
```

## 测试

```bash
pip install -r requirements.txt
python -m pytest
```

## Life Lab 离线生命实验

```bash
python -m life_lab.runner
```

独立观察者框架，验证小七在**无用户输入 / 无 LLM / 无 Avatar** 下独立运行 7 天（672 × 15min tick）：
- 输出 `logs/life_lab/<run_id>/state.jsonl`（672 行状态快照）
- 健康检查：能量范围 / 情绪演化 / 关系合理变化
- 实验 001 lonely_week：energy∈[0,1]、lonely 0.13→0.73、attachment 0.2→0.189、主动 5 次、日记 7 篇 —— **PASS**

实验 → 日志 → 报告 → 修改 core → 再实验，形成生命测试闭环。
