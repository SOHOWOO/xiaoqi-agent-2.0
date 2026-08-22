# xiaoqi-agent-2.0

小七 —— 拥有身体、感知、记忆、情绪、关系、主动行为和长期成长能力的 AI 生命体核心。

## 架构总览

```
                用户
                 │
        ┌────────┴────────┐
        │  感知系统        │   ← 阶段2：Open-LLM-VTuber（语音/视觉）
        │  Voice / Vision │
        └────────┬────────┘
                 │
        ┌────────┴────────┐
        │  生命核心        │   ← 本项目（xiaoqi-agent）
        │  Memory/Emotion │
        │  Neurochemical  │
        │  Diary/Proactive│
        └────────┬────────┘
                 │
        ┌────────┴────────┐
        │  身体表现        │   ← 阶段3：Soul-of-Waifu（VRM/表情/桌宠）
        │  Avatar         │
        └────────┬────────┘
                 │
               用户
```

三个系统通过 `xiaoqi-bus` 事件协议解耦，未来可无痛替换 Unity / Unreal / 网页 / 手机端。

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

## 阶段路线

- **阶段1（已完成）**：升级 xiaoqi-agent 为生命核心 —— Memory 2.0 / Emotion / Neurochemical / Diary / Proactive
- **阶段1.5（已完成）**：核心生命系统稳定化 —— 双时间尺度积分 / EMA 数值一致 / 关系 2.0 / 动机层 / 记忆生命周期 / WAL + 版本 / LLM 降级 / xiaoqi-bus
- **阶段2**：接入 Open-LLM-VTuber（实时语音/VAD/Whisper/打断/TTS/视觉）—— 实现其 `AgentInterface`
- **阶段3**：接入 Soul-of-Waifu（VRM 身体/表情/动作/桌宠）—— 通过 `Actions.expressions` 表情通道
