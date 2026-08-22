from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .provider import ResponseProvider


class OpenAICompatibleProvider:
    """OpenAI-compatible Chat Completions API Provider。"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.api_key = (
            api_key
            or os.getenv("DEEPSEEK_API_KEY")
            or os.getenv("XIAOQI_LLM_API_KEY")
        )

        self.base_url = (
            base_url
            or os.getenv("XIAOQI_LLM_BASE_URL")
            or "https://api.deepseek.com"
        ).rstrip("/")

        self.model = model or os.getenv(
            "XIAOQI_LLM_MODEL",
            "deepseek-v4-flash",
        )

        raw_timeout = (
            str(timeout)
            if timeout is not None
            else os.getenv("XIAOQI_LLM_TIMEOUT", "60")
        )

        try:
            self.timeout = float(raw_timeout)
        except ValueError as exc:
            raise ValueError(
                "XIAOQI_LLM_TIMEOUT must be a number"
            ) from exc

        if self.timeout <= 0:
            raise ValueError(
                "timeout must be greater than zero"
            )

    def generate(self, prompt: str) -> str:
        """发送 Prompt 并返回模型生成的文本。"""

        if not prompt.strip():
            raise ValueError("prompt cannot be empty")

        if not self.api_key:
            raise RuntimeError(
                "XIAOQI_LLM_API_KEY or DEEPSEEK_API_KEY is not configured"
            )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        request = Request(
            url=f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            body = exc.read().decode(
                "utf-8",
                errors="replace",
            )
            raise RuntimeError(
                f"LLM API returned HTTP {exc.code}: {body}"
            ) from exc
        except URLError as exc:
            raise RuntimeError(
                f"LLM API request failed: {exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise RuntimeError(
                "LLM API request timed out"
            ) from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "LLM API returned invalid JSON"
            ) from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (
            KeyError,
            IndexError,
            TypeError,
        ) as exc:
            raise RuntimeError(
                "LLM API response does not contain "
                "choices[0].message.content"
            ) from exc

        if not isinstance(content, str):
            raise RuntimeError(
                "LLM API response content is not text"
            )

        content = content.strip()

        if not content:
            raise RuntimeError(
                "LLM API returned an empty response"
            )

        return content

    def __repr__(self) -> str:
        return (
            f"OpenAICompatibleProvider("
            f"base_url={self.base_url!r}, "
            f"model={self.model!r})"
        )


def is_response_provider(provider: object) -> bool:
    """运行时检查对象是否符合 ResponseProvider 接口。"""

    return isinstance(provider, ResponseProvider)
