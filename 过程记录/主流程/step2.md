# Step 2 — Agent 实现 + Skill 文件填充完成记录

> 日期：2026-07-18  
> 状态：✅ 完成  
> 前置：Step 1（[step1.md](./step1.md)）  
> 本次范围：Step 5（6 个 Agent 核心逻辑实现）+ Step 6（19 个 Skill 文件填充）

---

## 一、本次完成的文件

### 1.1 新创建：Skill 文件（13 个，总计 19 个 Skill）

| Skill 路径 | 内容完整度 | 说明 |
|-----------|-----------|------|
| `a1-hotspot/datasources.md` | 模板 | 数据源配置表框架，待填实际 API 地址 |
| `a2-topic-select/rubric.md` | 完整 | 四维打分标准（1-5分）+ 加权公式 + 淘汰线 |
| `a2-topic-select/whitelist.md` | 完整 | 8 个泛娱乐领域 + 白名单过滤规则 |
| `a2-topic-select/sensitive_words.md` | 模板 | 敏感词分类框架，待填具体词库 |
| `a2-topic-select/combo_examples.md` | 完整 | 关联假设合格/不合格示例（6 组） |
| `a3-material-query/cleaning.md` | 完整 | 字数过滤+embedding去重+密度打分+Top8 规则 |
| `a3-material-query/query_rules.md` | 完整 | 单一选题/组合选题 query 生成规则 |
| `a4-scriptwriting/emotion_table.md` | 完整 | 8 种情绪：英文映射 + BPM + TTS 语气 + 约束规则 |
| `a4-scriptwriting/experience_map.md` | 完整 | 六体验：特征+叙事结构+情绪链+完播杠杆 |
| `a4-scriptwriting/storyboard_schema.md` | 完整 | 8 个分镜字段规范 + 硬性约束 |
| `a4-scriptwriting/hook_guide.md` | 完整 | 5 种钩子类型（信息差/冲突/共鸣/问题/反差） |
| `a5-production/voice_table.md` | 模板 | 情绪→音色映射表，待替换为实际 TTS 音色 ID |
| `a5-production/bgm_mapping.md` | 完整 | 情绪→曲库标签→BPM→闪避压缩 |
| `a5-production/style_suffix.md` | 完整 | 6 种画面风格后缀 + 默认风格 |
| `a5-production/render_params.md` | 完整 | ffmpeg 参数模板 + 分辨率选项 + 字幕参数 |
| `a6-publish/platforms.md` | 完整 | 抖音/B站/快手三平台发布字段规范 |

### 1.2 重写/更新：Agent 代码（6 个）

| 文件 | Agent | 类型 | 行数 | 核心实现 |
|------|-------|------|------|----------|
| `a1_collector.py` | A1 热点采集 | 执行型 | ~120 | 解析 skill 配置表 → HTTP 调用 → 统一格式化；`dry_run` 降级到 `mock_data()` |
| `a2_selector.py` | A2 选题裁决 | 判断型 | ~190 | 代码过滤（白名单+敏感词）→ LLM 四维打分+关联假设 → Top 3；候选不足自动降级 |
| `a3_material.py` | A3 素材采集清洗 | 执行型 | ~230 | 两种 query 生成策略 → RSS/API 抓取 → 字数过滤 → MD5 去重 → `info_density` 排序 → Top 8 |
| `a4_scriptwriter.py` | A4 编剧 | 判断型 | ~300 | 加载 4 个 skill → 构建 system prompt → LLM 生成 → `_validate_and_fix()` 校验修复 → 降级分镜 → 自动生成人读报告 |
| `a5_producer.py` | A5 音画制作 | 执行型 | ~145 | 逐分镜 TTS + BGM（首镜选，全片用） + 背景图（逐帧生） → ffmpeg 合成 |
| `a6_publisher.py` | A6 发布打包 | 执行型 | ~100 | 复制成片 → 生成标题/简介/标签 → 写 `publish.json` → `review_status=pending_human` |

### 1.3 更新的基础设施（4 个）

| 文件 | 变更内容 |
|------|---------|
| `src/llm/provider.py` | `OpenAICompatibleProvider`（httpx 直连，支持任意兼容 API）+ `MockProvider` |
| `src/agents/base.py` | `_load_skill()` 方法从文件系统读取 `.claude/skills/` 下的 `.md` |
| `src/graph.py` | `build_graph(llm)` 支持传入 LLM Provider；默认 MockProvider；A2/A4 初始化为 `JudgementAgent(llm)` |
| `src/main.py` | LLM 优先级链：外部传入 → 环境变量(`OPENAI_API_KEY`) → Mock；执行摘要报告 |
| `run.py` | 新增 `--api-key` / `--base-url` / `--model` CLI 参数 |

---

## 二、关键设计决策

### 2.1 LLM 抽象链

```
用户传入 ──→ 环境变量 ──→ MockProvider
(CLI args)   (OPENAI_API_KEY)  (干跑/测试)
```

- `OpenAICompatibleProvider` 基于 httpx 直连，不依赖 openai SDK
- 通过 `base_url` 参数可对接任何 OpenAI 兼容网关（如 Azure、Ollama、本地 vLLM）
- `MockProvider` 确保无 API Key 时不崩溃，返回 mock 结果继续流程

