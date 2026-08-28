"""小七 · VRM 校验器（Python）

解析 GLB 文件，检测是否为合法 VRM（1.0 / 0.x），
输出结构化结果供前端 avatar_vrm.js / /avatar-test 使用。

错误码：
  VRM_NOT_FOUND / VRM_LOAD_FAILED / VRM_INVALID /
  VRM_NO_HUMANOID / VRM_UNSUPPORTED_VERSION
"""

from __future__ import annotations

import json
import struct
from pathlib import Path

VRM1_MAGIC = "VRM"
VRM0_MAGIC = "VRM"
EXTENSIONS_KEY = "extensions"
VRMC_VRM = "VRMC_vrm"
VRM_OLD = "VRM"


def _read_glb(path: Path) -> tuple[dict, dict]:
    """读取 GLB，返回 (json_chunk, bin_data)。"""

    with open(path, "rb") as f:
        data = f.read()

    if len(data) < 12:
        raise ValueError("file too small for GLB")

    magic, version, length = struct.unpack("<III", data[:12])

    if magic != 0x46546C67:  # 'glTF'
        raise ValueError("not a GLB (bad magic)")

    if length != len(data):
        raise ValueError("GLB length mismatch")

    offset = 12
    json_chunk = None
    bin_data = b""

    while offset < len(data):
        chunk_len, chunk_type = struct.unpack(
            "<II", data[offset:offset + 8]
        )
        offset += 8
        payload = data[offset:offset + chunk_len]
        offset += chunk_len

        if chunk_type == 0x4E4F534A:  # JSON
            json_chunk = json.loads(payload.decode("utf-8"))
        elif chunk_type == 0x004E4942:  # BIN
            bin_data = payload

    if json_chunk is None:
        raise ValueError("GLB has no JSON chunk")

    return json_chunk, bin_data


def _vrm_extension(gltf: dict) -> tuple[str | None, dict]:
    """返回 (vrm_version, vrm_ext)。VRM 1.0 / 0.x 均支持。"""

    extensions = gltf.get("extensions", {}) or {}

    if VRMC_VRM in extensions:
        return "1.0", extensions[VRMC_VRM]

    if VRM_OLD in extensions:
        return "0.x", extensions[VRM_OLD]

    return None, {}


def validate_vrm(path: str | Path) -> dict:
    """校验 VRM 文件并返回结构化结果。"""

    path = Path(path)

    if not path.exists():
        return {"valid": False, "error": "VRM_NOT_FOUND"}

    try:
        gltf, _bin = _read_glb(path)
    except Exception as exc:
        return {
            "valid": False,
            "error": "VRM_LOAD_FAILED",
            "detail": str(exc),
        }

    version, vrm_ext = _vrm_extension(gltf)

    if version is None:
        return {"valid": False, "error": "VRM_INVALID"}

    if version not in ("1.0", "0.x"):
        return {"valid": False, "error": "VRM_UNSUPPORTED_VERSION"}

    result = {
        "valid": True,
        "version": version,
        "humanoid": bool(vrm_ext.get("humanoid")),
        "expression": bool(vrm_ext.get("expressions")),
        "lookAt": bool(vrm_ext.get("lookAt")),
        "springBone": bool(
            vrm_ext.get("secondaryAnimation")
            or vrm_ext.get("springBone")
        ),
        "meta": _meta_summary(vrm_ext),
    }

    if not result["humanoid"]:
        result["valid"] = False
        result["error"] = "VRM_NO_HUMANOID"

    return result


def _meta_summary(vrm_ext: dict) -> dict:
    meta = vrm_ext.get("meta", {}) or {}
    return {
        "name": meta.get("name", ""),
        "specVersion": meta.get("specVersion", ""),
    }


def check_available_model() -> dict:
    """检测项目标准模型位置。"""

    return validate_vrm("web/assets/avatar/xiaoqi.vrm")
