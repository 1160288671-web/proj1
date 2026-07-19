"""信息密度打分工具 —— 纯代码执行，不走 LLM

满分 9 分，分项加分明细：
- 含具体数据/金额/百分比：+2
- 含实名人物/机构：+2
- 含明确时间线/事件脉络：+2
- 含直接引语：+1
- 含因果解释（非纯情绪宣泄）：+2
"""
import re
from dataclasses import dataclass, field


@dataclass
class DensityScore:
    score: int = 0
    has_numbers: bool = False
    has_names: bool = False
    has_timeline: bool = False
    has_quote: bool = False
    has_causality: bool = False


# 数字/金额/百分比 正则
RE_NUMBERS = re.compile(
    r"\d+[\d,]*\.?\d*\s*(?:亿|万|千|百|元|美元|港币|日元|欧元|英镑|%|％|个百分点)",
)
RE_PERCENT = re.compile(r"\d+\.?\d*\s*[%％]")

# 实名人物/机构 简单启发式（后续可接入 NER）
RE_NAMED_ENTITY = re.compile(
    r"(?:[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)"  # 英文名
    r"|(?:[\u4e00-\u9fff]{2,4}(?:·[\u4e00-\u9fff]{1,4})?)"  # 中文名
)

# 时间线关键词
TIMELINE_KEYWORDS = [
    "年", "月", "日", "时", "分",
    "此前", "随后", "之后", "此前一天", "当晚", "次日",
    "第一", "第二", "最后", "最终", "首先", "其次",
    "开始于", "结束于", "历时", "持续",
]

# 因果关键词
CAUSALITY_KEYWORDS = [
    "因为", "所以", "因此", "由于", "导致", "造成",
    "原因", "结果", "因素", "源于", "归因", "起因",
    "引发", "使得", "致使", "以至于",
]

# 直接引语标识
QUOTE_MARKERS = ['"', '"', "'", "'", '「', '」', "『", "』", "：", ":"]


def score(text: str) -> DensityScore:
    """对一段文本进行信息密度打分

    Args:
        text: 待评分文本

    Returns:
        DensityScore 对象
    """
    result = DensityScore()

    # 1. 含具体数据/金额/百分比
    if RE_NUMBERS.search(text) or RE_PERCENT.search(text):
        result.has_numbers = True
        result.score += 2

    # 2. 含实名人物/机构
    if RE_NAMED_ENTITY.search(text):
        result.has_names = True
        result.score += 2

    # 3. 含明确时间线/事件脉络
    timeline_hits = sum(1 for kw in TIMELINE_KEYWORDS if kw in text)
    if timeline_hits >= 2:
        result.has_timeline = True
        result.score += 2

    # 4. 含直接引语
    if any(marker in text for marker in QUOTE_MARKERS):
        result.has_quote = True
        result.score += 1

    # 5. 含因果解释
    causality_hits = sum(1 for kw in CAUSALITY_KEYWORDS if kw in text)
    if causality_hits >= 1:
        result.has_causality = True
        result.score += 2

    return result
