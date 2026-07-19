"""Agent 基类 —— 区分执行型与判断型"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from src.llm.provider import LLMProvider


class BaseAgent(ABC):
    """Agent 基类"""

    SKILL_BASE = Path(".claude/skills")

    def __init__(self, name: str, llm: Optional[LLMProvider] = None):
        self.name = name
        self.llm = llm

    @abstractmethod
    async def run(self, state: dict) -> dict:
        """执行 agent 逻辑，读 state 返回修改后的 state"""
        ...

    def log(self, msg: str):
        print(f"[{self.name}] {msg}")

    def _load_skill(self, relative_path: str) -> str:
        """读取 .claude/skills/ 下的 .md 文件"""
        path = self.SKILL_BASE / relative_path
        if not path.exists():
            self.log(f"WARNING: skill 文件不存在: {path}")
            return ""
        return path.read_text(encoding="utf-8")


class ExecutionAgent(BaseAgent):
    """执行型 Agent：纯代码逻辑，不使用 LLM"""
    pass


class JudgementAgent(BaseAgent):
    """判断型 Agent：核心逻辑依赖 LLM"""

    def __init__(self, name: str, llm: LLMProvider):
        super().__init__(name, llm)
        if llm is None:
            raise ValueError(f"JudgementAgent '{name}' 必须传入 LLMProvider")
