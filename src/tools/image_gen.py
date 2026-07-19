"""AI 背景图生成工具（占位，后续对接生图服务）"""

# 全局风格后缀（保证同条视频画风一致）
DEFAULT_STYLE_SUFFIX = "cinematic lighting, 9:16 aspect ratio, realistic style, high quality"


async def generate_image(prompt: str, output_path: str, style_suffix: str = "") -> str:
    """生成 AI 背景图

    Args:
        prompt: 图像提示词
        output_path: 输出路径
        style_suffix: 统一追加的风格后缀（写在 skill 里）

    Returns:
        图片路径
    """
    full_prompt = f"{prompt}, {style_suffix}" if style_suffix else prompt
    full_prompt = full_prompt.strip().rstrip(",")

    # TODO: 对接生图 API（Stable Diffusion / DALL-E / Midjourney API）
    print(f"[ImageGen] 提示词: {full_prompt[:100]}...")

    # 占位：创建一个空文件
    from pathlib import Path
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.touch()

    return str(output)
