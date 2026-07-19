"""A6 发布打包（执行型）：打包成片 + 元数据到待发布目录"""
import json
import os
import shutil
from datetime import datetime

from src.agents.base import ExecutionAgent


class A6Publisher(ExecutionAgent):
    """A6：发布打包"""

    PUBLISH_DIR = "data/publish"

    def __init__(self):
        super().__init__(name="A6_Publisher")

    async def run(self, state: dict) -> dict:
        self.log("开始发布打包...")

        video_outputs = state.get("video_outputs", [])
        scripts = state.get("scripts", [])
        publish_results = []

        os.makedirs(self.PUBLISH_DIR, exist_ok=True)

        for i, video in enumerate(video_outputs):
            video_id = video.get("video_id", f"vd-{i+1:03d}")
            self.log(f"  打包视频 {video_id}...")

            script = scripts[i] if i < len(scripts) else {}
            target_dir = os.path.join(self.PUBLISH_DIR, video_id)

            # 创建发布目录
            os.makedirs(target_dir, exist_ok=True)

            # 复制成片
            src_video = video.get("output_video", "")
            if src_video and os.path.exists(src_video):
                dst_video = os.path.join(target_dir, f"{video_id}.mp4")
                try:
                    shutil.copy2(src_video, dst_video)
                except Exception as e:
                    self.log(f"  WARNING 复制视频失败: {e}")
                    dst_video = ""

            # 生成 publish.json
            publish_data = {
                "video_id": video_id,
                "script_id": script.get("script_id", video.get("script_id", "")),
                "topic_id": script.get("topic_id", ""),
                "platform": "douyin",
                "title": self._pick_title(script),
                "description": self._make_description(script),
                "tags": self._make_tags(script),
                "cover_image": "cover.png",
                "review_status": "pending_human",
                "video_file": dst_video,
                "packaged_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
            }

            publish_path = os.path.join(target_dir, "publish.json")
            with open(publish_path, "w", encoding="utf-8") as f:
                json.dump(publish_data, f, ensure_ascii=False, indent=2)
            self.log(f"    publish.json → {publish_path}")

            publish_results.append(publish_data)

        state["publish_results"] = publish_results
        state["stage"] = "A6_publish"
        self.log(f"发布打包完成，共 {len(publish_results)} 个待发布")
        return state

    def _pick_title(self, script: dict) -> str:
        """从候选标题中选取第一个"""
        titles = script.get("title_options", [])
        return titles[0] if titles else "未命名"

    def _make_description(self, script: dict) -> str:
        """生成简介"""
        exp = script.get("experience", {})
        primary = exp.get("primary", "")
        hook = script.get("hook", "")
        parts = []
        if hook:
            parts.append(hook)
        if primary:
            parts.append(f"#棒读 #{primary}")
        return " ".join(parts)

    def _make_tags(self, script: dict) -> list[str]:
        """生成标签"""
        tags = []
        exp = script.get("experience", {})
        primary = exp.get("primary", "")
        if primary:
            tags.append(primary)
        tags.append("棒读")
        tags.append("娱乐")
        return tags[:5]
