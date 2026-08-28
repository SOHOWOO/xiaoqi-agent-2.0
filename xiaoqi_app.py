"""小七 · Windows 桌面应用入口

统一启动：
1. 合并 HTTP + WebSocket 语音服务（单进程，随机端口）
2. 从 secrets 注入 API Key 到环境变量
3. 启动 PyWebView 窗口（加载 localhost 随机端口）
4. 关闭时自动清理所有后台服务

构建后：
  双击「小七.exe」→ 独立窗口 → 直接进入小七的房间
"""

from __future__ import annotations

import asyncio
import os
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from appkit.config import ConfigManager
from appkit.secrets import SecretStore

_web_server: ThreadingHTTPServer | None = None
_voice_thread: threading.Thread | None = None
_ws_port: int = 0


def _inject_secrets() -> None:
    """从 SecretStore 读取 API Key 写入环境变量（供 web_server 等模块使用）。"""

    store = SecretStore()
    for env, value in store.env_overrides().items():
        if value and not os.environ.get(env):
            os.environ[env] = value


def _start_web_server() -> int:
    """启动 HTTP 服务器（随机端口），返回实际端口号。"""

    global _web_server

    import web_server

    _web_server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        web_server.WebHandler,
    )
    port = _web_server.server_address[1]

    thread = threading.Thread(
        target=_web_server.serve_forever,
        daemon=True,
    )
    thread.start()

    return port


def _start_voice_ws() -> int:
    """启动语音 WebSocket 服务（随机端口），返回端口号。

    桌面端 TTS 由 web_server 的 /api/tts 处理（Alibaba），
    状态由 /api/voice/status 处理；本进程只需 WebSocket STT。
    """

    import voice_server

    async def _run() -> None:
        global _ws_port

        server = await asyncio.start_server(
            voice_server.handle_websocket,
            "127.0.0.1",
            0,
        )
        _ws_port = server.sockets[0].getsockname()[1]

        async with server:
            await server.serve_forever()

    def _start_loop() -> None:
        asyncio.run(_run())

    global _voice_thread
    _voice_thread = threading.Thread(target=_start_loop, daemon=True)
    _voice_thread.start()

    import time

    for _ in range(50):
        if _ws_port:
            return _ws_port
        time.sleep(0.1)

    return 0


def _open_window(http_port: int) -> None:
    """启动 PyWebView 窗口（加载小七前端）。"""

    try:
        import webview
    except ImportError:
        print(
            "pywebview 未安装。请执行: pip install pywebview\n"
            f"开发模式可手动打开: http://127.0.0.1:{http_port}"
        )
        return

    url = f"http://127.0.0.1:{http_port}"

    webview.create_window(
        title="小七",
        url=url,
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True,
        fullscreen=False,
        text_select=False,
        confirm_close=True,
    )


def _cleanup() -> None:
    """关闭所有后台服务。"""

    global _web_server

    if _web_server is not None:
        try:
            _web_server.shutdown()
            _web_server.server_close()
        except Exception:
            pass
        _web_server = None


def main() -> None:
    """启动小七桌面应用。"""

    _inject_secrets()

    http_port = _start_web_server()
    _start_voice_ws()

    print(f"小七启动: http://127.0.0.1:{http_port}")

    try:
        _open_window(http_port)
    finally:
        _cleanup()


if __name__ == "__main__":
    main()