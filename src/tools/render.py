"""ffmpeg 视频合成渲染工具

固定管线（agent 只填参数不决策）：
1. 背景图 + TTS 音频 + BGM 合并
2. 叠加字幕
3. 输出成品 MP4
"""
import subprocess
from pathlib import Path


def render_video(
    output_path: str,
    resolution: str = "1080x1920",
    fps: int = 30,
    format: str = "mp4",
    inputs: list[dict] | None = None,
) -> Path:
    """ffmpeg 合成渲染主入口

    Args:
        output_path: 输出视频路径
        resolution: 分辨率（宽x高）
        fps: 帧率
        format: 输出格式
        inputs: 输入素材列表 [{"image": "path", "audio": "path", "duration": 3.0}, ...]

    Returns:
        输出文件路径
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    if not inputs:
        print(f"[Render] 无输入素材，生成占位文件: {output}")
        output.touch()
        return output

    try:
        # 构建 ffmpeg 命令（简化版，实际需按分镜拼接）
        _build_and_execute(output, inputs, resolution, fps)
    except FileNotFoundError:
        print(f"[Render] ffmpeg 未安装，写入占位文件: {output}")
        output.touch()
    except Exception as e:
        print(f"[Render] 渲染失败: {e}")
        output.touch()

    return output


def _build_and_execute(
    output: Path,
    inputs: list[dict],
    resolution: str,
    fps: int,
):
    """构建 ffmpeg 命令并执行"""
    # TODO: 实现完整的分镜合成逻辑：
    #   1. 每组分镜生成一段视频片段（背景图 + 音频）
    #   2. 用 concat 拼接所有片段
    #   3. 叠加字幕（drawtext）
    #   4. 加入 BGM（amix + 闪避压缩）

    # 占位：检查 ffmpeg 是否可用
    subprocess.run(
        ["ffmpeg", "-version"],
        capture_output=True,
        check=True,
        timeout=10,
    )

    # 构建简单的测试命令
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", f"color=c=black:s={resolution}:d=3",
        "-c:v", "libx264",
        "-r", str(fps),
        "-pix_fmt", "yuv420p",
        str(output),
    ]
    subprocess.run(cmd, capture_output=True, check=True, timeout=300)
