"""A4 输出：script.json —— 全链路最关键接口"""
from typing import Literal, Optional
from pydantic import BaseModel, Field

from .meta import Meta


EMOTION_LABELS = ["悬疑", "紧张", "激昂", "欢快", "戏谑", "温暖", "治愈", "严肃"]
TRANSITION_TYPES = ["cut", "fade", "slide"]
BPM_HINTS = ["low", "mid", "high"]


class Experience(BaseModel):
    """体验定位"""
    primary: str = Field(..., description="主攻体验")
    secondary: str = Field(..., description="辅攻体验")
    reason: str = Field(..., description="选择理由（若推翻 A2 hint 必须说明）")


class StoryboardScene(BaseModel):
    """单个分镜"""
    seq: int = Field(..., ge=1, description="分镜序号")
    duration_sec: float = Field(..., gt=0, description="时长（秒）")
    voice_text: str = Field(..., description="该镜头配音文本")
    subtitle_text: str = Field(default="", description="字幕文本")
    visual_prompt: str = Field(..., description="背景图提示词（系统统一追加风格后缀）")
    emotion: str = Field(..., description="情绪标签，必须来自受控词表")
    transition: Literal["cut", "fade", "slide"] = Field(default="cut", description="转场类型")
    bpm_hint: Literal["low", "mid", "high"] = Field(default="mid", description="BPM 节奏提示")


class ScriptOutput(BaseModel):
    """A4 输出：script.json"""
    meta: Meta
    script_id: str = Field(..., description="脚本唯一 ID", examples=["sc-001"])
    topic_id: str = Field(..., description="关联的选题 ID")
    experience: Experience
    duration_target_sec: float = Field(default=75.0, ge=60.0, le=90.0, description="目标时长（秒）")
    title_options: list[str] = Field(..., min_length=1, description="候选标题，1-N 个")
    hook: str = Field(..., description="前 3 秒口播钩子")
    full_text: str = Field(..., description="完整口播稿")
    storyboard: list[StoryboardScene] = Field(..., min_length=1, description="分镜列表")

    def validate_emotions(self) -> list[str]:
        """校验情绪标签合规：必须是受控词表内、不超过 3 种"""
        used = set(s.emotion for s in self.storyboard)
        invalid = used - set(EMOTION_LABELS)
        if invalid:
            raise ValueError(f"非法情绪标签: {invalid}，允许值: {EMOTION_LABELS}")
        if len(used) > 3:
            raise ValueError(f"情绪标签超过 3 种: {used}")
        return list(used)
