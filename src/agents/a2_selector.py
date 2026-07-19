"""A2 选题裁决（判断型）：领域过滤 → 敏感过滤 → 四维打分 → 放行 3 个"""
import json
import re

from src.agents.base import JudgementAgent
from src.utils.id_gen import generate_topic_id


class A2Selector(JudgementAgent):
    """A2：选题裁决"""

    WEIGHTS = {"heat": 0.35, "safety": 0.25, "feasibility": 0.25, "material_richness": 0.15}

    def __init__(self, llm):
        super().__init__(name="A2_Selector", llm=llm)

    async def run(self, state: dict) -> dict:
        self.log("开始选题裁决...")

        hot_raw = state.get("hot_raw", [])
        if not hot_raw:
            self.log("无热点数据，终止")
            state["topics"] = []
            state["stage"] = "A2_select"
            return state

        # Step 1: 加载 skill
        whitelist = self._load_whitelist()
        sensitive_words = self._load_sensitive_words()
        rubric = self._load_skill("a2-topic-select/rubric.md")
        combo_examples = self._load_skill("a2-topic-select/combo_examples.md")

        # Step 2: 领域过滤（代码执行）
        filtered = self._filter_by_domain(hot_raw, whitelist)
        self.log(f"  领域过滤: {len(hot_raw)} → {len(filtered)} 条")

        # Step 3: 敏感过滤（代码执行）
        safe = self._filter_sensitive(filtered, sensitive_words)
        self.log(f"  敏感过滤: {len(filtered)} → {len(safe)} 条")

        if len(safe) < 3:
            self.log(f"  候选不足 3 个（仅 {len(safe)}），全部保留不做打分")
            topics = self._minimal_topics(safe)
            state["topics"] = topics
            state["stage"] = "A2_select"
            return state

        # Step 4: LLM 生成候选 + 打分 + 裁决
        topics = await self._llm_select(safe, rubric, combo_examples)
        state["topics"] = topics
        state["stage"] = "A2_select"
        self.log(f"选题裁决完成，选中 {len(topics)} 个选题")
        return state

    def _load_whitelist(self) -> list[str]:
        """加载领域白名单"""
        content = self._load_skill("a2-topic-select/whitelist.md")
        if not content:
            return ["泛娱乐", "影视综", "音乐演出", "明星八卦", "游戏电竞", "潮流消费", "网络热点", "动漫二次元", "生活方式"]

        domains = []
        for line in content.split("\n"):
            m = re.match(r"\|\s*(.+?)\s*\|", line)
            if m and m.group(1) and "领域" not in m.group(1) and "---" not in m.group(1):
                domains.append(m.group(1).strip())
        return domains if domains else ["泛娱乐"]

    def _load_sensitive_words(self) -> list[str]:
        """加载敏感词"""
        content = self._load_skill("a2-topic-select/sensitive_words.md")
        if not content:
            return []
        # 提取代码块中的词
        words = []
        in_block = False
        for line in content.split("\n"):
            if line.strip().startswith("```"):
                in_block = not in_block
                continue
            if in_block and line.strip() and line.strip() != "待补充":
                words.append(line.strip())
        return words

    def _filter_by_domain(self, entries: list[dict], whitelist: list[str]) -> list[dict]:
        """仅保留泛娱乐领域条目"""
        if not whitelist:
            return entries
        result = []
        for e in entries:
            domain = e.get("domain_tag", "")
            if any(w in domain for w in whitelist):
                result.append(e)
        return result

    def _filter_sensitive(self, entries: list[dict], sensitive_words: list[str]) -> list[dict]:
        """敏感词过滤"""
        if not sensitive_words:
            return entries
        result = []
        for e in entries:
            text = e.get("title", "")
            if not any(w.lower() in text.lower() for w in sensitive_words):
                result.append(e)
        return result

    async def _llm_select(
        self, entries: list[dict], rubric: str, combo_examples: str
    ) -> list[dict]:
        """LLM 生成候选、打分、选出 Top 3"""
        entries_json = json.dumps(
            [
                {"id": e.get("fingerprint", str(i)), "title": e["title"], "domain": e.get("domain_tag", ""), "heat_score": e.get("heat_score", 0)}
                for i, e in enumerate(entries[:30])
            ],
            ensure_ascii=False,
        )

        system_prompt = f"""你是短视频选题裁决专家。你的任务是从候选热点中选出 3 个最适合做棒读视频的选题。

## 评分标准
{rubric}

## 组合选题示例
{combo_examples}

## 输出格式
你只输出一个 JSON object，不要包含任何额外文本：
{{
  "topics": [
    {{
      "type": "single 或 combo",
      "title_candidate": "吸引人的候选标题",
      "domains": ["领域1", "领域2"],
      "keywords": ["关键词1", "关键词2", "关键词3"],
      "combo_hypotheses": ["仅 combo 必填，关联假设1"],
      "experience_hint": "六体验之一",
      "scores": {{ "heat": 4, "safety": 5, "feasibility": 4, "material_richness": 3 }}
    }}
  ]
}}

注意：
- topics 数组恰好 3 个，按 total 分降序
- combo_hypotheses 只对 type=combo 的选题填写，single 为空数组
- experience_hint 从 [掌控感, 爽感, 共鸣感, 优越感, 成长感, 参与感] 中选择
- 每个选题必须先在心中评分再输出"""

        user_prompt = f"候选热点列表（共 {len(entries)} 条）：\n{entries_json}"

        try:
            result = await self.llm.chat_with_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
        except Exception as e:
            self.log(f"LLM 调用失败: {e}")
            return self._minimal_topics(entries)

        topics = result.get("topics", [])
        # 补充 topic_id、status、total
        for t in topics:
            t["topic_id"] = generate_topic_id()
            t["status"] = "approved"
            scores = t.get("scores", {})
            if scores:
                total = sum(
                    scores.get(k, 0) * self.WEIGHTS.get(k, 0.25)
                    for k in self.WEIGHTS
                )
                scores["total"] = round(total, 1)

        return topics[:3]

    def _minimal_topics(self, entries: list[dict]) -> list[dict]:
        """候选不足时直接格式化输出"""
        return [
            {
                "topic_id": generate_topic_id(),
                "type": "single",
                "title_candidate": e["title"],
                "domains": [e.get("domain_tag", "未分类")],
                "keywords": [],
                "combo_hypotheses": [],
                "experience_hint": "共鸣感",
                "scores": {"heat": 3, "safety": 5, "feasibility": 3, "material_richness": 3, "total": 3.4},
                "status": "approved",
            }
            for e in entries[:3]
        ]
