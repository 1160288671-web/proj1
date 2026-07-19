"""A3 素材采集清洗（执行型）：query 生成 → 抓取 → 清洗 → 去重 → 排序"""
import hashlib
from datetime import datetime

import httpx

from src.agents.base import ExecutionAgent
from src.tools.info_density import score as density_score
from src.tools.dedup import cluster_keep
from src.utils.id_gen import generate_material_id


class A3Material(ExecutionAgent):
    """A3：素材采集清洗"""

    TOP_N = 8
    CHAR_MIN = 500
    DEDUP_THRESHOLD = 0.85

    def __init__(self):
        super().__init__(name="A3_Material")

    async def run(self, state: dict) -> dict:
        self.log("开始素材采集清洗...")

        topics = state.get("topics", [])
        materials: dict[str, list] = {}

        for topic in topics:
            topic_id = topic.get("topic_id", "")
            self.log(f"  处理选题 {topic_id}: {topic.get('title_candidate', '')[:30]}...")

            # Step 1: query 生成
            queries = self._generate_queries(topic)

            # Step 2: 素材抓取
            raw_materials = await self._fetch_materials(queries)

            # Step 3: 字数过滤
            filtered = self._filter_by_length(raw_materials)

            # Step 4: 去重（简化版：基于 fingerprint 而不是 embedding）
            deduped = self._dedup(filtered)

            # Step 5: 信息密度排序 + Top N
            ranked = self._rank_and_truncate(deduped, topic_id)

            # Step 6: 关联假设验证（组合选题）
            if topic.get("type") == "combo":
                ranked = self._verify_hypotheses(ranked, topic)

            # 素材不足标记
            material_warning = "insufficient" if len(ranked) < 3 else None
            topic_materials = {
                "topic_id": topic_id,
                "materials": ranked,
            }
            if material_warning:
                topic_materials["material_warning"] = material_warning

            materials[topic_id] = ranked

        state["materials"] = materials
        state["stage"] = "A3_material"
        summary = {tid: len(ms) for tid, ms in materials.items()}
        self.log(f"素材采集完成: {summary}")
        return state

    def _generate_queries(self, topic: dict) -> list[str]:
        """生成搜索 query"""
        query_rules = self._load_skill("a3-material-query/query_rules.md")

        if topic.get("type") == "combo":
            return self._combo_queries(topic)
        else:
            return self._single_queries(topic)

    def _single_queries(self, topic: dict) -> list[str]:
        """单一选题：关键词扩展"""
        keywords = topic.get("keywords", [])
        title = topic.get("title_candidate", "")
        queries = [title]
        for kw in keywords[:5]:
            if kw and kw not in title and len(kw) >= 2:
                queries.append(f"{kw} 最新")
                queries.append(f"{kw} 2026")
        # 去重
        seen = set()
        unique = []
        for q in queries:
            if q not in seen:
                seen.add(q)
                unique.append(q)
        return unique[:8]

    def _combo_queries(self, topic: dict) -> list[str]:
        """组合选题：从关联假设转写搜索词"""
        hypotheses = topic.get("combo_hypotheses", [])
        domains = topic.get("domains", [])
        queries = []

        for h in hypotheses:
            # 简单分词提取实体词
            words = h.replace("「", "").replace("」", "").replace("、", " ").replace("的", " ")
            for w in ["因为", "产生关联", "关联", "与", "同为", "均是"]:
                words = words.replace(w, " ")
            parts = [p.strip() for p in words.split() if len(p.strip()) >= 2]
            queries.extend(parts[:3])

        # 补充领域组合搜索
        if len(domains) >= 2:
            queries.append(f"{domains[0]} {domains[1]} 2026")

        # 去重
        seen = set()
        unique = []
        for q in queries:
            if q not in seen:
                seen.add(q)
                unique.append(q)
        return unique[:10]

    async def _fetch_materials(self, queries: list[str]) -> list[dict]:
        """素材抓取（使用公开 RSS / News API）"""
        results = []
        for query in queries[:5]:  # 限制搜索数
            try:
                items = await self._search(query)
                results.extend(items)
            except Exception as e:
                self.log(f"    搜索失败 '{query[:30]}': {e}")
        return results

    async def _search(self, query: str) -> list[dict]:
        """单次搜索"""
        # 尝试多种公开源
        sources = [
            self._search_rss,
        ]

        for source_fn in sources:
            results = await source_fn(query)
            if results:
                return results
        return []

    async def _search_rss(self, query: str) -> list[dict]:
        """从公开 RSS 源搜索（示例，需配置实际 RSS 源）"""
        # RSS 源配置在 skill 中
        rss_urls = [
            # TODO: 配置实际 RSS 源
        ]
        results = []
        for url in rss_urls:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(url, headers={"User-Agent": "VideoBot/1.0"})
                    resp.raise_for_status()
                    # RSS 解析（简化）
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(resp.text)
                    for item in root.iter("item"):
                        title = item.findtext("title", "")
                        desc = item.findtext("description", "")
                        link = item.findtext("link", "")
                        pub = item.findtext("pubDate", "")
                        if query.lower() in (title + desc).lower():
                            results.append({
                                "title": title,
                                "text": desc,
                                "url": link,
                                "publish_time": pub or datetime.now().strftime("%Y-%m-%d"),
                                "source": url,
                            })
            except Exception:
                continue
        return results

    def _filter_by_length(self, items: list[dict]) -> list[dict]:
        """字数过滤：< 500 丢弃"""
        return [
            item for item in items
            if len(item.get("text", "")) >= self.CHAR_MIN
        ]

    def _dedup(self, items: list[dict]) -> list[dict]:
        """基于 fingerprint 的简单去重（embedding 去重需额外依赖）"""
        seen = set()
        result = []
        for item in items:
            fp = hashlib.md5(
                (item.get("title", "") + item.get("text", "")[:200]).encode()
            ).hexdigest()
            if fp not in seen:
                seen.add(fp)
                result.append(item)
        return result

    def _rank_and_truncate(self, items: list[dict], topic_id: str) -> list[dict]:
        """信息密度打分 + 排序 + Top N"""
        for item in items:
            ds = density_score(item.get("text", ""))
            item["material_id"] = generate_material_id()
            item["char_count"] = len(item.get("text", ""))
            item["info_density"] = {
                "score": ds.score,
                "has_numbers": ds.has_numbers,
                "has_names": ds.has_names,
                "has_timeline": ds.has_timeline,
                "has_quote": ds.has_quote,
                "has_causality": ds.has_causality,
            }
            item["dedup"] = {"is_duplicate": False, "similar_to": None, "similarity": 0.0}

        # 按信息密度降序，同分按发布更早优先
        items.sort(
            key=lambda m: (
                -m.get("info_density", {}).get("score", 0),
                m.get("publish_time", "9999-12-31"),
            )
        )

        return items[: self.TOP_N]

    def _verify_hypotheses(self, materials: list[dict], topic: dict) -> list[dict]:
        """组合选题：验证关联假设是否搜到素材"""
        # 简化：如果搜到素材数量 >= 3 则认为假设验证通过
        # TODO: 更精细的验证逻辑（关键词匹配等）
        return materials
