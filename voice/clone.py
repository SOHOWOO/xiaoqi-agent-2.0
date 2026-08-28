"""小七 · 声音克隆工具（python -m voice.clone）

在真正上传前检查参考音频格式；显式执行创建 Voice ID。

用法：
  python -m voice.clone check                 # 检查 reference.wav
  python -m voice.clone create [name]         # 创建 Voice ID（需 .env 配置好）
  python -m voice.clone list                  # 查询音色列表

绝不自动上传任何声音文件；必须显式执行 create。
"""

from __future__ import annotations

import os
import sys
import wave
from pathlib import Path

from .profile import DEFAULT_PROFILE_DIR

DEFAULT_REFERENCE = (
    Path(__file__).parent / "profiles" / "xiaoqi" / "reference.wav"
)


def check_reference_audio(
    path: str | Path | None = None,
) -> dict:
    """检查参考音频：存在 / wav 格式 / 可读取 / 时长 / 采样率 / 声道 / 大小。"""

    ref = Path(path) if path else DEFAULT_REFERENCE

    if not ref.is_file():
        return {
            "valid": False,
            "error": "REFERENCE_NOT_FOUND",
            "path": str(ref),
        }

    if ref.suffix.lower() not in (".wav", ".wave"):
        return {
            "valid": False,
            "error": "NOT_WAV",
            "path": str(ref),
        }

    try:
        with wave.open(str(ref), "rb") as w:
            params = w.getparams()
            frames = w.getnframes()
            rate = w.getframerate()
            channels = w.getnchannels()
            duration = frames / rate if rate else 0.0
            sample_width = w.getsampwidth()
    except (wave.Error, EOFError, OSError) as exc:
        return {
            "valid": False,
            "error": "UNREADABLE",
            "detail": str(exc),
            "path": str(ref),
        }

    size = ref.stat().st_size

    issues = []
    if rate < 24000:
        issues.append("采样率需 ≥ 24 kHz")
    if channels != 1:
        issues.append("需单声道（Qwen-TTS 复刻要求单声道）")
    if sample_width != 2:
        issues.append("需 16bit（sample_width=2）")
    if duration <= 0:
        issues.append("音频时长为 0")
    if duration > 60:
        issues.append("时长需 ≤ 60 秒")
    if size <= 0:
        issues.append("文件为空")
    if size > 10 * 1024 * 1024:
        issues.append("文件大小需 ≤ 10 MB")

    return {
        "valid": not issues,
        "issues": issues,
        "path": str(ref),
        "format": "wav",
        "duration_sec": round(duration, 2),
        "sample_rate": rate,
        "channels": channels,
        "sample_width": sample_width,
        "size_bytes": size,
    }


def _print_check(result: dict) -> None:
    print("声音样本检查:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    if result.get("valid"):
        print("✅ 参考音频可用")
    else:
        print(f"❌ 参考音频不可用: {result.get('error')}")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    action = args[0] if args else "check"

    if action == "check":
        _print_check(check_reference_audio())
        return 0 if check_reference_audio()["valid"] else 1

    if action in ("create", "list"):
        from .providers.alibaba_tts import (
            AlibabaTTSError,
            AlibabaVoiceClone,
        )

        clone = AlibabaVoiceClone()

        if not clone.configured:
            print(
                "❌ 未配置：需设置 XIAOQI_ALIBABA_API_KEY"
            )
            return 1

        if action == "list":
            try:
                voices = clone.list_voices()
                print("音色列表:")
                for v in voices:
                    print(f"  - {v}")
                return 0
            except AlibabaTTSError as exc:
                print(f"❌ {exc}")
                return 1

        # create
        name = args[1] if len(args) > 1 else "xiaoqi"

        result = check_reference_audio()

        if not result["valid"]:
            _print_check(result)
            print("❌ 请先提供合法的 reference.wav")
            return 1

        with open(result["path"], "rb") as f:
            audio = f.read()

        print(f"正在创建 Voice ID（name={name}）…")
        print("⚠️ 这将上传参考音频到阿里云，请确认已授权。")

        try:
            voice_id = clone.create_voice(
                audio_wav=audio,
                preferred_name=name,
            )
        except AlibabaTTSError as exc:
            print(f"❌ 创建失败: {exc}")
            return 1

        print(f"✅ Voice ID 创建成功: {voice_id}")
        print("请把它填入 .env 的 XIAOQI_ALIBABA_VOICE_ID")
        return 0

    print(f"未知命令: {action}")
    print("用法: python -m voice.clone [check|create|list]")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
