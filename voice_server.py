"""小七 · 语音服务

- WebSocket /stt：音频 -> faster-whisper STT -> 文本
- HTTP GET  /status：真实语音状态（同主服务器 /api/voice/status）
- HTTP POST /tts：CosyVoice 文本 -> wav 音频（可选）

STT：faster-whisper（未安装 -> unavailable）
TTS：CosyVoice（未安装 -> unavailable）

运行：python voice_server.py [port]   # 默认 8769
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import struct
import sys
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from voice.engines import CosyVoiceTTS, STTEngine
from voice.status import build_voice_status


class STTService:
    def __init__(self) -> None:
        self.stt = STTEngine()
        self.tts = CosyVoiceTTS()


service = STTService()


# ---------------------------------------------------------
# WebSocket STT
# ---------------------------------------------------------

async def handle_websocket(reader, writer):
    """处理 WebSocket 连接（标准库 RFC 6455 握手 + 帧）。"""

    import base64
    import hashlib

    _WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    data = b""
    while b"\r\n\r\n" not in data:
        data += await reader.read(4096)
    request = data.decode("latin-1")

    key = None
    for line in request.split("\r\n"):
        if line.lower().startswith("sec-websocket-key:"):
            key = line.split(":", 1)[1].strip()
            break
    if not key:
        writer.close()
        return

    accept = base64.b64encode(
        hashlib.sha1((key + _WS_GUID).encode("utf-8")).digest()
    ).decode("ascii")

    writer.write(
        (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n"
            "\r\n"
        ).encode("ascii")
    )
    await writer.drain()

    audio_data = bytearray()

    while True:
        try:
            header = await asyncio.wait_for(
                reader.readexactly(2),
                timeout=30,
            )
        except (asyncio.TimeoutError, asyncio.IncompleteReadError):
            break

        b1, b2 = header
        opcode = b1 & 0x0F
        mask = (b2 & 0x80) != 0
        length = b2 & 0x7F

        if length == 126:
            length = struct.unpack(">H", await reader.readexactly(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", await reader.readexactly(8))[0]

        mask_key = b""
        if mask:
            mask_key = await reader.readexactly(4)

        payload = b""
        remaining = length
        while remaining > 0:
            chunk = await reader.readexactly(remaining)
            payload += chunk
            remaining -= len(chunk)

        if mask:
            payload = bytes(
                b ^ mask_key[i % 4] for i, b in enumerate(payload)
            )

        if opcode == 0x8:  # close
            break
        if opcode == 0x2:  # binary：一次话语
            audio_data.extend(payload)
            break
        if opcode == 0x1:
            break

    if not audio_data:
        await _ws_send_text(writer, {"error": "no audio"})
        writer.close()
        return

    text = service.stt.transcribe(bytes(audio_data))

    if text.startswith("["):
        await _ws_send_text(writer, {"error": text})
    else:
        await _ws_send_text(writer, {"text": text})

    writer.write(b"\x88\x00")
    await writer.drain()
    writer.close()


async def _ws_send_text(writer, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    header = bytearray()
    header.append(0x81)
    n = len(body)
    if n < 126:
        header.append(n)
    elif n < 65536:
        header.append(126)
        header += struct.pack(">H", n)
    else:
        header.append(127)
        header += struct.pack(">Q", n)
    writer.write(bytes(header) + body)
    await writer.drain()


# ---------------------------------------------------------
# HTTP（/status /tts）
# ---------------------------------------------------------

class VoiceHandler(BaseHTTPRequestHandler):
    server_version = "XiaoQiVoice/1.1"

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_audio(self, data: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path.startswith("/status"):
            self._send_json(build_voice_status())
            return
        self._send_json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        if not self.path.startswith("/tts"):
            self._send_json({"error": "not found"}, 404)
            return

        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            self._send_json({"error": "empty body"}, 400)
            return

        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json({"error": "invalid JSON"}, 400)
            return

        text = (payload.get("text") or "").strip()

        if not text:
            self._send_json({"error": "text required"}, 400)
            return

        if not service.tts.available:
            self._send_json({"error": "CosyVoice unavailable"}, 503)
            return

        try:
            audio = service.tts.synthesize(text)
            self._send_audio(audio, "audio/wav")
        except Exception as exc:
            self._send_json({"error": str(exc)}, 500)

    def log_message(self, fmt, *args):
        print(f"[voice-http] {self.address_string()} - {fmt % args}")


# ---------------------------------------------------------
# 启动
# ---------------------------------------------------------

async def run_websocket(port: int) -> None:
    server = await asyncio.start_server(
        handle_websocket,
        "127.0.0.1",
        port,
    )
    print(f"[voice] WebSocket STT on ws://127.0.0.1:{port}")
    async with server:
        await server.serve_forever()


def run_http(http_port: int) -> threading.Thread:
    http_server = ThreadingHTTPServer(
        ("127.0.0.1", http_port),
        VoiceHandler,
    )

    def _serve() -> None:
        http_server.serve_forever()

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()

    print(f"[voice] HTTP on http://127.0.0.1:{http_port}"
          f" (GET /status, POST /tts)")
    return thread


def main(ws_port: int = 8769, http_port: int = 8779) -> None:
    print(f"[voice] STT: {service.stt.status().to_dict()}")
    print(f"[voice] TTS: {service.tts.status().to_dict()}")

    run_http(http_port)

    asyncio.run(run_websocket(ws_port))


if __name__ == "__main__":
    _ws_port = int(sys.argv[1]) if len(sys.argv) > 1 else 8769
    _http_port = int(sys.argv[2]) if len(sys.argv) > 2 else 8779
    main(_ws_port, _http_port)
