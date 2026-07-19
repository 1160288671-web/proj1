"""A5 输出：production.json —— 溯源用"""
from typing import Optional
from pydantic import BaseModel, Field

from .meta import Meta


class TtsParams(BaseModel):
    """TTS 配音参数"""
    voice_id: str = Field(..., description="音色 ID", examples=["v_qinglang_01"])
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="语速")


class BgmParams(BaseModel):
    """BGM 参数"""
    track_id: str = Field(..., description="曲目 ID", examples=["lib_suspense_042"])
    emotion: str = Field(..., description="情绪标签")
    bpm: Optional[int] = Field(None, ge=40, le=200, description="BPM")
    ducking_db: float = Field(default=-12.0, description="闪避音量 dB")


class Asset(BaseModel):
    """单个素材资源"""
    seq: int = Field(..., description="分镜序号")
    image_path: str = Field(..., description="图片路径")
    prompt_used: str = Field(default="", description="使用的生图提示词")


class RenderParams(BaseModel):
    """渲染参数"""
    resolution: str = Field(default="1080x1920", description="分辨率")
    fps: int = Field(default=30, ge=15, le=60)
    format: str = Field(default="mp4")


class ProductionOutput(BaseModel):
    """A5 输出：production.json"""
    meta: Meta
    video_id: str = Field(..., description="视频唯一 ID", examples=["vd-001"])
    script_id: str = Field(..., description="关联的脚本 ID")
    tts: TtsParams
    bgm: BgmParams
    assets: list[Asset] = Field(default_factory=list)
    render: RenderParams = Field(default_factory=RenderParams)
