"""LLM provider with Groq primary + OpenAI fallback."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import SecretStr

load_dotenv()


class LLMProvider:
    """LLM provider with Groq as primary and OpenAI as fallback."""

    def __init__(self):
        self._primary: BaseChatModel | None = None
        self._fallback: BaseChatModel | None = None
        self._use_fallback = False

    def _init_primary(self) -> BaseChatModel:
        from langchain_groq import ChatGroq

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set")
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=SecretStr(api_key),
            temperature=0,
        )

    def _init_fallback(self) -> BaseChatModel:
        from langchain_openai import ChatOpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        return ChatOpenAI(
            model="gpt-4o",
            api_key=SecretStr(api_key),
            temperature=0,
        )

    @property
    def llm(self) -> BaseChatModel:
        if self._use_fallback:
            if self._fallback is None:
                self._fallback = self._init_fallback()
            return self._fallback
        if self._primary is None:
            self._primary = self._init_primary()
        return self._primary

    async def ainvoke(self, prompt: str, **kwargs: Any):
        try:
            return await self.llm.ainvoke([HumanMessage(content=prompt)], **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            if any(
                kw in error_str for kw in ["rate limit", "429", "quota", "overloaded"]
            ):
                if not self._use_fallback:
                    print(
                        "[WARN] Primary LLM rate limited, switching to OpenAI fallback"
                    )
                    self._use_fallback = True
                    return await self.llm.ainvoke(
                        [HumanMessage(content=prompt)], **kwargs
                    )
            raise

    def invoke(self, prompt: str, **kwargs: Any):
        try:
            return self.llm.invoke([HumanMessage(content=prompt)], **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            if any(
                kw in error_str for kw in ["rate limit", "429", "quota", "overloaded"]
            ):
                if not self._use_fallback:
                    print(
                        "[WARN] Primary LLM rate limited, switching to OpenAI fallback"
                    )
                    self._use_fallback = True
                    return self.llm.invoke([HumanMessage(content=prompt)], **kwargs)
            raise


_provider: LLMProvider | None = None


def get_llm() -> LLMProvider:
    global _provider
    if _provider is None:
        _provider = LLMProvider()
    return _provider
