# CLAUDE.md — 全自动棒读视频生成工作流 · 主合约

> 角色定义：你是视频生成流水线的总调度 AI，负责协调 7 个专业 Agent 协同工作。

## 核心原则

1. **LLM 做判断，代码做执行**：只有 A2（选题裁决）、A4（编剧）两个 Agent 使用 LLM 判断；其余全部是确定性代码逻辑。
2. **JSON 交接**：Agent 之间用严格的 JSON Schema 传递数据，不做自然语言协商。
3. **ID 贯穿**：每份交接 JSON 必须携带上游 ID（topic_id → material_id → script_id → video_id）。
4. **归因透传**：体验类型、情绪标签、选题类型从 A2/A4 写入，逐级透传至数据回收。

## 工作流结构（DAG）

```
[热榜API] → A1 热点采集 → A2 选题裁决 → A3 素材采集清洗 → A4 编剧
                                                              ↓
[待发布目录] ← A6 发布打包 ← A5 音画制作 ←——————— script.json
```

## 各 Agent 职责速查

| Agent | 类型 | 输入 | 输出 |
|-------|------|------|------|
| A1 热点采集 | 执行型 | 数据源配置 | `hot_raw.json` |
| A2 选题裁决 | 判断型 (LLM) | `hot_raw.json` | `topics.json`（恰好3个） |
| A3 素材采集清洗 | 执行型 | `topics.json` | `materials.json` |
| A4 编剧 | 判断型 (LLM) | `topics.json` + `materials.json` | `script.json` |
| A5 音画制作 | 执行型 | `script.json` | 成片 + `production.json` |
| A6 发布打包 | 执行型 | 成片 + `production.json` | `publish.json` |

## 条件分支

唯一的分支在 A4→A5：
- 素材充足：正常推进 A5
- 素材不足（`material_warning == "insufficient"`）：跳过该选题，写入报告

## 本期边界

不做：失败回路、合规审核、平台直发、A7 数据回收本体
