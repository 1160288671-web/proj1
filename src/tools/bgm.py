"""BGM 选配工具（占位，后续对接免版权曲库）"""

# 情绪标签 → BPM 参考范围
EMOTION_BPM_RANGE = {
    "悬疑": (80, 100),
    "紧张": (110, 130),
    "激昂": (120, 140),
    "欢快": (100, 120),
    "戏谑": (95, 115),
    "温暖": (70, 90),
    "治愈": (60, 80),
    "严肃": (90, 105),
}

# 情绪 → 曲库检索英文标签
EMOTION_MUSIC_TAGS = {
    "悬疑": ["suspense", "mystery"],
    "紧张": ["tense", "dramatic"],
    "激昂": ["epic", "uplifting"],
    "欢快": ["upbeat", "happy"],
    "戏谑": ["quirky", "playful"],
    "温暖": ["warm", "emotional"],
    "治愈": ["healing", "gentle"],
    "严肃": ["serious", "corporate"],
}


def select_bgm(emotion: str, bpm_hint: str = "mid") -> dict:
    """根据情绪标签和 BPM 提示选曲

    Args:
        emotion: 情绪标签（受控词表中的值）
        bpm_hint: BPM 节奏提示（low/mid/high）

    Returns:
        曲目信息 dict，含 track_id, emotion, bpm, ducking_db
    """
    # TODO: 对接免版权曲库 API（如 Pixabay Music / Uppbeat / YouTube Audio Library）
    bpm_range = EMOTION_BPM_RANGE.get(emotion, (90, 110))
    bpm_min, bpm_max = bpm_range

    if bpm_hint == "low":
        target_bpm = bpm_min
    elif bpm_hint == "high":
        target_bpm = bpm_max
    else:
        target_bpm = (bpm_min + bpm_max) // 2

    return {
        "track_id": "lib_placeholder_001",
        "emotion": emotion,
        "bpm": target_bpm,
        "ducking_db": -12.0,
    }
