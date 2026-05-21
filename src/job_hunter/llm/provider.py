"""LLM provider configured via environment variables."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import SecretStr

load_dotenv()

_SUPPORTED_PROVIDERS = ("groq", "openai", "claude")

_DEFAULT_MODELS = {
    "groq": "llama-3.3-70b-versatile",
    "openai": "gpt-4o",
    "claude": "claude-sonnet-4-6",
}


def _build_llm(provider: str, model: str) -> BaseChatModel:
    if provider == "groq":
        from langchain_groq import ChatGroq

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set")
        return ChatGroq(model=model, api_key=SecretStr(api_key), temperature=0)

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        return ChatOpenAI(model=model, api_key=SecretStr(api_key), temperature=0)

    if provider == "claude":
        from langchain_anthropic import ChatAnthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        return ChatAnthropic(model=model, api_key=SecretStr(api_key), temperature=0)  # type: ignore[call-arg]

    raise ValueError(
        f"Unsupported provider '{provider}'. Supported: {_SUPPORTED_PROVIDERS}"
    )


def _resolve_provider_config(role: str) -> tuple[str, str] | None:
    """Return (provider, model) for 'primary' or 'fallback', or None if not configured."""
    provider_key = f"LLM_{role.upper()}_PROVIDER"
    model_key = f"LLM_{role.upper()}_MODEL"

    provider = os.getenv(provider_key, "").strip().lower()
    if not provider:
        return None

    if provider not in _SUPPORTED_PROVIDERS:
        raise ValueError(
            f"{provider_key}='{provider}' is invalid. Supported: {_SUPPORTED_PROVIDERS}"
        )

    model = os.getenv(model_key, "").strip() or _DEFAULT_MODELS[provider]
    return provider, model


class LLMProvider:
    """LLM provider driven by env vars LLM_PRIMARY_PROVIDER/MODEL and LLM_FALLBACK_PROVIDER/MODEL."""

    def __init__(self):
        self._primary: BaseChatModel | None = None
        self._fallback: BaseChatModel | None = None
        self._use_fallback = False

        primary_cfg = _resolve_provider_config("primary")
        if primary_cfg is None:
            # Backwards-compatible default: groq primary
            primary_cfg = ("groq", _DEFAULT_MODELS["groq"])
        self._primary_provider, self._primary_model = primary_cfg

        fallback_cfg = _resolve_provider_config("fallback")
        if fallback_cfg is None:
            # Backwards-compatible default: pick the first available key that isn't primary
            _key_map = {
                "groq": os.getenv("GROQ_API_KEY", "").strip(),
                "openai": os.getenv("OPENAI_API_KEY", "").strip(),
                "claude": os.getenv("ANTHROPIC_API_KEY", "").strip(),
            }
            for candidate in ("openai", "groq", "claude"):
                if candidate != self._primary_provider and _key_map[candidate]:
                    fallback_cfg = (candidate, _DEFAULT_MODELS[candidate])
                    break
        self._fallback_provider = fallback_cfg[0] if fallback_cfg else None
        self._fallback_model = fallback_cfg[1] if fallback_cfg else None

        print(
            f"[INFO] LLM primary: {self._primary_provider}/{self._primary_model}"
            + (
                f" | fallback: {self._fallback_provider}/{self._fallback_model}"
                if self._fallback_provider
                else " | no fallback configured"
            )
        )

    @property
    def llm(self) -> BaseChatModel:
        if self._use_fallback:
            if self._fallback is None:
                if not self._fallback_provider:
                    raise RuntimeError("No fallback LLM configured")
                self._fallback = _build_llm(self._fallback_provider, self._fallback_model)  # type: ignore[arg-type]
            return self._fallback
        if self._primary is None:
            self._primary = _build_llm(self._primary_provider, self._primary_model)
        return self._primary

    async def ainvoke(self, prompt: str, **kwargs: Any):
        try:
            return await self.llm.ainvoke([HumanMessage(content=prompt)], **kwargs)
        except Exception as e:
            if _is_rate_limit(e) and not self._use_fallback and self._fallback_provider:
                print(
                    f"[WARN] Primary LLM ({self._primary_provider}) rate limited, "
                    f"switching to fallback ({self._fallback_provider})"
                )
                self._use_fallback = True
                return await self.llm.ainvoke([HumanMessage(content=prompt)], **kwargs)
            raise

    def invoke(self, prompt: str, **kwargs: Any):
        try:
            return self.llm.invoke([HumanMessage(content=prompt)], **kwargs)
        except Exception as e:
            if _is_rate_limit(e) and not self._use_fallback and self._fallback_provider:
                print(
                    f"[WARN] Primary LLM ({self._primary_provider}) rate limited, "
                    f"switching to fallback ({self._fallback_provider})"
                )
                self._use_fallback = True
                return self.llm.invoke([HumanMessage(content=prompt)], **kwargs)
            raise


def _is_rate_limit(e: Exception) -> bool:
    return any(
        kw in str(e).lower() for kw in ["rate limit", "429", "quota", "overloaded"]
    )


_provider: LLMProvider | None = None


def get_llm() -> LLMProvider:
    global _provider
    if _provider is None:
        _provider = LLMProvider()
    return _provider
