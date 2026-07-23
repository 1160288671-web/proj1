# Step 1 — 项目骨架搭建完成记录

> 日期：2026-07-18  
> 状态：✅ 完成  
> 基于：[视频生成工作流设计初稿.md](../../视频生成工作流设计初稿.md)  
> 目录结构参照：[项目结构说明.md](../项目结构说明.md)（LOOPKIT VAULT）

---

## 一、已完成工作

### 1.1 技术选型

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 框架 | LangGraph (Python) | DAG 流水线天然匹配，StateGraph 内置状态管理和条件分支 |
| LLM 层 | 抽象接口，不绑定提供商 | `src/llm/provider.py` 抽象基类，后续按需实现 OpenAI 等 |
| 项目结构 | LOOPKIT VAULT | `.claude/` 规则层 + `src/` 执行层，双轨分离 |
| 实施策略 | 先骨架后填充 | Step 1-4 搭建框架，Step 5-6 逐个实现 Agent 和 Skill |

### 1.2 已创建的文件（48 个）

#### 根目录
```
run.py                  # CLI 入口（支持 --from/--to/--dry-run）
requirements.txt        # Python 依赖（langgraph, pydantic, httpx, numpy, scikit-learn）
MEMORY.md               # 跨会话记忆日志
```

#### .claude/ 规则层（AI 操作系统）
```
.claude/
├── CLAUDE.md                         # 主合约：角色定义 + 工作流速查表
├── settings.json                     # 权限与资源边界
├── .mcp.json                         # MCP 工具注册
├── hooks/
│   ├── pre-tool-use.sh               # 工具调用前拦截
│   ├── post-tool-use.sh              # 工具调用后日志
│   └── stop.sh                       # 终止清理
├── agents/                           # 7 个 Agent 角色卡
│   ├── supervisor.md                 # 总调度
│   ├── a1_collector.md               # A1 热点采集（执行型）
│   ├── a2_selector.md                # A2 选题裁决（判断型，LLM）
│   ├── a3_material.md                # A3 素材采集清洗（执行型）
│   ├── a4_scriptwriter.md            # A4 编剧（判断型，LLM）
│   ├── a5_producer.md                # A5 音画制作（执行型）
│   └── a6_publisher.md               # A6 发布打包（执行型）
└── skills/                           # 6 个子目录，各含占位 .md
    ├── a1-hotspot/datasources.md
    ├── a2-topic-select/rubric.md
    ├── a3-material-query/cleaning.md
    ├── a4-scriptwriting/experience_map.md
    ├── a5-production/params.md
    └── a6-publish/platforms.md
```

#### src/ 执行层

**核心框架（5 文件）：**
```
src/
├── state.py                           # WorkflowState TypedDict（贯穿全图的共享状态）
├── graph.py                           # LangGraph DAG 定义（A1→A6 + A4 条件分支）
├── main.py                            # VideoWorkflow 协调器
├── agents/base.py                     # ExecutionAgent / JudgementAgent 基类
└── llm/provider.py                    # LLMProvider 抽象接口 + OpenAIProvider 桩
```

**Schema 层（7 个 Pydantic Model）：**
```
src/schemas/
├── meta.py                            # 通用信封 Meta
├── topics.py                          # A2 输出：选题裁决结果（含四维打分）
├── materials.py                       # A3 输出：素材 + 信息密度 + 去重
├── script.py                          # A4 输出：脚本 + 分镜（含情绪词表校验方法）
├── production.py                      # A5 输出：制作溯源（TTS+BGM+素材+渲染参数）
├── publish.py                         # A6 输出：发布打包（含人工审核状态）
└── performance.py                     # A7 预留：数据回收指标
```

**工具层（6 文件，其中 2 个已实现核心逻辑）：**
```
src/tools/
├── info_density.py                    # ✅ 已实现：正则评分引擎（满分 9）
│                                       #   数字/金额 +2, 人名/机构 +2, 时间线 +2, 引语 +1, 因果 +2
├── dedup.py                           # ✅ 已实现：余弦相似度判重 + 簇内排序
├── bgm.py                             # 桩：情绪→BPM 范围映射表 + 英文标签映射
├── tts.py                             # 桩：TTS 合成（edge-tts 降级）
├── render.py                          # 桩：ffmpeg 合成管线
└── image_gen.py                       # 桩：AI 生图 + 全局风格后缀
```

