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
import traceback
from http.server import ThreadingHTTPServer
from pathlib import Path

from appkit.config import ConfigManager
from appkit.secrets import SecretStore

_web_server: ThreadingHTTPServer | None = None
_voice_thread: threading.Thread | None = None
_ws_port: int = 0


def _bootstrap_log_path() -> Path:
    """启动日志路径（用户数据目录 logs/ 下的 bootstrap.log）。"""

    from appkit.paths import get_logs_dir

    return get_logs_dir() / "bootstrap.log"


def _log_bootstrap(message: str) -> None:
    """记录启动诊断信息（绝不包含 API Key / Authorization）。"""

    try:
        path = _bootstrap_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception:
        pass


def _dump_startup_info() -> None:
    """记录启动关键路径与环境（用于排查嵌入式解释器问题）。"""

    import json

    info = {
        "frozen": bool(getattr(sys, "frozen", False)),
        "executable": str(Path(sys.executable).resolve()),
        "meipass": str(getattr(sys, "_MEIPASS", "")),
        "cwd": str(Path.cwd()),
        "python_path": sys.path[:10],
        "api_keys_configured": {
            provider: "yes" if SecretStore().has(provider) else "no"
            for provider in ("deepseek", "alibaba", "openai")
        },
    }

    _log_bootstrap(
        "[startup] " + json.dumps(info, ensure_ascii=False)
    )


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


class JsApi:
    """前端 JS → Python 日志 bridge（诊断交互问题，不写 API Key）。"""

    def __init__(self) -> None:
        pass

    def log(self, msg: str) -> None:
        _log_bootstrap(f"[js] {msg}")

    def error(self, msg: str) -> None:
        _log_bootstrap(f"[js-error] {msg}")

    def apiChat(self, msg: str) -> str:
        """前端调用后端的真实聊天（绕过 JS fetch，验证 WebView→Python 链路）。"""
        try:
            return self._chat(msg)
        except Exception as exc:
            return f"[error] {exc}"

    def _chat(self, msg: str) -> str:
        from web_server import RUNTIME

        result = RUNTIME.handle_message(msg)
        return RUNTIME.respond(result)


def _open_window(http_port: int) -> None:
    """启动 PyWebView 窗口（加载小七前端）。"""

    try:
        import webview
    except ImportError:
        _log_bootstrap("[boot] pywebview not installed")
        print(
            "pywebview 未安装。请执行: pip install pywebview\n"
            f"开发模式可手动打开: http://127.0.0.1:{http_port}"
        )
        return

    _log_bootstrap("[create_window] starting")
    url = f"http://127.0.0.1:{http_port}"

    window = webview.create_window(
        title="小七",
        url=url,
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True,
        fullscreen=False,
        text_select=True,          # 允许文本选择（不阻止输入）
        confirm_close=True,
        js_api=JsApi(),
    )
    _log_bootstrap(
        f"[create_window] done url={url} "
        f"window={getattr(window, 'uid', '?')}"
    )

    _log_bootstrap("[webview_start] starting")
    webview.start()
    _log_bootstrap("[webview_return] returned")


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

    _dump_startup_info()

    try:
        _inject_secrets()

        http_port = _start_web_server()
        _start_voice_ws()

        _log_bootstrap(
            f"[ready] HTTP on 127.0.0.1:{http_port}"
        )

        print(f"小七启动: http://127.0.0.1:{http_port}")

        try:
            _open_window(http_port)
        finally:
            _cleanup()
    except Exception as exc:
        _log_bootstrap(
            "[fatal] " + traceback.format_exc()
        )
        _show_fatal_error(exc)


def _show_fatal_error(exc: Exception) -> None:
    """显示友好错误（不暴露 traceback）。"""

    log_path = _bootstrap_log_path()

    try:
        import webview
        import webview.window

        webview.create_window(
            title="小七",
            html=(
                "<div style='font-family:sans-serif;padding:40px;"
                "text-align:center'>"
                "<h2>小七启动失败</h2>"
                "<p>请查看日志：</p>"
                f"<p style='color:#888'>{log_path}</p>"
                f"<p style='color:#a00'>{exc}</p>"
                "</div>"
            ),
            width=520,
            height=360,
        )
        webview.start()
    except Exception:
        # 连错误窗口都打不开时，回退到控制台输出
        print(f"小七启动失败: {exc}")


if __name__ == "__main__":
    main()