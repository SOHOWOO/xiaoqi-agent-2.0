"""小七 · 语音服务（WebSocket + 可选 STT）

接受 WebSocket 音频 -> STT -> 返回文本。
STT provider 优先级：faster-whisper > 占位 mock。
运行：python voice_server.py [port]
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import traceback

try:
    import faster_whisper

    _HAS_WHISPER = True
except ImportError:
    _HAS_WHISPER = False


_WHISPER_MODEL_SIZE = os.getenv("XIAOQI_STT_MODEL", "base")


class STTEngine:
    """语音识别引擎（faster-whisper 或 mock fallback）。"""

    def __init__(self) -> None:
        self._model = None

        if _HAS_WHISPER:
            try:
                self._model = faster_whisper.WhisperModel(
                    _WHISPER_MODEL_SIZE,
                    device="cpu",
                    compute_type="int8",
                )
                print(f"[voice] faster-whisper loaded ({_WHISPER_MODEL_SIZE})")
            except Exception as exc:
                print(f"[voice] faster-whisper load failed: {exc}")

    def transcribe(self, audio_data: bytes) -> str:
        """将音频字节数据转换为文本。"""

        if self._model is not None:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            try:
                segments, _ = self._model.transcribe(tmp_path, language="zh")
                texts = [s.text for s in segments]
                return " ".join(texts).strip()
            except Exception as exc:
                return f"[STT error: {exc}]"
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

        # Mock fallback（无 faster-whisper 时返回占位）
        return "[STT unavailable: install faster-whisper]"


async def handle_websocket(reader, writer):
    """处理 WebSocket 连接（标准库 RFC 6455 握手 + 帧）。"""

    import base64
    import hashlib
    import struct

    _WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    # 握手
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

    # 接收音频帧（二进制帧，opcode 2）
    audio_data = bytearray()

    while True:
        try:
            header = await asyncio.wait_for(reader.readexactly(2), timeout=30)
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
            payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))

        if opcode == 0x8:  # close
            break
        if opcode == 0x2:  # binary：一次话语，处理并响应
            audio_data.extend(payload)
            break
        if opcode == 0x1:  # text
            break

    if not audio_data:
        writer.write(b"\x88\x00")  # close frame
        await writer.drain()
        writer.close()
        return

    # STT
    text = stt_engine.transcribe(bytes(audio_data))

    response = json.dumps(
        {"text": text} if not text.startswith("[") else {"error": text}
    ).encode("utf-8")

    # 发送 text 帧
    payload = response
    header = bytearray()
    header.append(0x81)
    n = len(payload)
    if n < 126:
        header.append(n)
    elif n < 65536:
        header.append(126)
        header += struct.pack(">H", n)
    else:
        header.append(127)
        header += struct.pack(">Q", n)

    writer.write(bytes(header) + payload)
    await writer.drain()

    writer.write(b"\x88\x00")  # close frame
    await writer.drain()

    writer.close()


stt_engine = STTEngine()


async def main(port: int = 8769):
    server = await asyncio.start_server(handle_websocket, "127.0.0.1", port)
    print(f"[voice] WebSocket server on ws://127.0.0.1:{port}")
    print(f"[voice] STT: {'faster-whisper' if _HAS_WHISPER else 'MOCK (install faster-whisper)'}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8769
    asyncio.run(main(port))