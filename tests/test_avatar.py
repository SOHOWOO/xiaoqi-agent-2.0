import base64
import hashlib
import json
import socket
from datetime import datetime

import pytest

from core.avatar import (
    AvatarAction,
    AvatarController,
    AvatarEmotion,
    AvatarEvent,
    AvatarVoice,
    CallbackAvatarBridge,
    WebSocketAvatarBridge,
    expression_for,
    map_action,
    map_emotion,
    motion_for,
)
from core.bus import EventBus


def _state_data(emotion="calm", time="2026-08-22T20:00:00+08:00"):
    return {
        "simulated_time": time,
        "dominant_emotion": emotion,
        "emotion": {
            "happy": 0.2,
            "lonely": 0.1,
            "excited": 0.1,
            "anxious": 0.1,
            "angry": 0.05,
            "calm": 0.6,
            emotion: 0.8,
        },
        "neurochemical": {},
        "relationship": {},
    }


# ---------------------------------------------------------
# protocol
# ---------------------------------------------------------


def test_avatar_event_to_dict():
    event = AvatarEvent(
        time=datetime(2026, 8, 22, 20, 0),
        emotion=AvatarEmotion("happy", 0.75),
        action=AvatarAction("smile"),
        voice=AvatarVoice(speaking=True),
    )

    data = event.to_dict()

    assert data["type"] == "avatar_state"
    assert data["time"] == "2026-08-22T20:00:00"
    assert data["emotion"] == {"name": "happy", "intensity": 0.75}
    assert data["action"] == {"name": "smile"}
    assert data["voice"] == {"speaking": True}


# ---------------------------------------------------------
# 映射
# ---------------------------------------------------------


def test_emotion_map_happy():
    assert expression_for("happy") == "smile"
    assert motion_for("happy") == "happy_idle"

    presentation = map_emotion("happy", 0.8)
    assert presentation["expression"] == "smile"
    assert presentation["eyes"] == "bright"
    assert presentation["intensity"] == 0.8


def test_emotion_map_lonely():
    assert expression_for("lonely") == "soft_sad"
    assert motion_for("lonely") == "quiet_idle"


def test_emotion_map_unknown_falls_back_calm():
    assert expression_for("unknown") == "neutral"
    assert motion_for("unknown") == "idle"


def test_action_map():
    assert map_action("smile") == "smile"
    assert map_action("wave") == "wave"
    assert map_action("comfort") == "comfort"
    assert map_action("chat") == "wave"
    assert map_action("play") == "excited"
    assert map_action("unknown") == "idle"


# ---------------------------------------------------------
# controller（通过 bus 解耦）
# ---------------------------------------------------------


def test_controller_subscribes_bus_and_maps_state():
    bus = EventBus()
    bridge = CallbackAvatarBridge()
    controller = AvatarController(bus, bridge=bridge)

    bus.publish("state_update", _state_data(emotion="happy"))

    assert controller.last_event is not None
    assert controller.last_event.emotion.name == "happy"
    assert controller.last_event.action.name == "idle"
    assert bridge.events[-1].emotion.name == "happy"


def test_controller_proactive_sets_action():
    bus = EventBus()
    bridge = CallbackAvatarBridge()
    controller = AvatarController(bus, bridge=bridge)

    bus.publish("proactive_triggered", {"action": "chat"})
    bus.publish("state_update", _state_data(emotion="happy"))

    assert controller.last_event.action.name == "wave"


def test_controller_speaking_flag():
    bus = EventBus()
    bridge = CallbackAvatarBridge()
    controller = AvatarController(bus, bridge=bridge)

    controller.set_speaking(True)
    bus.publish("state_update", _state_data())

    assert controller.last_event.voice.speaking is True


def test_controller_does_not_mutate_core():
    """Avatar 表达不应改变核心状态（隔离原则）。"""

    bus = EventBus()
    controller = AvatarController(bus)

    state = _state_data(emotion="angry")

    bus.publish("state_update", state)

    assert state["dominant_emotion"] == "angry"
    assert controller.last_event.emotion.name == "angry"


# ---------------------------------------------------------
# WebSocket bridge
# ---------------------------------------------------------


def _ws_handshake(host, port):
    client = socket.create_connection((host, port), timeout=5)

    key = base64.b64encode(b"testkey").decode("ascii")

    request = (
        "GET / HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n"
    )

    client.sendall(request.encode("ascii"))

    response = client.recv(4096).decode("latin-1")

    expected = base64.b64encode(
        hashlib.sha1(
            (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()
        ).digest()
    ).decode("ascii")

    assert "101 Switching Protocols" in response
    assert expected in response

    return client


def _read_ws_frame(client):
    b1, b2 = client.recv(2)

    length = b2 & 0x7F

    if length == 126:
        length = int.from_bytes(client.recv(2), "big")
    elif length == 127:
        length = int.from_bytes(client.recv(8), "big")

    payload = b""

    while len(payload) < length:
        payload += client.recv(length - len(payload))

    return payload.decode("utf-8")


def test_websocket_bridge_sends_event():
    bridge = WebSocketAvatarBridge("127.0.0.1", 0).start()

    try:
        client = _ws_handshake("127.0.0.1", bridge.port)

        event = AvatarEvent(
            emotion=AvatarEmotion("happy", 0.75),
            action=AvatarAction("smile"),
        )

        bridge.send(event)

        frame = _read_ws_frame(client)
        data = json.loads(frame)

        assert data["emotion"]["name"] == "happy"
        assert data["action"]["name"] == "smile"

        client.close()
    finally:
        bridge.stop()


def test_websocket_bridge_records_sent():
    bridge = WebSocketAvatarBridge("127.0.0.1", 0).start()

    try:
        bridge.send(AvatarEvent(emotion=AvatarEmotion("calm")))
        assert len(bridge.sent) == 1
        assert bridge.sent[0]["emotion"]["name"] == "calm"
    finally:
        bridge.stop()
