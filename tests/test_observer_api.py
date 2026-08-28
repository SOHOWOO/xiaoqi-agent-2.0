import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from web_runtime import WebRuntime


def _make_runtime(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return WebRuntime(
        simulation_minutes_per_real_second=60,
        load_canonical=False,
    )


def test_observer_state_sections(tmp_path, monkeypatch):
    runtime = _make_runtime(tmp_path, monkeypatch)

    try:
        state = runtime.observer_state()

        assert "emotion" in state
        assert "neurochemical" in state
        assert "relationship" in state
        assert "diaries" in state
        assert "memories" in state
        assert "schedule" in state

        assert "dominant" in state["emotion"]
        assert "current" in state["emotion"]
        assert "trust" in state["relationship"]
        assert "attachment" in state["relationship"]
    finally:
        runtime.close()


def test_observer_state_emotion_has_all_dims(tmp_path, monkeypatch):
    runtime = _make_runtime(tmp_path, monkeypatch)

    try:
        emotion = runtime.observer_state()["emotion"]["current"]

        for dim in ("happy", "lonely", "excited", "anxious", "angry", "calm"):
            assert dim in emotion
            assert 0.0 <= emotion[dim] <= 1.0
    finally:
        runtime.close()


def test_observer_state_memories_are_real(tmp_path, monkeypatch):
    runtime = _make_runtime(tmp_path, monkeypatch)

    try:
        # 触发一条互动记忆
        runtime.handle_message("我喜欢吃火锅")

        state = runtime.observer_state()

        contents = [m["content"] for m in state["memories"]]
        assert any("火锅" in c for c in contents)
    finally:
        runtime.close()


def test_observer_endpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    import web_server

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        web_server.WebHandler,
    )
    port = server.server_address[1]

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/observer"
        ) as response:
            data = json.loads(response.read().decode("utf-8"))

        assert "emotion" in data
        assert "relationship" in data
        assert "schedule" in data
    finally:
        server.shutdown()
        server.server_close()


def test_status_endpoint_still_works(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    import web_server

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        web_server.WebHandler,
    )
    port = server.server_address[1]

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/status"
        ) as response:
            data = json.loads(response.read().decode("utf-8"))

        assert "life_state" in data
        assert "memory_counts" in data
    finally:
        server.shutdown()
        server.server_close()
