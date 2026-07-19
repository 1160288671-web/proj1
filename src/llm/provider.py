"""LLM Provider 抽象层 + OpenAI 兼容实现"""
import json
from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx


class LLMProvider(ABC):
    """LLM 调用统一接口"""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """发送对话请求，返回文本响应"""
        ...

    @abstractmethod
    async def chat_with_json(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """发送请求，强制返回 JSON object"""
        ...


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI 兼容 API 实现

    支持 OpenAI / 各类兼容网关（通过 base_url 配置）
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
        timeout: float = 120.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def _request(self, body: dict) -> dict:
        """发送 POST 请求到 chat/completions"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            resp.raise_for_status()
            return resp.json()

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """标准对话"""
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = await self._request(body)
        return data["choices"][0]["message"]["content"]

    async def chat_with_json(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """强制 JSON 输出模式"""
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        data = await self._request(body)
        raw = data["choices"][0]["message"]["content"]
        return json.loads(raw)


class MockProvider(LLMProvider):
    """Mock 实现：用于测试和干跑"""

    async def chat(self, messages, *, temperature=0.7, max_tokens=4096):
        return "[MOCK] 这是模拟 LLM 响应"

    async def chat_with_json(self, messages, *, temperature=0.3, max_tokens=4096):
        return {"mock": True, "message": "这是模拟结构化输出"}
