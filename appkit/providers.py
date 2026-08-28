"""小七 · Provider 管理（AI / TTS / STT）

- AIProvider 统一接口：DeepSeek / OpenAI Compatible（同一实现，换 base_url/model）
- TTSProvider / STTProvider 状态统一接口

切换 Provider 时 Core（chat）无需修改——通过统一接口注入。
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------
# AI Provider
# ---------------------------------------------------------


@dataclass(frozen=True)
class AIProviderConfig:
    provider: str = "deepseek"
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-v4-flash"
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 1024
    timeout: float = 60.0


class AIProvider:
    """OpenAI 兼容 Chat Completions 客户端（DeepSeek/Qwen/OpenAI/自定义）。"""

    def __init__(self, config: AIProviderConfig | None = None) -> None:
        self.config = config or self._load_env_config()

    @staticmethod
    def _load_env_config() -> AIProviderConfig:
        provider = os.getenv("XIAOQI_AI_PROVIDER", "deepseek")
        api_key = (
            os.getenv("XIAOQI_LLM_API_KEY")
            or os.getenv("DEEPSEEK_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or ""
        )
        base_url = os.getenv(
            "XIAOQI_LLM_BASE_URL",
            "https://api.deepseek.com",
        )
        model = os.getenv("XIAOQI_LLM_MODEL", "deepseek-v4-flash")
        return AIProviderConfig(
            provider=provider,
            base_url=base_url.rstrip("/"),
            model=model,
            api_key=api_key,
        )

    @property
    def available(self) -> bool:
        return bool(self.config.api_key)

    def status(self) -> dict:
        return {
            "provider": self.config.provider,
            "available": self.available,
            "has_api_key": bool(self.config.api_key),
            "model": self.config.model,
            "base_url": self.config.base_url,
        }

    def chat(self, messages: list[dict]) -> str:
        """messages: [{"role": "user", "content": "..."}] -> 回复文本。"""

        if not self.config.api_key:
            raise RuntimeError("AI API key not configured")

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        request = urllib.request.Request(
            url=f"{self.config.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.config.timeout,
            ) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:200]
            raise RuntimeError(f"AI API HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"AI API request failed: {exc.reason}") from exc
        except TimeoutError as exc:
            raise RuntimeError("AI API request timed out") from exc

        try:
            data = json.loads(raw)
            return data["choices"][0]["message"]["content"].strip()
        except (json.JSONDecodeError, KeyError, IndexError) as exc:
            raise RuntimeError("AI API bad response") from exc

    def test_connection(self) -> dict:
        """测试连接：调用一次极短请求。"""

        if not self.config.api_key:
            return {"ok": False, "error": "API key not configured"}

        try:
            reply = self.chat(
                [{"role": "user", "content": "ping"}]
            )
            return {"ok": True, "reply": reply[:80]}
        except RuntimeError as exc:
            return {"ok": False, "error": str(exc)}


# ---------------------------------------------------------
# TTS / STT Provider 状态
# ---------------------------------------------------------


def tts_provider_status() -> dict:
    """TTS Provider 统一状态。"""

    from voice.providers.alibaba_tts import (
        AlibabaTTS,
        load_tts_config,
    )

    config = load_tts_config()
    alibaba = AlibabaTTS(config)

    return {
        "provider": config.engine if hasattr(config, "engine") else "alibaba",
        "alibaba": {
            "available": alibaba.available,
            "has_api_key": bool(config.api_key),
            "has_voice_id": bool(config.voice),
        },
        "browser": {"available": True},
    }


def stt_provider_status() -> dict:
    """STT Provider 统一状态。"""

    from voice.engines import STTEngine

    engine = STTEngine()

    return {
        "provider": "faster-whisper",
        "faster_whisper": {
            "available": engine.available,
            "detail": engine.status().detail,
        },
        "browser": {"available": True},
    }
