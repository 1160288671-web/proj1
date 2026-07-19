# MEMORY — 跨会话记忆

> 视频生成工作流的开发日志，记录每一步决策和理由。

---

## 项目初始化（2026-07-18）

- **框架选型**：LangGraph，因为工作流是确定性的 DAG 流水线，不需要动态 task delegation
- **LLM 抽象**：不绑定具体提供商，通过 `src/llm/provider.py` 统一接口
- **目录结构**：采用 LOOPKIT VAULT 结构（.claude/ 规则层 + src/ 执行层）
- **实施顺序**：先搭骨架（Step 1-4），再逐个填充 Agent（Step 5-6）
