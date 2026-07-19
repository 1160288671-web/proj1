"""LangGraph WorkflowState —— 贯穿所有 Agent 的共享状态"""
from typing import Annotated, Any, Optional, TypedDict
from operator import add


class WorkflowState(TypedDict, total=False):
    """图状态：每个 Node 读/写此对象，按 key 传递"""

    # ====== 配置 ======
    config: dict[str, Any]                             # 运行时配置（数据源、权重、阈值等）

    # ====== A1 产出 ======
    hot_raw: list[dict]                                # hot_raw.json 内容

    # ====== A2 产出 ======
    topics: list[dict]                                 # topics.json 内容（最多 3 个选题）

    # ====== A3 产出 ======
    materials: dict[str, list[dict]]                   # topic_id → [Material dict]

    # ====== A4 产出 ======
    scripts: list[dict]                                # script.json 内容（每个选题一个）

    # ====== A5 产出 ======
    video_outputs: Annotated[list[dict], add]          # 各视频产出信息（累加）

    # ====== A6 产出 ======
    publish_results: Annotated[list[dict], add]        # 发布打包结果（累加）

    # ====== 贯穿字段 ======
    workflow_id: str                                   # 工作流实例 ID
    stage: str                                         # 当前阶段
    errors: Annotated[list[str], add]                  # 错误收集（累加）
    dry_run: bool                                      # 干跑模式
