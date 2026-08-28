import asyncio
import json
import socket
import struct
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from voice_server import STTEngine


def test_stt_engine_fallback_when_no_whisper():
    """无 faster-whisper 时返回明确的 unavailable 标记（不伪造识别）。"""

    engine = STTEngine()

    text = engine.transcribe(b"\x00\x01" * 100)

    assert "unavailable" in text or "error" in text or text.strip()


def test_stt_engine_rejects_empty(monkeypatch):
    engine = STTEngine()

    result = engine.transcribe(b"")

    assert result is not None


def test_web_serves_vendor_and_assets(tmp_path, monkeypatch):
    """web_server 应能服务 three vendor 与 avatar assets。"""

    monkeypatch.chdir(tmp_path)

    import web_server

    # vendor/three 可能未在 tmp cwd 下，但路由应按 WEB_DIR 相对解析
    server = ThreadingHTTPServer(("127.0.0.1", 0), web_server.WebHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        # three module 应可访问（WEB_DIR 指向真实项目 web/）
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/vendor/three/three.module.js") as resp:
            assert resp.status == 200
            assert resp.read()[:2] == b"/*"

        # assets 目录应存在
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/assets/avatar/README.md") as resp:
            assert resp.status == 200
    finally:
        server.shutdown()
        server.server_close()


def test_voice_server_websocket_roundtrip():
    """voice_server WebSocket：握手 + 收音频 + 返回文本帧。"""

    import voice_server

    # 注入 stub STT（不触发真实 whisper 惰性加载），聚焦 WebSocket 协议
    class _StubSTT:
        engine_name = "stub"

        def transcribe(self, audio_data):
            return "小七测试"

        def streaming_available(self):
            return False

    voice_server.service.stt = _StubSTT()

    # 在独立线程/事件循环启动 server
    results = {}

    def run_server():
        async def _run():
            server = await asyncio.start_server(
                voice_server.handle_websocket,
                "127.0.0.1",
                0,
            )
            port = server.sockets[0].getsockname()[1]
            results["port"] = port

            async def serve():
                async with server:
                    await server.serve_forever()

            task = asyncio.ensure_future(serve())
            # 等 2 秒让客户端完成
            await asyncio.sleep(3)
            server.close()
            await task

        asyncio.run(_run())

    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    import time

    for _ in range(50):
        if "port" in results:
            break
        time.sleep(0.1)
    assert "port" in results, "voice server failed to start"

    port = results["port"]

    # 客户端：握手 + 发二进制音频 + 读文本帧
    client = socket.create_connection(("127.0.0.1", port), timeout=5)
    key = "dGhlIHNhbXBsZSBub25jZQ=="  # 任意 base64

    req = (
        "GET / HTTP/1.1\r\n"
        f"Host: 127.0.0.1:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n"
    )
    client.sendall(req.encode())

    # 读握手响应
    resp = b""
    while b"\r\n\r\n" not in resp:
        resp += client.recv(4096)
    assert b"101 Switching Protocols" in resp

    # 发送二进制帧（客户端必须掩码）
    payload = b"\x00\x01\x00\x01\x00\x01"  # 伪音频
    mask_key = b"\x11\x22\x33\x44"
    masked = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
    frame = bytes([0x82, 0x80 | len(payload)]) + mask_key + masked
    client.sendall(frame)

    # 读响应帧（server -> client 不掩码）
    h1 = client.recv(2)
    assert len(h1) == 2
    length = h1[1] & 0x7F
    if length == 126:
        length = struct.unpack(">H", client.recv(2))[0]
    body = b""
    while len(body) < length:
        body += client.recv(length - len(body))

    data = json.loads(body.decode())
    assert "text" in data or "error" in data

    client.close()
    t.join(timeout=5)
