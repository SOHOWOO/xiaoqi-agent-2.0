"""小七 · 阿里云 Model Studio（百炼）Provider

- AlibabaTTS：非实时 Qwen3-TTS 语音合成（HTTP）
- AlibabaVoiceClone：声音复刻（创建/查询/删除 Voice ID）

以阿里云 Model Studio 官方 API 为准（2026 文档）：
  TTS endpoint:
    POST {base}/api/v1/services/aigc/multimodal-generation/generation
  Voice clone endpoint:
    POST https://{WorkspaceId}.{region}.maas.aliyuncs.com/api/v1/services/audio/tts/customization

API Key 只由后端读取，绝不写入 JS / Git / profile.json / README。
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Optional

# 阿里云百炼官方 region -> 域名（用户要求新加坡优先）
_REGION_HOSTS = {
    "singapore": "dashscope-intl.aliyuncs.com",
    "beijing": "dashscope.aliyuncs.com",
    "cn-beijing": "dashscope.aliyuncs.com",
    "ap-southeast-1": "dashscope-intl.aliyuncs.com",
}

_TTS_PATH = "/api/v1/services/aigc/multimodal-generation/generation"

_REGION_MAA = {
    "singapore": "ap-southeast-1",
    "beijing": "cn-beijing",
    "cn-beijing": "cn-beijing",
    "ap-southeast-1": "ap-southeast-1",
}


class AlibabaTTSError(Exception):
    """阿里云 TTS 错误（项目自有错误类型，不暴露原始响应头）。"""

    def __init__(self, kind: str, message: str) -> None:
        self.kind = kind
        self.message = message
        super().__init__(f"{kind}: {message}")


def _base_url(region: str) -> str:
    host = _REGION_HOSTS.get(region, _REGION_HOSTS["singapore"])
    return f"https://{host}"


def _clone_base_url(workspace_id: str, region: str) -> str:
    maa_region = _REGION_MAA.get(region, "ap-southeast-1")
    return (
        f"https://{workspace_id}.{maa_region}.maas.aliyuncs.com/"
        "api/v1/services/audio/tts/customization"
    )


def _read_api_key() -> Optional[str]:
    """API Key 只从环境变量读取。"""

    return (
        os.getenv("XIAOQI_ALIBABA_API_KEY")
        or os.getenv("DASHSCOPE_API_KEY")
    )


def _post_json(
    url: str,
    api_key: str,
    payload: dict,
    *,
    timeout: float = 30.0,
    headers: Optional[dict] = None,
) -> dict:
    """POST JSON，统一错误处理（不记录 API Key / 请求头）。"""

    body = json.dumps(payload).encode("utf-8")

    request_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if headers:
        request_headers.update(headers)

    request = urllib.request.Request(
        url,
        data=body,
        headers=request_headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise _http_error(exc) from exc
    except urllib.error.URLError as exc:
        raise AlibabaTTSError(
            "NETWORK",
            f"request failed: {exc.reason}",
        ) from exc
    except TimeoutError as exc:
        raise AlibabaTTSError("TIMEOUT", "request timed out") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AlibabaTTSError(
            "BAD_RESPONSE",
            "invalid JSON from API",
        ) from exc


def _http_error(exc: urllib.error.HTTPError) -> AlibabaTTSError:
    """HTTP 错误 -> 项目自有错误类型。"""

    kind_map = {
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        429: "RATE_LIMITED",
    }

    kind = kind_map.get(exc.code, "HTTP_ERROR")

    detail = ""
    try:
        body = exc.read()
        if body:
            detail = body.decode("utf-8", errors="replace")[:200]
    except Exception:
        detail = ""

    return AlibabaTTSError(kind, f"HTTP {exc.code} {detail}")


# ---------------------------------------------------------
# TTS
# ---------------------------------------------------------


@dataclass(frozen=True)
class AlibabaTTSConfig:
    api_key: str = ""
    model: str = "qwen3-tts-flash"
    voice: str = ""
    region: str = "singapore"
    language: str = "zh"
    timeout: float = 30.0
    extra: dict = field(default_factory=dict)


def load_tts_config() -> AlibabaTTSConfig:
    """从环境变量加载 TTS 配置（Voice ID 从 env 读取，不进 Git）。"""

    return AlibabaTTSConfig(
        api_key=_read_api_key() or "",
        model=os.getenv(
            "XIAOQI_ALIBABA_MODEL",
            "qwen3-tts-flash",
        ),
        voice=os.getenv("XIAOQI_ALIBABA_VOICE_ID", ""),
        region=os.getenv(
            "XIAOQI_ALIBABA_REGION",
            "singapore",
        ),
        language=os.getenv(
            "XIAOQI_ALIBABA_LANGUAGE",
            "zh",
        ),
        timeout=float(
            os.getenv("XIAOQI_ALIBABA_TIMEOUT", "30")
        ),
    )


class AlibabaTTS:
    """阿里云 Qwen3-TTS 语音合成客户端（HTTP 非流式 / SSE 流式）。"""

    provider = "alibaba"

    def __init__(
        self,
        config: AlibabaTTSConfig | None = None,
    ) -> None:
        self.config = config or load_tts_config()

    @property
    def available(self) -> bool:
        """API Key + Voice ID 都配置才视为可用（不伪造）。"""

        return bool(self.config.api_key and self.config.voice)

    def status(self) -> dict:
        return {
            "provider": self.provider,
            "available": self.available,
            "model": self.config.model if self.config.api_key else "",
            "has_api_key": bool(self.config.api_key),
            "has_voice_id": bool(self.config.voice),
            "voice_id": self.config.voice if self.config.available else "",
        }

    def synthesize(
        self,
        text: str,
        *,
        voice: str | None = None,
    ) -> bytes:
        """文本 -> 音频字节（HTTP 非流式，从 OSS url 下载）。"""

        if not self.config.api_key:
            raise AlibabaTTSError(
                "NO_API_KEY",
                "XIAOQI_ALIBABA_API_KEY 未配置",
            )

        voice = voice or self.config.voice

        if not voice:
            raise AlibabaTTSError(
                "NO_VOICE_ID",
                "XIAOQI_ALIBABA_VOICE_ID 未配置",
            )

        payload = {
            "model": self.config.model,
            "input": {
                "text": text,
                "voice": voice,
                "language_type": self.config.language,
            },
        }

        data = _post_json(
            _base_url(self.config.region) + _TTS_PATH,
            self.config.api_key,
            payload,
            timeout=self.config.timeout,
        )

        audio = (data.get("output") or {}).get("audio") or {}
        url = audio.get("url")

        if not url:
            code = data.get("code", "")
            message = data.get("message", "")
            raise AlibabaTTSError(
                "API_ERROR",
                f"code={code} message={message}",
            )

        return self._download(url, self.config.timeout)

    def synthesize_stream(
        self,
        text: str,
        *,
        voice: str | None = None,
    ):
        """SSE 流式 TTS（预留接口）。当前返回生成器，chunk 为音频字节。"""

        raise NotImplementedError(
            "streaming TTS: 需处理 SSE 分帧，第一版用非流式 synthesize"
        )

    def streaming_available(self) -> bool:
        return False

    @staticmethod
    def _download(url: str, timeout: float) -> bytes:
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                return resp.read()
        except Exception as exc:
            raise AlibabaTTSError(
                "AUDIO_DOWNLOAD",
                f"failed to download audio: {exc}",
            ) from exc


# ---------------------------------------------------------
# Voice Clone（声音复刻）
# ---------------------------------------------------------


class AlibabaVoiceClone:
    """阿里云声音复刻（创建 Voice ID）。

    参考音频由用户在命令行显式执行上传/创建后才调用。
    不自动上传任何声音文件。
    """

    provider = "alibaba"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        workspace_id: str = "",
        region: str = "singapore",
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key or _read_api_key() or ""
        self.workspace_id = (
            workspace_id
            or os.getenv("XIAOQI_ALIBABA_WORKSPACE_ID", "")
        )
        self.region = region or os.getenv(
            "XIAOQI_ALIBABA_REGION",
            "singapore",
        )
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        """API Key + Workspace ID 都配置才视为已配置。"""

        return bool(self.api_key and self.workspace_id)

    def status(self) -> dict:
        return {
            "provider": self.provider,
            "configured": self.configured,
            "has_api_key": bool(self.api_key),
            "has_workspace_id": bool(self.workspace_id),
        }

    def _endpoint(self) -> str:
        if not self.workspace_id:
            raise AlibabaTTSError(
                "NO_WORKSPACE_ID",
                "XIAOQI_ALIBABA_WORKSPACE_ID 未配置",
            )
        return _clone_base_url(self.workspace_id, self.region)

    def create_voice(
        self,
        *,
        audio_wav: bytes,
        preferred_name: str,
        target_model: str = "qwen3-tts-vc-realtime-2026-01-15",
        text: str = "",
        language: str = "zh",
    ) -> str:
        """用参考音频创建 Voice ID（显式调用，绝不自动上传）。"""

        if not self.api_key:
            raise AlibabaTTSError(
                "NO_API_KEY",
                "XIAOQI_ALIBABA_API_KEY 未配置",
            )

        data_url = (
            "data:audio/wav;base64,"
            + base64.b64encode(audio_wav).decode("ascii")
        )

        payload = {
            "model": "qwen-voice-enrollment",
            "input": {
                "action": "create",
                "target_model": target_model,
                "preferred_name": preferred_name,
                "audio": {"data": data_url},
                "language": language,
            },
        }

        if text:
            payload["input"]["text"] = text

        data = _post_json(
            self._endpoint(),
            self.api_key,
            payload,
            timeout=self.timeout,
        )

        output = data.get("output") or {}
        voice_id = output.get("voice") or output.get("voice_id")

        if not voice_id:
            raise AlibabaTTSError(
                "CLONE_FAILED",
                "no voice id returned",
            )

        return voice_id

    def list_voices(self) -> list[dict]:
        payload = {
            "model": "qwen-voice-enrollment",
            "input": {"action": "list", "page_size": 20},
        }
        data = _post_json(
            self._endpoint(),
            self.api_key,
            payload,
            timeout=self.timeout,
        )
        output = data.get("output") or {}
        return output.get("voice_list") or []

    def delete_voice(self, voice: str) -> dict:
        payload = {
            "model": "qwen-voice-enrollment",
            "input": {"action": "delete", "voice": voice},
        }
        return _post_json(
            self._endpoint(),
            self.api_key,
            payload,
            timeout=self.timeout,
        )
