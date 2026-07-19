"""LangGraph DAG 定义 —— 视频生成工作流的执行图"""
from typing import Literal, Optional
from langgraph.graph import StateGraph, START, END

from src.llm.provider import LLMProvider, MockProvider
from src.agents.a1_collector import A1Collector
from src.agents.a2_selector import A2Selector
from src.agents.a3_material import A3Material
from src.agents.a4_scriptwriter import A4ScriptWriter
from src.agents.a5_producer import A5Producer
from src.agents.a6_publisher import A6Publisher


def build_graph(llm: Optional[LLMProvider] = None) -> StateGraph:
    """构建 A1 → A2 → A3 → A4 → A5 → A6 DAG

    Args:
        llm: LLM 提供商，若不传入则使用 MockProvider（用于测试/干跑）。
             只有 A2 和 A4 使用 LLM，其余 agent 不受影响。
    """
    if llm is None:
        llm = MockProvider()

    builder = StateGraph(dict)

    # 注册所有 Node
    builder.add_node("A1_collect", A1Collector().run)
    builder.add_node("A2_select", A2Selector(llm).run)
    builder.add_node("A3_material", A3Material().run)
    builder.add_node("A4_script", A4ScriptWriter(llm).run)
    builder.add_node("A5_produce", A5Producer().run)
    builder.add_node("A6_publish", A6Publisher().run)

    # DAG 边
    builder.add_edge(START, "A1_collect")
    builder.add_edge("A1_collect", "A2_select")
    builder.add_edge("A2_select", "A3_material")
    builder.add_edge("A3_material", "A4_script")

    # A4 → A5 是唯一条件分支：素材不足则跳过
    builder.add_conditional_edges(
        "A4_script",
        _route_from_a4,
        {
            "continue": "A5_produce",
            "skip": END,
        },
    )
    builder.add_edge("A5_produce", "A6_publish")
    builder.add_edge("A6_publish", END)

    return builder.compile()


def _route_from_a4(state: dict) -> Literal["continue", "skip"]:
    """A4 条件分支：检查是否有脚本产出"""
    scripts = state.get("scripts", [])
    if not scripts:
        return "skip"
    return "continue"