**Agent 代码（6 个桩，每个 run() 内标注 TODO 步骤）：**
```
src/agents/
├── a1_collector.py                    # 执行型：含 dry_run 跳过 + 数据源 TODO
├── a2_selector.py                     # 判断型：5 步过滤/打分流 TODO
├── a3_material.py                     # 执行型：query 生成→抓取→清洗→去重→排序（5 步 TODO）
├── a4_scriptwriter.py                 # 判断型：素材不足检测 + 5 步编剧 TODO
├── a5_producer.py                     # 执行型：TTS→BGM→背景图→字幕→合成（5 步 TODO）
└── a6_publisher.py                    # 执行型：打包目录创建 + TODO
```

**工具层（3 文件）：**
```
src/utils/
├── id_gen.py                          # topic_id / material_id / script_id / video_id / workflow_id 生成
└── __init__.py
```

### 1.3 Agent 类型分布

| Agent | 类型 | LLM 调用 | 当前状态 |
|-------|------|----------|----------|
| A1 热点采集 | ExecutionAgent | 无 | 桩，待实现 |
| A2 选题裁决 | JudgementAgent | 有（结构化输出） | 桩，待实现 |
| A3 素材采集清洗 | ExecutionAgent | 仅 query 生成 | 桩，待实现 |
| A4 编剧 | JudgementAgent | 有（结构化输出） | 桩，已含素材不足检测 |
| A5 音画制作 | ExecutionAgent | 无 | 桩，待实现 |
| A6 发布打包 | ExecutionAgent | 无 | 桩，待实现 |

### 1.4 LangGraph DAG 结构

```
START
  │
  ▼
A1_collect ──→ A2_select ──→ A3_material ──→ A4_script
                                                │
                                      ┌─ continue ─┼─ skip ─┐
                                      ▼                     ▼
                                  A5_produce               END
                                      │
                                      ▼
                                  A6_publish
                                      │
                                      ▼
                                     END
```

唯一条件分支：A4 检测到素材不足或脚本为空时，走 `skip` 直接结束。

---

## 二、待完成任务

### 2.1 待填充：Skill 文件（Step 6）

| Skill 文件 | 应包含内容 | 来源（设计稿章节） |
|------------|-----------|-------------------|
| `a1-hotspot/datasources.md` | 数据源 API 地址、调用方式、响应字段映射 | 第 2 节 A1 |
| `a2-topic-select/rubric.md` | 娱乐领域白名单、敏感词表、四维打分 rubric | 第 2 节 A2 / 第 7 节 |
| `a2-topic-select/*.md` | 组合假设写法示例 | 第 7 节 |
| `a3-material-query/cleaning.md` | 字数阈值、去重阈值、密度打分公式 | 第 6 节 |
| `a4-scriptwriting/experience_map.md` | 六体验完整映射表 | 第 5 节 |
| `a4-scriptwriting/emotion_table.md` | 受控情绪词表（含 BPM 参考、TTS 语气建议） | 第 4 节 |
| `a4-scriptwriting/storyboard_schema.md` | 分镜字段规范、钩子写法要求 | 第 2 节 A4 |
| `a5-production/params.md` | 音色映射表、曲库标签映射表、风格后缀、渲染参数模板 | 第 2 节 A5 |
| `a6-publish/platforms.md` | 各平台发布字段规范 | 第 2 节 A6 |

### 2.2 待实现：Agent 核心逻辑（Step 5）

**A1 热点采集：**
- [ ] 读取 `datasources.md` 配置
- [ ] 调用各平台热榜 API
- [ ] 原样格式化输出 `hot_raw` list

**A2 选题裁决：**
- [ ] 加载领域白名单 → 过滤非娱乐条目
- [ ] 敏感词过滤
- [ ] 单一/组合候选生成（组合须 LLM 写关联假设）
- [ ] LLM 四维打分（需设计 prompt + structured output）
- [ ] Top 3 放行
- [ ] 权重可配置（从 skill 文件读取）

