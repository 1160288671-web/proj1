"""A5 音画制作（执行型）：TTS → BGM → 背景图 → 字幕 → 合成渲染"""
import os
import asyncio

from src.agents.base import ExecutionAgent
from src.utils.id_gen import generate_video_id
from src.tools.tts import synthesize as tts_synthesize, get_voice
from src.tools.bgm import select_bgm
from src.tools.image_gen import generate_image, DEFAULT_STYLE_SUFFIX
from src.tools.render import render_video


class A5Producer(ExecutionAgent):
    """A5：音画制作"""

    OUTPUT_DIR = "data/output"

    def __init__(self):
        super().__init__(name="A5_Producer")

    async def run(self, state: dict) -> dict:
        self.log("开始音画制作...")

        scripts = state.get("scripts", [])
        video_outputs = []

        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

        for script in scripts:
            script_id = script.get("script_id", "unknown")
            self.log(f"  制作脚本 {script_id}...")

            try:
                video = await self._produce_one(script)
                video_outputs.append(video)
            except Exception as e:
                self.log(f"  ERROR 脚本 {script_id}: {e}")
                state.setdefault("errors", []).append(
                    f"A5: 脚本 {script_id} 制作失败: {e}"
                )

        state["video_outputs"] = video_outputs
        state["stage"] = "A5_produce"
        self.log(f"音画制作完成，共 {len(video_outputs)} 个视频")
        return state

    async def _produce_one(self, script: dict) -> dict:
        """制作单个视频"""
        script_id = script["script_id"]
        storyboard = script.get("storyboard", [])
        video_id = generate_video_id()

        video_dir = os.path.join(self.OUTPUT_DIR, video_id)
        os.makedirs(video_dir, exist_ok=True)

        assets = []
        bgm_info = {}

        # Step 1-4: 逐分镜处理
        for scene in storyboard:
            seq = scene["seq"]
            emotion = scene.get("emotion", "严肃")

            # Step 1: TTS 配音
            voice_id = get_voice(emotion)
            audio_path = os.path.join(video_dir, f"voice_{seq:02d}.mp3")
            await tts_synthesize(
                text=scene.get("voice_text", ""),
                output_path=audio_path,
                voice_id=voice_id,
                speed=1.0 if emotion not in ("悬疑", "温暖", "治愈") else 0.9,
            )
            self.log(f"    TTS 分镜 {seq}: {audio_path}")

            # Step 2: BGM 选配（只做一次，覆盖全片）
            if not bgm_info:
                bgm_info = select_bgm(
                    emotion=emotion,
                    bpm_hint=scene.get("bpm_hint", "mid"),
                )
                self.log(f"    BGM: {bgm_info['track_id']} ({emotion}, {bgm_info['bpm']}bpm)")

            # Step 3: 背景图生成
            image_path = os.path.join(video_dir, f"bg_{seq:02d}.png")
            await generate_image(
                prompt=scene.get("visual_prompt", "abstract background"),
                output_path=image_path,
                style_suffix=DEFAULT_STYLE_SUFFIX,
            )
            self.log(f"    背景图 分镜 {seq}: {image_path}")

            assets.append({
                "seq": seq,
                "image_path": image_path,
                "audio_path": audio_path,
                "prompt_used": scene.get("visual_prompt", ""),
                "emotion": emotion,
                "duration_sec": scene.get("duration_sec", 5),
            })

        # Step 5: ffmpeg 合成渲染
        output_video = os.path.join(video_dir, f"{video_id}.mp4")
        render_inputs = [
            {
                "image": a["image_path"],
                "audio": a["audio_path"],
                "duration": a["duration_sec"],
            }
            for a in assets
        ]
        result = render_video(
            output_path=output_video,
            resolution="1080x1920",
            fps=30,
            inputs=render_inputs,
        )
        self.log(f"    合成完成: {output_video}")

        # 构建 production.json 内容
        production = {
            "video_id": video_id,
            "script_id": script_id,
            "tts": {
                "voice_id": get_voice(assets[0]["emotion"]) if assets else "v_default",
                "speed": 1.0,
            },
            "bgm": bgm_info,
            "assets": [
                {
                    "seq": a["seq"],
                    "image_path": a["image_path"],
                    "prompt_used": a["prompt_used"],
                }
                for a in assets
            ],
            "render": {
                "resolution": "1080x1920",
                "fps": 30,
                "format": "mp4",
            },
            "output_video": str(result),
        }

        return production
