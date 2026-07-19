"""TTS 配音工具（占位，后续对接 TTS 服务）"""
import json
import subprocess
from pathlib import Path

# 情绪 → 音色映射（初稿，后续从 skill 文件读取）
EMOTION_VOICE_MAP = {
    "悬疑": "v_qinglang_01",
    "紧张": "v_qinglang_01",
    "激昂": "v_qinglang_01",
    "欢快": "v_qinglang_01",
    "戏谑": "v_qinglang_01",
    "温暖": "v_qinglang_01",
    "治愈": "v_qinglang_01",
    "严肃": "v_qinglang_01",
}


def get_voice(emotion: str) -> str:
    """按情绪标签获取音色 ID"""
    return EMOTION_VOICE_MAP.get(emotion, "v_qinglang_01")


async def synthesize(
    text: str,
    output_path: str,
    voice_id: str = "v_qinglang_01",
    speed: float = 1.0,
) -> Path:
    """合成 TTS 音频

    Args:
        text: 配音文本
        output_path: 输出音频路径
        voice_id: 音色 ID
        speed: 语速（0.5-2.0）

    Returns:
        输出文件路径
    """
    # TODO: 对接实际 TTS 服务（如 Edge-TTS / Azure / 火山引擎）
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # 占位实现：尝试用系统自带 edge-tts
    try:
        result = subprocess.run(
            [
                "edge-tts",
                "--voice", "zh-CN-XiaoxiaoNeural",
                "--text", text,
                "--write-media", str(output),
                f"--rate={int((speed - 1.0) * 100):+d}%",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"TTS failed: {result.stderr}")
    except FileNotFoundError:
        print(f"[TTS] edge-tts 未安装，写入占位文件: {output}")
        output.touch()
    except Exception as e:
        print(f"[TTS] 合成失败: {e}")
        output.touch()

    return output
