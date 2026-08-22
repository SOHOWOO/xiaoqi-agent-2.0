from __future__ import annotations

import base64
import hashlib
import json
import socket
import struct
import threading
from typing import Set

from .protocol import AvatarEvent

_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class WebSocketAvatarBridge:
    """最小 WebSocket server（标准库，RFC 6455）。

    向 Soul-of-Waifu / Live2D 前端推送 AvatarEvent JSON。
    仅用于把 xiaoqi-agent 的 Avatar 事件送达独立运行的 Avatar 进程。
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 0,
    ) -> None:
        self.host = host
        self.port = port

        self._server: socket.socket | None = None
        self._clients: Set[socket.socket] = set()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._running = False

        # 记录已发送事件（测试 / 观测）
        self.sent: list[dict] = []

    # ---------------------------------------------------------
    # 生命周期
    # ---------------------------------------------------------

    def start(self) -> "WebSocketAvatarBridge":
        self._server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )
        self._server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )
        self._server.bind((self.host, self.port))
        self._server.listen(4)

        self.port = self._server.getsockname()[1]
        self._running = True

        self._thread = threading.Thread(
            target=self._accept_loop,
            daemon=True,
        )
        self._thread.start()

        return self

    def stop(self) -> None:
        self._running = False

        with self._lock:
            for client in list(self._clients):
                try:
                    client.close()
                except OSError:
                    pass
            self._clients.clear()

        if self._server is not None:
            try:
                self._server.close()
            except OSError:
                pass

    # ---------------------------------------------------------
    # WebSocket 实现
    # ---------------------------------------------------------

    def _accept_loop(self) -> None:
        assert self._server is not None

        while self._running:
            try:
                conn, _ = self._server.accept()
            except OSError:
                break

            threading.Thread(
                target=self._handle_client,
                args=(conn,),
                daemon=True,
            ).start()

    def _handle_client(self, conn: socket.socket) -> None:
        try:
            conn.settimeout(5)

            key = self._read_handshake_key(conn)

            if key is None:
                conn.close()
                return

            # 先登记再发握手，避免 send 竞态
            with self._lock:
                self._clients.add(conn)

            self._send_handshake(conn, key)

            # 保持连接（读取帧，处理 close/ping）
            while self._running:
                header = conn.recv(2)

                if not header or len(header) < 2:
                    break

                b1, b2 = header

                length = b2 & 0x7F
                mask = (b2 & 0x80) != 0

                if length == 126:
                    length = struct.unpack(
                        ">H",
                        conn.recv(2),
                    )[0]
                elif length == 127:
                    length = struct.unpack(
                        ">Q",
                        conn.recv(8),
                    )[0]

                mask_key = b""
                if mask:
                    mask_key = conn.recv(4)

                payload = b""
                remaining = length

                while remaining > 0:
                    chunk = conn.recv(remaining)
                    if not chunk:
                        break
                    payload += chunk
                    remaining -= len(chunk)

                if mask:
                    payload = bytes(
                        b ^ mask_key[i % 4]
                        for i, b in enumerate(payload)
                    )

                opcode = b1 & 0x0F

                if opcode == 0x8:  # close
                    break
        except (OSError, ValueError):
            pass
        finally:
            with self._lock:
                self._clients.discard(conn)
            try:
                conn.close()
            except OSError:
                pass

    @staticmethod
    def _read_handshake_key(
        conn: socket.socket,
    ) -> str | None:
        data = b""

        while b"\r\n\r\n" not in data:
            chunk = conn.recv(4096)

            if not chunk:
                return None

            data += chunk

            if len(data) > 65536:
                return None

        request = data.decode("latin-1")

        for line in request.split("\r\n"):
            if line.lower().startswith(
                "sec-websocket-key:"
            ):
                return line.split(":", 1)[1].strip()

        return None

    def _send_handshake(
        self,
        conn: socket.socket,
        key: str,
    ) -> None:
        accept = base64.b64encode(
            hashlib.sha1(
                (key + _WS_GUID).encode("utf-8")
            ).digest()
        ).decode("ascii")

        conn.sendall(
            (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n"
                "\r\n"
            ).encode("ascii")
        )

    # ---------------------------------------------------------
    # 发送
    # ---------------------------------------------------------

    def send(
        self,
        event: AvatarEvent,
    ) -> None:
        """向所有已连接的 Avatar 客户端推送事件。"""

        payload = json.dumps(
            event.to_dict(),
            ensure_ascii=False,
        ).encode("utf-8")

        frame = self._encode_text_frame(payload)

        with self._lock:
            for client in list(self._clients):
                try:
                    client.sendall(frame)
                except OSError:
                    pass

        self.sent.append(event.to_dict())

    @staticmethod
    def _encode_text_frame(
        payload: bytes,
    ) -> bytes:
        # server -> client 不需要掩码
        header = bytearray()
        header.append(0x81)  # FIN + text

        n = len(payload)

        if n < 126:
            header.append(n)
        elif n < 65536:
            header.append(126)
            header += struct.pack(">H", n)
        else:
            header.append(127)
            header += struct.pack(">Q", n)

        return bytes(header) + payload
