"""统一 ID 生成工具"""
import uuid
from datetime import datetime


def generate_topic_id() -> str:
    """生成选题 ID：tp-{short_uuid}"""
    return f"tp-{uuid.uuid4().hex[:8]}"


def generate_material_id() -> str:
    """生成素材 ID：mt-{short_uuid}"""
    return f"mt-{uuid.uuid4().hex[:8]}"


def generate_script_id() -> str:
    """生成脚本 ID：sc-{short_uuid}"""
    return f"sc-{uuid.uuid4().hex[:8]}"


def generate_video_id() -> str:
    """生成视频 ID：vd-{short_uuid}"""
    return f"vd-{uuid.uuid4().hex[:8]}"


def generate_workflow_id() -> str:
    """生成工作流 ID：wf-{timestamp}"""
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"wf-{ts}"
