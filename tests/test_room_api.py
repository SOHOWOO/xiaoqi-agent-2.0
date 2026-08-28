import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from web_runtime import WebRuntime


def _make_runtime(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return WebRuntime(
        simulation_minutes_per_real_second=60,
        load_canonical=False,
    )


def test_handle_action_maps_room_targets(tmp_path, monkeypatch):
    runtime = _make_runtime(tmp_path, monkeypatch)

    try:
        result = runtime.handle_action(
            {"action": "move_to", "target": "bed"}
        )

        assert result["accepted"] is True
        assert result["behavior"] == "resting"
        assert result["target"] == "bed"
        assert "hook" in result

        reading = runtime.handle_action(
            {"action": "move_to", "target": "desk"}
        )
        assert reading["behavior"] == "reading"

        unknown = runtime.handle_action(
            {"action": "move_to", "target": "roof"}
        )
        assert unknown["behavior"] == "idle"
    finally:
        runtime.close()


def test_handle_action_does_not_crash_runtime(tmp_path, monkeypatch):
    runtime = _make_runtime(tmp_path, monkeypatch)

    try:
        # 交互不影响核心状态
        before = runtime.life_loop.relationship_engine.state.as_dict()

        runtime.handle_action(
            {"action": "interact", "target": "xiaoqi"}
        )

        after = runtime.life_loop.relationship_engine.state.as_dict()
        assert before == after
    finally:
        runtime.close()


def test_schedule_data_has_today_slots(tmp_path, monkeypatch):
    runtime = _make_runtime(tmp_path, monkeypatch)

    try:
        schedule = runtime.schedule_data()

        assert "current_activity" in schedule
        assert "today" in schedule
        assert len(schedule["today"]) >= 1
        assert "name" in schedule["today"][0]
    finally:
        runtime.close()


def test_memory_data_returns_records(tmp_path, monkeypatch):
    runtime = _make_runtime(tmp_path, monkeypatch)

    try:
        runtime.handle_message("我喜欢喝咖啡")

        memories = runtime.memory_data()

        assert isinstance(memories, list)
        contents = [m["content"] for m in memories]
        assert any("咖啡" in c for c in contents)
    finally:
        runtime.close()


def test_settings_data(tmp_path, monkeypatch):
    runtime = _make_runtime(tmp_path, monkeypatch)

    try:
        data = runtime.settings_data()

        assert "simulation_minutes_per_real_second" in data
        assert data["allow_proactive"] is True
    finally:
        runtime.close()


def _server(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import web_server

    server = ThreadingHTTPServer(("127.0.0.1", 0), web_server.WebHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def _get(port, path):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}") as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_api_schedule_endpoint(tmp_path, monkeypatch):
    server, port = _server(tmp_path, monkeypatch)
    try:
        data = _get(port, "/api/schedule")
        assert "today" in data
    finally:
        server.shutdown(); server.server_close()


def test_api_memory_endpoint(tmp_path, monkeypatch):
    server, port = _server(tmp_path, monkeypatch)
    try:
        data = _get(port, "/api/memory")
        assert "memories" in data
    finally:
        server.shutdown(); server.server_close()


def test_api_settings_endpoint(tmp_path, monkeypatch):
    server, port = _server(tmp_path, monkeypatch)
    try:
        data = _get(port, "/api/settings")
        assert "allow_proactive" in data
    finally:
        server.shutdown(); server.server_close()


def test_api_action_endpoint(tmp_path, monkeypatch):
    server, port = _server(tmp_path, monkeypatch)
    try:
        import urllib.request

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/action",
            data=json.dumps({"action": "move_to", "target": "sofa"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        assert data["behavior"] == "relaxing"
    finally:
        server.shutdown(); server.server_close()
