from __future__ import annotations

import json
import os
from datetime import timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from core.chat import ChatService, OpenAICompatibleProvider
from core.life_loop import LifeLoop
from core.memory import MemoryContextBuilder, MemoryRetriever


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"


def build_chat_service() -> ChatService:
    """创建网页使用的 ChatService。"""

    loop = LifeLoop(
        start_time=__import__(
            "core.time_engine",
            fromlist=["make_aware"],
        ).make_aware(2026, 8, 20, 9, 0),
        seed=42,
    )

    retriever = MemoryRetriever(loop.memory_store)
    context_builder = MemoryContextBuilder(retriever)

    provider = OpenAICompatibleProvider()

    return ChatService(
        life_loop=loop,
        memory_context_builder=context_builder,
        response_provider=provider,
    )


CHAT_SERVICE = build_chat_service()


def life_state_dict() -> dict:
    state = CHAT_SERVICE.life_loop.life_state

    return {
        "current_time": str(state.current_time),
        "current_activity": state.current_activity,
        "energy": state.energy,
        "fatigue": state.fatigue,
    }


class WebHandler(BaseHTTPRequestHandler):
    """小七网页聊天 HTTP Handler。"""

    server_version = "XiaoQiWeb/1.0"

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

        if path == "/api/status":
            self._send_json(
                {
                    "life_state": life_state_dict(),
                }
            )
            return

        self.send_error(
            HTTPStatus.NOT_FOUND,
            "Not found",
        )

    def do_POST(self) -> None:
        path = urlparse(self.path).path

        if path != "/api/chat":
            self.send_error(
                HTTPStatus.NOT_FOUND,
                "Not found",
            )
            return

        content_length = int(
            self.headers.get("Content-Length", "0")
        )

        if content_length <= 0:
            self._send_json(
                {"error": "request body is required"},
                HTTPStatus.BAD_REQUEST,
            )
            return

        try:
            raw = self.rfile.read(content_length)
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(
                {"error": "invalid JSON"},
                HTTPStatus.BAD_REQUEST,
            )
            return

        message = payload.get("message")

        if not isinstance(message, str) or not message.strip():
            self._send_json(
                {"error": "message cannot be empty"},
                HTTPStatus.BAD_REQUEST,
            )
            return

        try:
            result = CHAT_SERVICE.handle_message(message)
            reply = CHAT_SERVICE.respond(result)

            self._send_json(
                {
                    "reply": reply,
                    "life_state": life_state_dict(),
                    "memory_count": len(
                        CHAT_SERVICE.life_loop.memory_store
                    ),
                }
            )
        except Exception as exc:
            self._send_json(
                {"error": str(exc)},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

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
        f"小七网页已启动："
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
