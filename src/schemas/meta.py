"""通用信封 Meta —— 所有交接 JSON 的头部"""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class Meta(BaseModel):
    """每个 agent 输出 JSON 必须携带的信封"""
    workflow_id: str = Field(..., description="工作流实例 ID，如 wf-20260718-01")
    stage: str = Field(
        ...,
        description="当前阶段标识",
        examples=["A1_collect", "A2_select", "A3_material", "A4_script", "A5_produce", "A6_publish"],
    )
    schema_version: str = Field(default="0.1", description="接口版本号")
    created_at: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        description="创建时间",
    )
    status: Literal["ok", "error", "skip"] = Field(default="ok", description="本阶段状态")
