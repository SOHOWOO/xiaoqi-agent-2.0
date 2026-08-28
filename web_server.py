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
from voice.status import build_voice_status


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

        try:
            content_length = int(
                self.headers.get(
                    "Content-Length",
                    "0",
                )
            )
        except ValueError:
            content_length = 0

        if content_length <= 0:
            self._send_json(
                {
                    "error": (
                        "request body is required"
                    )
                },
                HTTPStatus.BAD_REQUEST,
            )
            return

        try:
            raw = self.rfile.read(
                content_length
            )
            payload = json.loads(
                raw.decode("utf-8")
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            self._send_json(
                {"error": "invalid JSON"},
                HTTPStatus.BAD_REQUEST,
            )
            return

        message = payload.get("message")

        if (
            not isinstance(message, str)
            or not message.strip()
        ):
            self._send_json(
                {"error": "message cannot be empty"},
                HTTPStatus.BAD_REQUEST,
            )
            return

        try:
            result = RUNTIME.handle_message(
                message
            )

            reply = RUNTIME.respond(result)

            self._send_json(
                {
                    "reply": reply,
                    "life_state": (
                        RUNTIME.life_state_dict()
                    ),
                    "memory_counts": (
                        RUNTIME.memory_counts()
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
