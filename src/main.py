"""主入口 —— 工作流协调器"""
import os
from typing import Optional

from src.graph import build_graph
from src.llm.provider import OpenAICompatibleProvider, MockProvider, LLMProvider
from src.utils.id_gen import generate_workflow_id


class VideoWorkflow:
    """视频生成工作流"""

    STAGE_ORDER = ["A1", "A2", "A3", "A4", "A5", "A6"]

    def __init__(self, workflow_id: Optional[str] = None, dry_run: bool = False, llm: Optional[LLMProvider] = None):
        self.workflow_id = workflow_id or generate_workflow_id()
        self.dry_run = dry_run

        # LLM 提供商：外部传入 > 环境变量 > Mock
        if llm:
            self.llm = llm
        elif api_key := os.environ.get("OPENAI_API_KEY"):
            self.llm = OpenAICompatibleProvider(
                api_key=api_key,
                base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
            )
        else:
            self.llm = MockProvider()

        self.graph = build_graph(llm=self.llm)

    async def run(self, from_stage: str = "A1", to_stage: str = "A6") -> dict:
        """执行工作流

        Args:
            from_stage: 起始阶段（A1-A5）
            to_stage: 结束阶段（A2-A6）
        """
        start_idx = self.STAGE_ORDER.index(from_stage)
        end_idx = self.STAGE_ORDER.index(to_stage)
        if start_idx >= end_idx:
            raise ValueError(f"起始阶段 {from_stage} 必须在结束阶段 {to_stage} 之前")

        stages = self.STAGE_ORDER[start_idx:end_idx + 1]
        print(f"\n{'='*50}")
        print(f"[Workflow {self.workflow_id}] 启动: {from_stage} → {to_stage}")
        print(f"[LLM] {'Mock (干跑模式)' if isinstance(self.llm, MockProvider) else self.llm.model}")
        print(f"{'='*50}\n")

        # 初始化状态
        initial_state: dict = {
            "workflow_id": self.workflow_id,
            "stage": from_stage,
            "dry_run": self.dry_run,
            "config": {},
            "errors": [],
        }

        # 执行图
        final_state = await self.graph.ainvoke(initial_state)

        # 报告
        print(f"\n{'='*50}")
        errors = final_state.get("errors", [])
        if errors:
            print(f"[Workflow {self.workflow_id}] 完成，有 {len(errors)} 个错误:")
            for e in errors:
                print(f"  ✗ {e}")
        else:
            print(f"[Workflow {self.workflow_id}] 全部完成，无错误")

        # 输出摘要
        topics = final_state.get("topics", [])
        scripts = final_state.get("scripts", [])
        videos = final_state.get("video_outputs", [])
        published = final_state.get("publish_results", [])
        print(f"  选题: {len(topics)} | 脚本: {len(scripts)} | 视频: {len(videos)} | 待发布: {len(published)}")
        print(f"{'='*50}\n")

        return final_state
