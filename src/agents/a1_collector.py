"""A1 热点采集（执行型）：从预设数据源拉取热榜 + 增量榜

配置来源：.claude/skills/a1-hotspot/datasources.json（机器配置）
输出：data/hot_raw.json（A1 自行落盘，含 meta 信封）+ state["hot_raw"]
原则：原样结构化，不做任何判断（不过滤、不归一化、不去重）

支持两种榜单类型：
  list_type = "hot"    → 实时热度榜（当前最热内容，按热度绝对值排序）
  list_type = "rising" → 实时增量榜（上升最快的条目，按增长率/变化量排序）
两种类型的条目均汇入 hot_raw，通过每个条目的 list_type 字段区分。
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import httpx

from src.agents.base import ExecutionAgent

CONFIG_PATH = Path(".claude/skills/a1-hotspot/datasources.json")


class A1Collector(ExecutionAgent):
    """A1：热点采集"""

    def __init__(self):
        super().__init__(name="A1_Collector")

    async def run(self, state: dict) -> dict:
        self.log("开始采集热点数据...")

        if state.get("dry_run"):
            self.log("[DRY-RUN] 使用模拟数据")
            state["hot_raw"] = self._mock_data()
            state["stage"] = "A1_collect"
            self._write_output(state, source_stats={"mock_source": len(state["hot_raw"])})
            return state

        config = self._load_config()
        defaults = config.get("defaults", {})
        top_n = config.get("output", {}).get("top_n_per_source", 20)
        sources = [s for s in config.get("sources", []) if s.get("enabled")]

        if not sources:
            self.log("WARNING: 无启用的数据源，hot_raw 为空")
            state.setdefault("errors", []).append("A1: 无启用的数据源")

        hot_raw: list[dict] = []
        source_stats: dict[str, dict] = {}
        timeout = defaults.get("timeout_sec", 15)

        async with httpx.AsyncClient(timeout=timeout) as client:
            for src in sources:
                try:
                    list_type = src.get("list_type", "hot")
                    entries = await self._fetch_source(client, src, defaults, list_type)
                    entries = entries[:top_n]
                    hot_raw.extend(entries)
                    source_stats[src["id"]] = {
                        "name": src["name"],
                        "list_type": list_type,
                        "count": len(entries),
                    }
                    self.log(f"  [{list_type}] {src['name']}: 获取 {len(entries)} 条")
                except Exception as e:
                    source_stats[src["id"]] = {
                        "name": src["name"],
                        "list_type": src.get("list_type", "hot"),
                        "count": 0,
                        "error": str(e),
                    }
                    state.setdefault("errors", []).append(f"A1 {src['id']}: {e}")
                    self.log(f"  ERROR {src['name']}: {e}")

        state["hot_raw"] = hot_raw
        state["stage"] = "A1_collect"
        self._write_output(state, source_stats=source_stats)

        hot_count = sum(1 for e in hot_raw if e.get("list_type") == "hot")
        rising_count = sum(1 for e in hot_raw if e.get("list_type") == "rising")
        self.log(f"热点采集完成，共 {len(hot_raw)} 条（热度榜 {hot_count} + 增量榜 {rising_count}）")
        return state

    # ---------- 配置 ----------

    def _load_config(self) -> dict:
        """读取 datasources.json 机器配置"""
        if not CONFIG_PATH.exists():
            self.log(f"WARNING: 配置文件不存在: {CONFIG_PATH}")
            return {}
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    # ---------- 抓取与结构化 ----------

    async def _fetch_source(self, client: httpx.AsyncClient, src: dict,
                            defaults: dict, list_type: str = "hot") -> list[dict]:
        """调用单个数据源，按 field_map 原样结构化"""
        if src.get("type") != "json_api":
            raise ValueError(f"不支持的数据源类型: {src.get('type')}（RSS 通道待 v2）")

        headers = {"User-Agent": defaults.get("user_agent", "VideoBot/1.0")}
        headers.update(src.get("headers") or {})
        resp = await client.get(src["url"], headers=headers,
                                params=src.get("params") or None)
        resp.raise_for_status()
        return self._normalize(resp.json(), src, list_type)

    @staticmethod
    def _dig(data, list_path: str):
        """按点分路径取值，数字段表示数组下标，如 data.cards.0.content"""
        cur = data
        for key in list_path.split("."):
            cur = cur[int(key)] if isinstance(cur, list) else cur[key]
        return cur

    def _normalize(self, data, src: dict, list_type: str = "hot") -> list[dict]:
        """按配置字段映射结构化；不做任何过滤与归一化"""
        items = self._dig(data, src["list_path"])
        if not isinstance(items, list):
            return []

        fmap = src.get("field_map", {})
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")
        entries = []
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            title = str(self._pick(item, fmap.get("title")) or "").strip()
            if not title:
                continue
            entries.append({
                "title": title,
                "heat_score": self._to_int(self._pick(item, fmap.get("heat_score"))),
                "rank": self._to_int(self._pick(item, fmap.get("rank"))) or idx + 1,
                "url": self._resolve_url(item, src, title),
                "domain_tag": str(self._pick(item, fmap.get("domain_tag"))
                                  or src.get("default_domain") or "综合"),
                "source": src["name"],
                "source_id": src["id"],
                "platform": src.get("platform", ""),
                "list_type": list_type,
                "trend": str(self._pick(item, fmap.get("trend")) or ""),
                "fetch_time": now,
                "fingerprint": hashlib.md5(title.encode()).hexdigest()[:8],
            })
        return entries

    def _pick(self, item: dict, field: str | None):
        """按字段映射取值，支持嵌套路径（如 stat.view）；field 为 None 返回 None"""
        if not field:
            return None
        try:
            return self._dig(item, field)
        except (KeyError, IndexError, TypeError):
            return None

    def _resolve_url(self, item: dict, src: dict, title: str) -> str:
        """url 优先取字段映射，其次用 url_template 拼装（{title} 及任意原始字段）"""
        url = self._pick(item, src.get("field_map", {}).get("url"))
        if url:
            return str(url)
        template = src.get("url_template")
        if not template:
            return ""
        try:
            kwargs = dict(item)
            kwargs["title"] = quote(title)  # 覆盖原始 title 字段并做 URL 编码
            return template.format(**kwargs)
        except (KeyError, IndexError):
            return ""

    @staticmethod
    def _to_int(value) -> int:
        """热度/排名转 int；兼容字符串数字（如百度 hotScore）；失败为 0"""
        try:
            return int(float(str(value).replace(",", "")))
        except (TypeError, ValueError):
            return 0

    # ---------- 落盘 ----------

    def _write_output(self, state: dict, source_stats: dict):
        """A1 自行落盘 hot_raw.json（含 meta 信封 + 榜单类型统计）"""
        config = self._load_config()
        out_path = Path(config.get("output", {}).get("path", "data/hot_raw.json"))
        out_path.parent.mkdir(parents=True, exist_ok=True)

        hot_raw = state.get("hot_raw", [])
        hot_count = sum(1 for e in hot_raw if e.get("list_type") == "hot")
        rising_count = sum(1 for e in hot_raw if e.get("list_type") == "rising")

        payload = {
            "meta": {
                "workflow_id": state.get("workflow_id", ""),
                "stage": "A1_collect",
                "schema_version": "0.3",
                "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
                "status": "ok" if hot_raw else "error",
            },
            "summary": {
                "total": len(hot_raw),
                "hot": hot_count,
                "rising": rising_count,
            },
            "source_stats": source_stats,
            "items": hot_raw,
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                            encoding="utf-8")
        self.log(f"已落盘 {out_path}（{len(hot_raw)} 条：热度榜 {hot_count} + 增量榜 {rising_count}）")

    # ---------- 模拟数据 ----------

    def _mock_data(self) -> list[dict]:
        """模拟数据（干跑/测试用）：混合热度榜 + 增量榜"""
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")
        result = []
        for i in range(1, 21):
            result.append({
                "title": f"模拟热榜条目 #{i}",
                "heat_score": 10000 - i * 500,
                "rank": i,
                "url": "",
                "domain_tag": "泛娱乐",
                "source": "mock_source",
                "source_id": "mock",
                "platform": "mock",
                "list_type": "hot",
                "trend": "",
                "fetch_time": now,
                "fingerprint": f"mock_{i:03d}",
            })
        for i in range(1, 11):
            result.append({
                "title": f"模拟增量榜条目 #{i}",
                "heat_score": 5000 - i * 500,
                "rank": i,
                "url": "",
                "domain_tag": "泛娱乐",
                "source": "mock_source",
                "source_id": "mock",
                "platform": "mock",
                "list_type": "rising",
                "trend": "↑",
                "fetch_time": now,
                "fingerprint": f"mock_r_{i:03d}",
            })
        return result