**A3 素材采集清洗：**
- [ ] 根据选题类型生成搜索 query
- [ ] 组合选题：将关联假设转写为搜索词
- [ ] 素材抓取（RSS / 开放新闻源）
- [ ] 字数过滤（< 500 丢弃）
- [ ] embedding 去重（调用 `dedup.py`）
- [ ] 信息密度排序（调用 `info_density.py`）
- [ ] 输出 Top 8，不足则标记 warning
- [ ] 关联假设验证回填（`verified: false` 标记）

**A4 编剧：**
- [ ] 加载 skill（情绪词表 + 六体验映射 + 分镜 schema）
- [ ] LLM 读素材 → 定体验定位（主攻+辅攻）
- [ ] 推翻 A2 hint 时必须写 reason
- [ ] 按 4.5 字/秒换算总字数
- [ ] LLM 写口播稿（60-90 秒）
- [ ] LLM 拆分镜（填满所有字段）
- [ ] 校验情绪标签合规（`script.validate_emotions()`）
- [ ] 校验时长约束（Σ duration_sec ≈ duration_target_sec）
- [ ] 输出 `script.json` + `脚本报告.md`
- [ ] 素材不足时跳过该选题

**A5 音画制作：**
- [ ] 读取受控音色表 → TTS 配音（调 `tts.py`）
- [ ] BGM 选配（调 `bgm.py`），按分镜 emotion + bpm_hint
- [ ] 背景图生成（调 `image_gen.py`），统一追加风格后缀
- [ ] 字幕生成（基于 TTS 时间轴）
- [ ] ffmpeg 合成渲染（调 `render.py`）
- [ ] 输出 `production.json`

**A6 发布打包：**
- [ ] 复制成片到待发布目录
- [ ] 生成封面图
- [ ] 组装标题/简介/标签（从 script 取）
- [ ] 写入 `publish.json`，`review_status = pending_human`

### 2.3 待实现：基础设施

- [ ] **LLM Provider 实现**：至少完成一个提供商（OpenAI 兼容）的 `chat()` 和 `structured_output()`
- [ ] **embedding 模型接入**：dedup 需要 embedding 向量（可先用 sentence-transformers 占位）
- [ ] **数据目录初始化**：`data/` 目录的 `hot_raw.json`、`topics.json`、`materials.json` 等初始文件
- [ ] **输出目录**：`output/` 视频输出目录
- [ ] **logging**：从 `print` 升级为结构化日志
- [ ] **错误处理**：当前 `errors: Annotated[list, add]` 已定义，但 agent 桩未实际写入错误

### 2.4 待实现：数据层

- [ ] A1 数据源对接（至少 1 个热榜 API 跑通）
- [ ] A3 素材源对接（至少 1 个 RSS / 新闻源）
- [ ] TTS 服务对接（edge-tts 本地可用 / 云端服务）
- [ ] 免版权曲库对接（Pixabay Music / YouTube Audio Library 等）
- [ ] 生图服务对接

### 2.5 本期明确不做（v2 规划）

| 项目 | 说明 |
|------|------|
| 失败回路与重试状态机 | 开环版无重试，失败即记录 error |
| 合规/版权/事实审核 Agent | 人工审核替代 |
| 平台自动上传 | A6 仅打包，人工确认后发布 |
| A7 数据回收 Agent 本体 | Schema 已定义（`performance.py`），逻辑待 v2 |
| `history.jsonl` 自动排除逻辑 | 本期只追加记录 |

---

## 三、建议下一步实施顺序

1. **打通 LLM Provider**（至少一个实现）— 这是 A2 和 A4 的前置依赖
2. **实现 A4 编剧** — 核心判断型 Agent，决定了输出质量的天花板
3. **实现 A5 音画制作** — 工程难点，TTS + BGM + 生图 + ffmpeg 全链路
4. **实现 A6 发布打包** — 简单，快速收尾后半段
5. **实现 A3 素材采集清洗** — 验证素材质量对脚本的影响
6. **实现 A1 + A2** — 打通全自动链路
7. **填充所有 Skill 文件** — 为 LLM prompt 提供领域知识
