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

## 3.0 新增（阶段1：生命核心升级）

| 模块 | 说明 | 位置 |
|------|------|------|
| **Neurochemical Engine** | 神经化学模拟：多巴胺/血清素/催产素/皮质醇/内啡肽/去甲肾上腺素，随时间衰减、受刺激改变，驱动动机/依恋/压力/好奇 | `core/neurochemical/` |
| **Emotion Engine** | 多维情绪（开心/孤独/兴奋/焦虑/生气/平静），由神经化学映射 + 事件冲击 + 时间衰减 | `core/emotion/` |
| **Memory 2.0** | 四层认知记忆（情景/语义/关系/日记）+ 自动压缩归纳 + 冲突解决（记录变化而非覆盖） | `core/memory/` |
| **Diary Engine** | 跨天自动写第一人称日记（可接 LLM），记忆回顾 | `core/diary/` |
| **Proactive Engine 2.0** | 多驱动主动行为：情绪/神经化学/时间作息/日记/记忆关注 → 统一门控决策 | `core/proactive/` |

### 核心机制（参考 Soul-of-Waifu / Open-LLM-VTuber 设计）

- **四层认知记忆**：Episodic（事件）/ Semantic（事实）/ Relationship（关系）/ Diary（日记）
- **记忆压缩**：相似记忆自动聚类归纳为长期语义记忆
- **冲突解决**：新旧矛盾不覆盖，生成带时间上下文的演变记忆（如"过去喜欢咖啡，现在已减少"）
- **崩溃安全写入**：SQLite 事务原子持久化
- **行为能量成本**：说话/思考消耗能量，能量低时减少主动
- **睡眠状态机**：精力阈值驱动睡眠/唤醒，睡眠时不打扰
- **EMA 情绪平滑**：避免情绪突变

## 目录结构

```
xiaoqi-agent/
├── core/
│   ├── neurochemical/     # 神经化学引擎
│   ├── emotion/           # 情绪引擎
│   ├── memory/            # 记忆系统（含 Memory 2.0）
│   ├── diary/             # 日记引擎
│   ├── proactive/         # 主动行为引擎 2.0
│   ├── life_loop.py       # 持续生命循环（已接入全部新引擎）
│   ├── config.py          # 统一配置
│   ├── ...                # 2.0 原有：simulator/energy/schedule/events 等
├── web_runtime.py         # 网页运行时（SQLite 持久化 + 引擎恢复）
├── web_server.py          # HTTP 服务器
├── tests/                 # 测试（189+ 通过）
└── requirements.txt
```

## 测试

```bash
pip install -r requirements.txt
python -m pytest
```

## 阶段路线

- **阶段1（已完成）**：升级 xiaoqi-agent 为生命核心 —— Memory 2.0 / Emotion / Neurochemical / Diary / Proactive
- **阶段2**：接入 Open-LLM-VTuber（实时语音/VAD/Whisper/打断/TTS/视觉）—— 实现其 `AgentInterface`
- **阶段3**：接入 Soul-of-Waifu（VRM 身体/表情/动作/桌宠）—— 通过 `Actions.expressions` 表情通道
