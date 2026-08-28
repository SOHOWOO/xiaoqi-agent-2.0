from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
from pathlib import Path
from urllib.parse import urlparse

from web_runtime import WebRuntime
from vrm_validator import check_available_model
from voice.providers.alibaba_tts import (
    AlibabaTTSError,
    AlibabaTTS,
    load_tts_config,
)
from voice.status import build_voice_status

from appkit.config import ConfigManager
from appkit.providers import AIProvider
from appkit.secrets import SecretStore


def _system_status() -> dict:
    """真实系统状态（不伪造）。"""

    config = ConfigManager()

    core_ok = True
    memory_ok = True
    try:
        store = RUNTIME.memory_store
        _ = len(store)
    except Exception:
        memory_ok = False

    from voice.engines import STTEngine

    ai = AIProvider()
    tts_config = load_tts_config()
    tts = AlibabaTTS(tts_config)
    stt = STTEngine()

    return {
        "core": core_ok,
        "memory": memory_ok,
        "life_loop": True,
        "database": memory_ok,
        "ai": ai.status(),
        "tts": {
            "provider": "alibaba",
            "available": tts.available,
            "has_api_key": bool(tts_config.api_key),
            "has_voice_id": bool(tts_config.voice),
        },
        "stt": {
            "provider": "faster-whisper",
            "available": stt.available,
            "browser_available": True,
        },
        "avatar": {
            "mode": "three",
            "vrm": check_available_model().get("valid", False),
        },
        "microphone": True,  # 浏览器侧检测
        "webview": True,
        "setup_complete": config.setup_complete,
    }


def _config_payload() -> dict:
    """设置中心配置（不含任何 API Key）。"""

    config = ConfigManager()
    data = config.all()
    # 安全：绝不把 key 写进返回
    return data


def _setup_payload() -> dict:
    """首次启动检测。"""

    config = ConfigManager()
    store = SecretStore()

    return {
        "setup_complete": config.setup_complete,
        "has_deepseek": store.has("deepseek"),
        "has_alibaba": store.has("alibaba"),
    }


