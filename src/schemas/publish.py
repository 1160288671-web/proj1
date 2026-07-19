"""A6 输出：publish.json"""
from typing import Literal
from pydantic import BaseModel, Field

from .meta import Meta


class PublishOutput(BaseModel):
    """A6 输出：publish.json"""
    meta: Meta
    video_id: str = Field(..., description="视频唯一 ID")
    topic_id: str = Field(..., description="关联的选题 ID")
    platform: str = Field(default="douyin", description="目标平台", examples=["douyin", "bilibili", "kuaishou"])
    title: str = Field(..., description="最终标题")
    description: str = Field(default="", description="简介")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    cover_image: str = Field(default="cover.png", description="封面图文件名")
    review_status: Literal["pending_human", "approved", "rejected"] = Field(
        default="pending_human", description="人工审核状态"
    )
