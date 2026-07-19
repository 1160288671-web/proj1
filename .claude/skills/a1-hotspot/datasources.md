# A1 数据源配置

> 本文件是**人读文档 + 跨 Agent 交接说明**；A1 采集器实际读取的机器配置是同目录下的
> **`datasources.json`**。修改数据源请改 JSON，并同步更新本文件的说明。

## 当前数据源状态（2026-07-19 实测）

| 平台 | 数据源 | 状态 | 条数 | 热度字段 | 热度量级 | 领域标签 |
|------|--------|------|------|----------|----------|----------|
| 微博 | 微博热搜 `weibo.com/ajax/side/hotSearch` | ✅ 启用 | ~52 | `num` | 百万级 | `flag_desc`（部分有） |
| 百度 | 百度热搜 `top.baidu.com/api/board?platform=pc` | ✅ 启用 | 50 | `hotScore` | 千万级 | 无 |
| 头条 | 头条热榜 `toutiao.com/hot-event/hot-board` | ✅ 启用 | 50 | `HotValue` | 千万级 | 无 |
| B站 | B站热搜 `api.bilibili.com/.../search/square` | ✅ 启用 | ~10 | `heat_score` | 百万级 | 无 |
| B站 | B站热门视频 `api.bilibili.com/.../popular` | ✅ 启用 | 20 | `stat.view`（播放量） | 百万级 | `tname`（分区，可靠） |
| 小红书 | 无公开接口 | ❌ 未接入 | — | — | — | — |

备用通道（默认关闭，官方接口失效时启用）：60s 聚合的 微博 / 头条 / 百度 中转，字段已归一。

## 关键说明

### 小红书为什么缺席

无公开热榜接口；已验证第三方免费聚合（韩小韩、DailyHot 公共实例）当前不可用。
三条候选路径：① 自建开源聚合服务（如 DailyHot）；② 付费聚合 API（需 API key）；③ v1 放弃该平台。待定。

### 热度口径（归一化待做）

各源热度字段**语义不同且未归一化**：微博/百度/头条/B站热搜是各自官方加权指数，B站热门是播放量。
A1 只负责原样采集并把口径说明记录在 JSON 的 `heat_meta` 里；归一化逻辑归 A2 热度打分环节，
具体方案待积累若干天 `data/hot_raw.json` 样本后分析决定。

### 字段映射与 list_path

- `list_path`：点分路径，数字段为数组下标。百度为 `data.cards.0.content`（注意须用 `platform=pc` 变体才有热度值）。
- `field_map.heat_score` 支持嵌套（如 `stat.view`）；百度 `hotScore` 是字符串数字，采集器已转 int。
- `url` 优先取字段；无 URL 字段的源用 `url_template` 拼装（`{title}` 自动 URL 编码，B站视频用 `{bvid}`）。
- 无 `rank` 字段的源按数组顺序补 rank。

### 输出契约（A1 自行落盘）

文件：`data/hot_raw.json`（路径在 JSON 配置的 `output.path` 可改）。

```json
{
  "meta": { "workflow_id": "...", "stage": "A1_collect", "schema_version": "0.2",
            "created_at": "...", "status": "ok" },
  "source_stats": { "weibo_hot": 20, "...": "..." },
  "items": [
    { "title": "...", "heat_score": 1791285, "rank": 1, "url": "...",
      "domain_tag": "剧集", "source": "微博热搜", "source_id": "weibo_hot",
      "platform": "weibo", "fetch_time": "...", "fingerprint": "81e12206" }
  ]
}
```

规则：A1 只做原样结构化——**不过滤、不归一化、不去重**（跨源重复保留，判断归 A2）。
原始响应样本存于 `testdemo/api_probe/`，供口径分析用。