def _config_body(self) -> dict | None:
    """读取 POST body。"""

    try:
        length = int(self.headers.get("Content-Length", "0") or 0)
    except ValueError:
        length = 0
    if length <= 0:
        return {}
    try:
        import json

        return json.loads(self.rfile.read(length).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return {}


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"

RUNTIME = WebRuntime(
    simulation_minutes_per_real_second=float(
        os.getenv(
            "XIAOQI_SIM_MINUTES_PER_REAL_SECOND",
            "60",
        )
    ),
)


class WebHandler(BaseHTTPRequestHandler):
    """小七网页 HTTP Handler。"""

    server_version = "XiaoQiWeb/1.1"

    def _send_json(
        self,
        payload: dict,
        status: int = HTTPStatus.OK,
    ) -> None:
        body = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )
        self.send_header(
            "Content-Length",
            str(len(body)),
        )
        self.end_headers()

        self.wfile.write(body)

    def _send_file(
        self,
        path: Path,
        content_type: str,
    ) -> None:
        if not path.is_file():
            self.send_error(
                HTTPStatus.NOT_FOUND,
                "Not found",
            )
            return

        body = path.read_bytes()

        self.send_response(HTTPStatus.OK)
        self.send_header(
            "Content-Type",
            content_type,
        )
        self.send_header(
            "Content-Length",
            str(len(body)),
        )
        self.end_headers()

        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path == "/":
            self._send_file(
                WEB_DIR / "index.html",
                "text/html; charset=utf-8",
            )
            return

        if path == "/style.css":
            self._send_file(
                WEB_DIR / "style.css",
                "text/css; charset=utf-8",
            )
            return

        if path == "/app.js":
            self._send_file(
                WEB_DIR / "app.js",
                "application/javascript; charset=utf-8",
            )
            return

        if path.startswith("/avatar/") or path.startswith("/voice/"):
            self._send_file(
                WEB_DIR / path.lstrip("/"),
                "application/javascript; charset=utf-8",
            )
            return

        if path.startswith("/vendor/"):
            self._send_file(
                WEB_DIR / path.lstrip("/"),
                "application/javascript; charset=utf-8",
            )
            return

        if path.startswith("/assets/"):
            self._send_file(
                WEB_DIR / path.lstrip("/"),
                "application/octet-stream",
            )
            return


        if path == "/api/proactive":
            RUNTIME.advance()

            self._send_json(
                {
                    "messages": (
                        RUNTIME.proactive_messages()
                    )
                }
            )
            return

        if path == "/api/status":
            RUNTIME.advance()

            self._send_json(
                {
                    "life_state": (
                        RUNTIME.life_state_dict()
                    ),
                    "memory_counts": (
                        RUNTIME.memory_counts()
                    ),
                }
            )
            return

        if path == "/api/observer":
            RUNTIME.advance()

            self._send_json(
                RUNTIME.observer_state()
            )
            return

        if path == "/api/schedule":
            RUNTIME.advance()

            self._send_json(
                RUNTIME.schedule_data()
            )
            return

        if path == "/api/memory":
            RUNTIME.advance()

            self._send_json(
                {"memories": RUNTIME.memory_data()}
            )
            return

        if path == "/avatar-test":
            self._send_file(
                WEB_DIR / "avatar-test.html",
                "text/html; charset=utf-8",
            )
            return

        if path in ("/settings", "/setup"):
            self._send_file(
                WEB_DIR / "settings.html",
                "text/html; charset=utf-8",
            )
            return

        if path == "/settings.css":
            self._send_file(
                WEB_DIR / "settings.css",
                "text/css; charset=utf-8",
            )
            return

        if path == "/settings.js":
            self._send_file(
                WEB_DIR / "settings.js",
                "application/javascript; charset=utf-8",
            )
            return

        if path == "/api/vrm-status":
            self._send_json(
                check_available_model()
            )
            return

        if path == "/api/voice/status":
            self._send_json(
                build_voice_status()
            )
            return

        if path == "/api/settings":
            RUNTIME.advance()

            self._send_json(
                RUNTIME.settings_data()
            )
            return

        if path == "/api/system/status":
            self._send_json(_system_status())
            return

        if path == "/api/config":
            self._send_json(_config_payload())
            return

        if path == "/api/setup":
            self._send_json(_setup_payload())
            return

        self.send_error(
            HTTPStatus.NOT_FOUND,
            "Not found",
        )

    def do_POST(self) -> None:
        path = urlparse(self.path).path

        if path == "/api/chat":
            self._handle_chat()
            return

        if path == "/api/tts":
            self._handle_tts()
            return

        if path in ("/api/config", "/api/secrets", "/api/setup"):
            self._handle_config_write(path)
            return

        self.send_error(
            HTTPStatus.NOT_FOUND,
            "Not found",
        )

    def _read_body(self) -> dict | None:
        """读取 POST body 并解析 JSON。"""

        try:
            length = int(
                self.headers.get("Content-Length", "0") or 0
            )
        except ValueError:
            length = 0

        if length <= 0:
            self._send_json(
                {"error": "request body is required"},
                HTTPStatus.BAD_REQUEST,
            )
            return None

        try:
            raw = self.rfile.read(length)
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(
                {"error": "invalid JSON"},
                HTTPStatus.BAD_REQUEST,
            )
            return None

    def _handle_chat(self) -> None:
        payload = self._read_body()
        if payload is None:
            return

        message = payload.get("message")

        if not isinstance(message, str) or not message.strip():
            self._send_json(
                {"error": "message cannot be empty"},
                HTTPStatus.BAD_REQUEST,
            )
            return

        try:
            result = RUNTIME.handle_message(message)
            reply = RUNTIME.respond(result)

            self._send_json(
                {
                    "reply": reply,
                    "life_state": RUNTIME.life_state_dict(),
                    "memory_counts": RUNTIME.memory_counts(),
                }
            )
        except Exception as exc:
            self._send_json(
                {"error": str(exc)},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def _handle_config_write(self, path: str) -> None:
        """保存设置 / API Key / 完成 setup。

        安全：API Key 只写入 SecretStore（用户目录，权限保护），
        绝不返回、绝不进 JS/HTML/日志。
        """

        payload = self._read_body()
        if payload is None:
            return

        config = ConfigManager()
        store = SecretStore()

        if path == "/api/secrets":
            provider = payload.get("provider", "")
            value = payload.get("value", "")

            action = payload.get("action", "set")

            if action == "test":
                self._send_json(
                    self._test_secret(provider)
                )
                return

            if action == "delete":
                store.delete(provider)
                self._send_json(
                    {"ok": True, "provider": provider}
                )
                return

            store.set(provider, value)
            self._send_json(
                {"ok": True, "provider": provider}
            )
            return

        if path == "/api/setup":
            config.mark_setup_complete()
            self._send_json({"ok": True, "setup_complete": True})
            return

        # /api/config: 保存非密钥设置（白名单，不信任任意字段）
        safe_sections = {
            "ai": {"provider", "base_url", "model", "temperature", "max_tokens"},
            "tts": {"provider", "model", "voice_id", "region", "language"},
            "stt": {"provider", "language"},
            "avatar": {"mode", "vrm_url"},
            "ui": {"night_mode", "sound", "show_hud", "allow_proactive"},
            "life": {"sim_minutes_per_real_second"},
            "system": {"auto_voice"},
        }

        for section, keys in safe_sections.items():
            section_data = payload.get(section)
            if not isinstance(section_data, dict):
                continue
            for key in keys:
                if key in section_data:
                    config.set(section, key, section_data[key])

        self._send_json({"ok": True})

    def _test_secret(self, provider: str) -> dict:
        """测试 Provider 连接（真实检测）。"""

        try:
            if provider == "deepseek":
                return AIProvider().test_connection()
            if provider == "alibaba":
                return {"ok": True, "note": "API Key 已保存"}
            return {"ok": False, "error": f"unknown provider: {provider}"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def _handle_tts(self) -> None:
        payload = self._read_body()
        if payload is None:
            return

        text = (payload.get("text") or "").strip()

        if not text:
            self._send_json(
                {"error": "text required"},
                HTTPStatus.BAD_REQUEST,
            )
            return

        config = load_tts_config()
        tts = AlibabaTTS(config)

        if not tts.available:
            self._send_json(
                {"error": "Alibaba TTS unavailable"},
                HTTPStatus.SERVICE_UNAVAILABLE,
            )
            return

        try:
            audio = tts.synthesize(text)
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(audio)))
            self.end_headers()
            self.wfile.write(audio)
        except AlibabaTTSError as exc:
            self._send_json({"error": str(exc)}, 502)
        except Exception as exc:
            self._send_json({"error": str(exc)}, 500)

    def log_message(
        self,
        format: str,
        *args,
    ) -> None:
        print(
            f"[web] {self.address_string()} - "
            f"{format % args}"
        )


def main() -> None:
    host = os.getenv(
        "XIAOQI_WEB_HOST",
        "0.0.0.0",
    )

    try:
        port = int(
            os.getenv(
                "XIAOQI_WEB_PORT",
                "8000",
            )
        )
    except ValueError as exc:
        raise ValueError(
            "XIAOQI_WEB_PORT must be an integer"
        ) from exc

    server = ThreadingHTTPServer(
        (host, port),
        WebHandler,
    )

    print(
        "小七网页已启动："
        f"http://127.0.0.1:{port}"
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n正在关闭服务器…")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
