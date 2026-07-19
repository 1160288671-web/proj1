"""A7 预留：performance.json —— 本期不实现"""
from typing import Optional
from pydantic import BaseModel, Field


class Metrics(BaseModel):
    """核心指标"""
    completion_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="完播率")
    retention_5s: float = Field(default=0.0, ge=0.0, le=1.0, description="5 秒留存率")
    like_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="点赞率")
    comment_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="评论率")
    share_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="分享率")


class PerformanceOutput(BaseModel):
    """A7 输出：performance.json（预留）"""
    video_id: str = Field(..., description="视频唯一 ID")
    topic_id: str = Field(..., description="选题 ID")
    experience_primary: str = Field(default="", description="主攻体验（用于归因）")
    metrics: Metrics = Field(default_factory=Metrics)
    attribution_note: Optional[str] = Field(None, description="归因备注")
