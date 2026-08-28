import json
import struct

import pytest
from pathlib import Path

from vrm_validator import (
    check_available_model,
    validate_vrm,
    _read_glb,
    _vrm_extension,
)


def test_missing_vrm_returns_not_found():
    result = validate_vrm("/nonexistent/xiaoqi.vrm")
    assert result["valid"] is False
    assert result["error"] == "VRM_NOT_FOUND"


def test_call_check_available_model_does_not_crash():
    result = check_available_model()
    # 标准模型不存在时 valid=False + error=VRM_NOT_FOUND
    assert "valid" in result
    assert result["valid"] is False
    assert result.get("error") == "VRM_NOT_FOUND"


def test_bad_glb_returns_load_failed(tmp_path):
    bad = tmp_path / "fake.vrm"
    bad.write_bytes(b"NOT A GLB")
    result = validate_vrm(str(bad))
    assert result["valid"] is False
    assert result["error"] == "VRM_LOAD_FAILED"


def test_glb_without_json_chunk(tmp_path):
    """GLB 文件头正确但无 JSON chunk。"""
    import struct
    glb = struct.pack("<III", 0x46546C67, 2, 20) + b"\x00" * 8
    bad = tmp_path / "nojson.vrm"
    bad.write_bytes(glb)
    result = validate_vrm(str(bad))
    assert result["valid"] is False
    assert result["error"] == "VRM_LOAD_FAILED"


def test_glb_without_vrm_extension(tmp_path):
    """合法 GLB 但无 VRM 扩展。"""
    fake_json = json.dumps({
        "asset": {"version": "2.0"},
        "extensions": {},
    }).encode("utf-8")
    pad = 4 - (len(fake_json) % 4)
    if pad != 4:
        fake_json += b" " * pad
    chunk_len = len(fake_json)
    glb = (
        struct.pack("<III", 0x46546C67, 2, 12 + 8 + chunk_len) +
        struct.pack("<II", chunk_len, 0x4E4F534A) +
        fake_json
    )
    bad = tmp_path / "novrm.vrm"
    bad.write_bytes(glb)
    result = validate_vrm(str(bad))
    assert result["valid"] is False
    assert result["error"] == "VRM_INVALID"