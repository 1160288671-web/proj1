"""A3 输出：materials.json"""
from typing import Literal, Optional
from pydantic import BaseModel, Field

from .meta import Meta


class InfoDensity(BaseModel):
    """信息密度打分"""
    score: int = Field(..., ge=0, le=9, description="密度总分 0-9")
    has_numbers: bool = Field(default=False, description="含具体数据/金额/百分比")
    has_names: bool = Field(default=False, description="含实名人物/机构")
    has_timeline: bool = Field(default=False, description="含明确时间线/事件脉络")
    has_quote: bool = Field(default=False, description="含直接引语")
    has_causality: bool = Field(default=False, description="含因果解释")


class Dedup(BaseModel):
    """去重信息"""
    is_duplicate: bool = Field(default=False)
    similar_to: Optional[str] = None
    similarity: float = Field(default=0.0, ge=0.0, le=1.0)


class Material(BaseModel):
    """单条素材"""
    material_id: str = Field(..., description="素材唯一 ID", examples=["mt-001"])
    source: str = Field(..., description="来源", examples=["rss_36kr"])
    url: str = Field(..., description="原始 URL")
    title: str = Field(..., description="标题")
    text: str = Field(..., description="正文全文")
    char_count: int = Field(..., description="正文字数")
    publish_time: str = Field(..., description="发布时间")
    info_density: InfoDensity
    dedup: Dedup


class MaterialHypothesis(BaseModel):
    """关联假设验证结果"""
    hypothesis: str = Field(..., description="假设原文")
    verified: bool = Field(default=True, description="是否搜到素材")


class MaterialsOutput(BaseModel):
    """A3 输出：materials.json"""
    meta: Meta
    topic_id: str = Field(..., description="关联的选题 ID")
    materials: list[Material] = Field(default_factory=list)
    hypotheses_verification: list[MaterialHypothesis] = Field(default_factory=list)
    material_warning: Optional[Literal["insufficient"]] = Field(
        None, description="素材不足警告，触发后 A4 可跳过该选题"
    )
