# xiaoqi-agent-2.0

小七 —— 拥有身体、感知、记忆、情绪、关系、主动行为和长期成长能力的 AI 生命体核心。

> **打开小七，不是打开一个 AI，而是推门走进她的生活。**

## 产品形态（Web UI）

小七是一款 **AI 女友软件**，不是聊天机器人。打开页面 = **推门走进小七的房间**。

| 界面 | 说明 |
|------|------|
| 🏠 **虚拟卧室** | 全屏沉浸房间：墙壁/地板/窗户/床/书桌/沙发/台灯/植物/书架。**时间真实改变房间**（昼夜光线、台灯自动开关），小七由 LifeLoop 驱动生活（起床→上班→回家→做饭→沙发→睡觉） |
| 🧍 **小七角色** | Avatar Adapter 架构（`web/avatar/`），2D 实现驱动表情/动作/位置（happy/sad/sleeping/reading/thinking/talking…）；未来无缝切 VRM/Unity |
| 💬 **房间内对话** | 小七说话以**气泡出现在她身边**；点 💬 打开对话抽屉，真实历史 + 已读 |
| ✨ **主动行为** | 小七主动找你：停止动作 → 转向 → 气泡说话（接 `/api/proactive`） |
| 🖱️ **物件交互** | 点床/书桌/沙发→小七过去休息/阅读/放松；点台灯→开关灯；点小七→互动；点空白→她走回房间中央 |
| 💗📅 **关系 / 日程** | 底部栏打开，接真实 Relationship / ScheduleEngine 数据 |
| ⚙️ **设置** | 名字/称呼/HUD 显隐/主动消息/夜间模式/音效（localStorage + 后端 `/api/settings`） |
| 🎤 **语音** | 底部占位（开发中，不伪造；预留 WebRTC/VAD/Whisper/TTS） |

核心原则：**Avatar（房间表现）不是大脑，只表达不解释**。状态通过行为表现（开心动作轻快、孤独发呆），数字只在 HUD/面板可见。

## 架构

```
用户 → Web UI(房间+Avatar) → Web Server(/api/*) → WebRuntime → xiaoqi-bus → 小七核心
                                                    ├── LifeLoop
                                                    ├── Memory 2.0
                                                    ├── Emotion / Neurochemical
                                                    ├── Relationship / Motivation
                                                    ├── Diary / Schedule
                                                    └── Proactive
                                        ↓ AvatarEvent (WebSocket, 可选)
                              Soul-of-Waifu / Live2D / VRM
```

## API

| 端点 | 说明 |
|------|------|
| `GET /api/status` | 生活状态 + 记忆计数 |
| `GET /api/observer` | 综合：情绪/神经化学/关系/日记/回忆/日程 |
| `GET /api/schedule` | 真实日程 |
| `GET /api/memory` | 真实记忆 |
| `GET /api/settings` | 后端设置 |
| `GET /api/proactive` | 主动消息 |
| `POST /api/chat` | 对话 |
| `POST /api/action` | 房间交互 → 行为建议（Web 层，VRM/LifeLoop 未来挂载点） |

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

## 启动

```bash
pip install -r requirements.txt
python web_server.py        # 打开 http://127.0.0.1:8000
```

环境变量：`XIAOQI_WEB_PORT`(8000)、`XIAOQI_SIM_MINUTES_PER_REAL_SECOND`(60)、`XIAOQI_LLM_API_KEY`。

## 测试

```bash
python -m pytest            # 292 passed
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
