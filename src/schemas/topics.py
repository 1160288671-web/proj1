"""A2 输出：topics.json"""
from typing import Literal
from pydantic import BaseModel, Field

from .meta import Meta


class Score(BaseModel):
    """四维打分明细"""
    heat: int = Field(..., ge=1, le=5, description="热度 1-5")
    safety: int = Field(..., ge=1, le=5, description="安全性 1-5")
    feasibility: int = Field(..., ge=1, le=5, description="可制作性 1-5")
    material_richness: int = Field(..., ge=1, le=5, description="素材丰富度预判 1-5")
    total: float = Field(..., description="加权总分")


class Topic(BaseModel):
    """单个选题"""
    topic_id: str = Field(..., description="选题唯一 ID", examples=["tp-001"])
    type: Literal["single", "combo"] = Field(..., description="选题类型")
    domains: list[str] = Field(..., description="关联领域")
    title_candidate: str = Field(..., description="候选标题")
    keywords: list[str] = Field(..., description="关键词")
    combo_hypotheses: list[str] = Field(
        default_factory=list, description="组合假设（仅 combo 必填，写不出即淘汰）"
    )
    experience_hint: str = Field(..., description="建议体验定位")
    scores: Score
    status: Literal["approved", "rejected"] = Field(default="approved")


class TopicsOutput(BaseModel):
    """A2 输出：topics.json"""
    meta: Meta
    topics: list[Topic] = Field(default_factory=list, max_length=3, description="0-3 个选题")
