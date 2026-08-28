"""声音克隆检查 + /api/voice/status（alibaba）测试。"""

import json
import threading
import urllib.request
import wave
from http.server import ThreadingHTTPServer
from pathlib import Path

from voice.clone import check_reference_audio


def _make_wav(path: Path, *, rate=16000, channels=1, seconds=2):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = b"\x00\x00" * (rate * seconds)
        w.writeframes(frames)


def test_check_missing_reference(tmp_path):
    result = check_reference_audio(tmp_path / "nope.wav")
    assert result["valid"] is False
    assert result["error"] == "REFERENCE_NOT_FOUND"


def test_check_non_wav(tmp_path):
    f = tmp_path / "ref.mp3"
    f.write_bytes(b"ID3")
    result = check_reference_audio(f)
    assert result["valid"] is False
    assert result["error"] == "NOT_WAV"


def test_check_valid_wav(tmp_path):
    p = tmp_path / "reference.wav"
    _make_wav(p, rate=16000, channels=1, seconds=2)

    result = check_reference_audio(p)

    assert result["valid"] is True
    assert result["sample_rate"] == 16000
    assert result["channels"] == 1
    assert result["duration_sec"] == 2.0
    assert result["size_bytes"] > 0


def test_check_broken_wav(tmp_path):
    p = tmp_path / "broken.wav"
    p.write_bytes(b"RIFFxxxx not a real wav")

    result = check_reference_audio(p)

    assert result["valid"] is False
    assert result["error"] == "UNREADABLE"


# ---------------------------------------------------------
# /api/voice/status（alibaba provider）
# ---------------------------------------------------------


def _server(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import web_server

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        web_server.WebHandler,
    )
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def test_voice_status_alibaba_without_key(tmp_path, monkeypatch):
    """未配置 API Key -> alibaba 明确 unavailable / clone 未配置。"""

    monkeypatch.delenv("XIAOQI_ALIBABA_API_KEY", raising=False)
    monkeypatch.delenv("XIAOQI_ALIBABA_VOICE_ID", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)

    server, port = _server(tmp_path, monkeypatch)
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/voice/status"
        ) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        assert data["tts"]["provider"] == "alibaba"
        assert data["tts"]["available"] is False
        assert data["tts"]["has_api_key"] is False

        assert data["voice_clone"]["provider"] == "alibaba"
        assert data["voice_clone"]["configured"] is False

        assert data["voice_profile"] == "xiaoqi"
    finally:
        server.shutdown()
        server.server_close()
