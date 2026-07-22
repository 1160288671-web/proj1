# A1 数据源配置

> 本文件是**人读文档 + 跨 Agent 交接说明**；A1 采集器实际读取的机器配置是同目录下的
> **`datasources.json`**。修改数据源请改 JSON，并同步更新本文件的说明。

## 当前数据源状态（2026-07-22 更新）

### 热度榜（list_type = "hot"）— 当前最热内容

| 平台 | 数据源 | 状态 | 条数 | 热度字段 | 热度量级 | 领域标签 |
|------|--------|------|------|----------|----------|----------|
| 微博 | 微博热搜 `weibo.com/ajax/side/hotSearch` | ✅ 启用 | ~52 | `num` | 百万级 | `flag_desc`（部分有） |
| 百度 | 百度热搜 `top.baidu.com/api/board?tab=realtime` | ✅ 启用 | ~50 | `hotScore` | 千万级 | 无 |
| 头条 | 头条热榜 `toutiao.com/hot-event/hot-board` | ✅ 启用 | ~50 | `HotValue` | 千万级 | 无 |
| B站 | B站热搜 `api.bilibili.com/.../search/square` | ✅ 启用 | ~10 | `heat_score` | 百万级 | 无 |
| B站 | B站热门视频 `api.bilibili.com/.../popular` | ✅ 启用 | 20 | `stat.view`（播放量） | 百万级 | `tname`（分区） |

### 增量榜（list_type = "rising"）— 上升最快的条目

| 平台 | 数据源 | 状态 | 条数 | 热度字段 | 热度量级 | 领域标签 |
|------|--------|------|------|----------|----------|----------|
| B站 | B站搜索趋势 `app.bilibili.com/.../search/trending/ranking` | ✅ 启用 | ~30 | 无（仅排名） | — | 无 |
| 百度 | 百度上升热搜 `tab=rising` | ⚠️ 待验证 | 未知 | `hotChange`（变化量） | 十万级 | 无 |

> **注**：微信/头条无独立免费上升榜 API。微博热度榜本身含 `label_name`（"新"/"热"/"爆"）趋势标记，
> 通过条目的 `trend` 字段透出。

备用通道（默认关闭，官方接口失效时启用）：60s 聚合的 微博 / 头条 / 百度 中转，字段已归一。

## 榜单类型说明

| list_type | 含义 | 排序逻辑 | 用途 |
|-----------|------|----------|------|
| `"hot"` | 实时热度榜 | 按热度绝对值降序 | 获取当前最受关注的话题 |
| `"rising"` | 实时增量榜 | 按热度增长率/排名 | 发现正在快速升温的潜在热点 |

A1 将两类榜单的条目全部汇入 `hot_raw`，通过每条记录的 `list_type` 字段区分。

## 趋势字段（trend）

部分数据源提供趋势标记，采集器提取后存入 `trend` 字段：

| 数据源 | trend 字段来源 | 典型值 |
|--------|---------------|--------|
| 微博热搜 | `label_name` | `"新"` / `"热"` / `"爆"` / `""` |
| 百度热搜 | `hotChange` | 热度变化数值（如 `"2180"`） |
| 百度上升 | `hotChange` | 变化量，同时用作 heat_score 代理 |
| 其他 | — | `""` |

## 关键说明

### 小红书为什么缺席

无公开热榜接口；已验证第三方免费聚合（韩小韩、DailyHot 公共实例）当前不可用。待定。

### 热度口径（归一化待做）

各源热度字段**语义不同且未归一化**：微博/百度/头条/B站热搜是各自官方加权指数，B站热门是播放量。
A1 只负责原样采集并把口径说明记录在 JSON 的 `heat_meta` 里；归一化逻辑归 A2 热度打分环节。

### 字段映射与 list_path

- `list_path`：点分路径，数字段为数组下标。百度为 `data.cards.0.content`（须用 `platform=pc` 才有热度值）。
- `field_map.heat_score` 支持嵌套（如 `stat.view`）；百度 `hotScore` 是字符串数字，采集器已转 int。
- `url` 优先取字段；无 URL 字段的源用 `url_template` 拼装。
- 无 `rank` 字段的源按数组顺序补 rank。

### 输出契约（A1 自行落盘）

文件：`data/hot_raw.json`。

```json
{
  "meta": { "workflow_id": "...", "stage": "A1_collect", "schema_version": "0.3",
            "created_at": "...", "status": "ok" },
  "summary": { "total": 160, "hot": 120, "rising": 40 },
  "source_stats": {
    "weibo_hot": { "name": "微博热搜", "list_type": "hot", "count": 20 },
    "bilibili_trending": { "name": "B站搜索趋势", "list_type": "rising", "count": 30 }
  },
  "items": [
    { "title": "...", "heat_score": 1791285, "rank": 1, "url": "...",
      "domain_tag": "剧集", "source": "微博热搜", "source_id": "weibo_hot",
      "platform": "weibo", "list_type": "hot", "trend": "新",
      "fetch_time": "...", "fingerprint": "81e12206" }
  ]
}
```

规则：A1 只做原样结构化——**不过滤、不归一化、不去重**。原始响应样本存于 `testdemo/api_probe/`。
