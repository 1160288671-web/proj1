"""全自动棒读视频生成工作流 · 主入口"""
import argparse
import asyncio
import os
from datetime import datetime

from src.main import VideoWorkflow
from src.llm.provider import OpenAICompatibleProvider


def parse_args():
    parser = argparse.ArgumentParser(description="全自动棒读视频生成工作流")
    parser.add_argument(
        "--from",
        dest="from_stage",
        type=str,
        default="A1",
        choices=["A1", "A2", "A3", "A4", "A5"],
        help="从哪个阶段开始（默认 A1）",
    )
    parser.add_argument(
        "--to",
        dest="to_stage",
        type=str,
        default="A6",
        choices=["A2", "A3", "A4", "A5", "A6"],
        help="执行到哪个阶段（默认 A6）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="干跑模式，使用 Mock 数据和 Mock LLM",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.environ.get("OPENAI_API_KEY", ""),
        help="OpenAI API Key（也可通过环境变量 OPENAI_API_KEY 设置）",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        help="API Base URL",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        help="模型名称",
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    # 构建 LLM Provider
    llm = None
    if not args.dry_run and args.api_key:
        llm = OpenAICompatibleProvider(
            api_key=args.api_key,
            base_url=args.base_url,
            model=args.model,
        )
        print(f"[LLM] {args.model} @ {args.base_url}")

    workflow = VideoWorkflow(
        workflow_id=f"wf-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        dry_run=args.dry_run,
        llm=llm,
    )
    await workflow.run(from_stage=args.from_stage, to_stage=args.to_stage)


if __name__ == "__main__":
    asyncio.run(main())