### 2.2 Agent 协作模式

- **A1**：纯代码。解析 `.md` 中的表格提取数据源 URL，支持 JSON API 和 RSS 两种格式
- **A2**：代码前置过滤 + LLM 核心裁决。领域白名单和敏感词走确定性代码，避免 LLM 遗漏
- **A3**：纯代码。query 生成依赖 A2 的关键词和关联假设，但由代码规则扩展
- **A4**：纯 LLM 创作 + 代码后置校验。LLM 出脚本 → `_validate_and_fix()` 修复非法情绪、超标种类、字段缺失
- **A5**：纯代码工具编排。每个分镜串行调 TTS → BGM(仅一次) → 生图 → 最后 ffmpeg 合成
- **A6**：纯代码打包。从 script 中自动提取标题/简介/标签

### 2.3 校验与降级策略

| 场景 | 处理方式 |
|------|---------|
| LLM 未配置 | `MockProvider` 返回固定 mock 数据，流程不中断 |
| A2 候选不足 3 个 | 跳过 LLM 打分，直接以默认分输出 |
| A2 LLM 调用失败 | 降级到 `_minimal_topics()` |
| A4 素材 < 3 条 | 跳过该选题，写入 `state.errors`，DAG 走 `skip` 分支 |
| A4 LLM 返回无分镜 | `_fallback_storyboard()` 按句号拆分口播稿 |
| A4 情绪标签超标 | 自动裁剪到 3 种 |
| A4 体验推翻 A2 hint 但无理由 | 自动补写 reason |
| TTS/BGM/生图/ffmpeg 不可用 | 各工具内部捕获异常，输出占位文件 |

### 2.4 数据流

```
A1 hot_raw ──→ A2 (领域+敏感过滤) ──→ A2 LLM 打分 ──→ topics.json (3个)
                                                              │
A3 ←── topics.json ──→ query生成 ──→ 抓取 ──→ 清洗 ──→ materials.json (每选题≤8条)
                                                              │
A4 ←── materials.json ──→ LLM 编剧 ──→ script.json + 脚本报告.md
                                                              │
A5 ←── script.json ──→ TTS+BGM+生图 ──→ ffmpeg ──→ mp4 + production.json
                                                              │
A6 ←── mp4 + production.json ──→ publish.json (pending_human)
```

---

## 三、Skill 文件完整度评估

| 类别 | 完整 | 模板 | 说明 |
|------|------|------|------|
| A1 数据源 | 0 | 1 | 模板空白，需填入实际热榜 API |
| A2 裁决规则 | 3 | 1 | rubric/whitelist/examples 完整，敏感词库待填 |
| A3 清洗规则 | 2 | 0 | 清洗规则完整，RSS 源 URL 待配置 |
| A4 编剧知识 | 4 | 0 | 全部完整 |
| A5 制作参数 | 3 | 1 | 音色 ID 待替换实际服务 |
| A6 发布配置 | 0 | 1 | 平台字段完整，无需再填 |
| **合计** | **12** | **4** | 3 个模板待后续补充 |

---

## 四、待后续补充项

### 高优先级（影响核心链路）

- [ ] **LLM API Key 配置**：设置 `OPENAI_API_KEY` 环境变量或传入 `--api-key`
- [ ] **A1 数据源 API**：在 `datasources.md` 中填入实际热榜接口
- [ ] **A3 RSS 源**：在 `a3_material.py` 的 `_search_rss()` 中配置 RSS URLs
- [ ] **A5 音色 ID**：在 `voice_table.md` 中将占位 ID 替换为实际 TTS 服务音色
- [ ] **TTS 服务安装**：`pip install edge-tts` 或对接云端 TTS

### 中优先级（增强）

- [ ] **A2 敏感词库**：在 `sensitive_words.md` 中填入具体敏感词列表
- [ ] **embedding 模型**：A3 当前用 MD5 去重，升级为 embedding 去重需安装 `sentence-transformers`
- [ ] **生图服务**：对接实际生图 API（Stable Diffusion / DALL-E）
- [ ] **免版权曲库**：对接实际曲库 API
- [ ] **日志系统**：从 `print` 升级为结构化 logging

### 低优先级（优化）

- [ ] **并发优化**：A3 的 RSS 抓取可改为并发请求
- [ ] **配置中心化**：将硬编码常量（阈值、权重）移入 `config` dict
- [ ] **单元测试**：为各 agent 编写测试用例
- [ ] **覆盖率**：校验覆盖率 > 80%

---

## 五、启动命令速查

```bash
# 干跑模式（全 Mock，不调外部服务）
python run.py --dry-run

# 干跑，只执行 A1→A3
python run.py --dry-run --to A3

# 真实 LLM（通过 CLI 传入）
python run.py --api-key sk-xxx --base-url https://api.openai.com/v1 --model gpt-4o

# 真实 LLM（通过环境变量）
set OPENAI_API_KEY=sk-xxx
python run.py

# 从 A2 断点执行到 A5
python run.py --from A2 --to A5 --api-key sk-xxx
```
