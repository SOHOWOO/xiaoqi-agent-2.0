"""小七 · 真实 TTS 测试（python -m voice.test_tts "文本"）

真正调用阿里云 Qwen3-TTS 并保存音频到 tmp/voice_test/。
需要 .env 配置好 XIAOQI_ALIBABA_API_KEY + XIAOQI_ALIBABA_VOICE_ID。
"""

from __future__ import annotations

import sys
from pathlib import Path

from .providers.alibaba_tts import (
    AlibabaTTSError,
    AlibabaTTS,
    load_tts_config,
)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]

    text = args[0] if args else "小七今天下班回来啦。"

    config = load_tts_config()

    if not config.api_key:
        print("❌ 未配置 XIAOQI_ALIBABA_API_KEY")
        return 1

    if not config.voice:
        print("❌ 未配置 XIAOQI_ALIBABA_VOICE_ID（先创建小七声音）")
        return 1

    tts = AlibabaTTS(config)

    print(f"TTS provider: alibaba")
    print(f"model: {config.model}")
    print(f"region: {config.region}")
    print(f"text: {text}")

    try:
        audio = tts.synthesize(text)
    except AlibabaTTSError as exc:
        print(f"❌ TTS 失败: {exc}")
        return 1

    out_dir = Path("tmp/voice_test")
    out_dir.mkdir(parents=True, exist_ok=True)

    out = out_dir / "test_tts.wav"
    out.write_bytes(audio)

    print(f"✅ 音频已保存: {out}")
    print(f"   大小: {len(audio)} bytes")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
