import threading
import urllib.request
from http.server import ThreadingHTTPServer


def _server(tmp_path, monkeypatch):
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

    return server, port


def test_api_voice_status_endpoint(tmp_path, monkeypatch):
    import json

    server, port = _server(tmp_path, monkeypatch)

    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/voice/status"
        ) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        # 真实状态：不写死
        assert "stt" in data
        assert "tts" in data
        assert "voice_profile" in data

        # 当前环境无 faster-whisper / cosyvoice -> 明确 unavailable
        assert data["stt"]["available"] is False
        assert data["stt"]["engine"] == "faster-whisper"
        assert data["tts"]["available"] is False
        assert data["tts"]["engine"] == "cosyvoice"
        assert data["voice_profile"] == "xiaoqi"
    finally:
        server.shutdown()
        server.server_close()


def test_voice_server_http_status(tmp_path, monkeypatch):
    """voice_server.py 的 HTTP /status 也应工作。"""

    import json

    import voice_server
    from http.server import ThreadingHTTPServer

    http_server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        voice_server.VoiceHandler,
    )
    port = http_server.server_address[1]

    thread = threading.Thread(
        target=http_server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/status"
        ) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        assert "stt" in data
        assert "tts" in data
    finally:
        http_server.shutdown()
        http_server.server_close()
