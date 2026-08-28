"""xiaoqi_app launcher 测试：服务合并 / 随机端口 / 清理。"""

import json
import threading
import time
import urllib.request

import pytest

import xiaoqi_app


def test_web_server_starts_on_random_port():
    port = xiaoqi_app._start_web_server()

    assert port > 0

    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/system/status",
            timeout=10,
        ) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        assert "core" in data
    finally:
        xiaoqi_app._cleanup()


def test_voice_ws_starts():
    port = xiaoqi_app._start_voice_ws()

    assert port > 0

    import socket

    s = socket.create_connection(("127.0.0.1", port), timeout=5)
    s.close()

    xiaoqi_app._cleanup()


def test_cleanup_stops_web_server():
    port = xiaoqi_app._start_web_server()

    assert xiaoqi_app._web_server is not None

    xiaoqi_app._cleanup()

    assert xiaoqi_app._web_server is None

    # 端口应已关闭
    import socket

    with pytest.raises(OSError):
        s = socket.create_connection(("127.0.0.1", port), timeout=2)
        s.close()
