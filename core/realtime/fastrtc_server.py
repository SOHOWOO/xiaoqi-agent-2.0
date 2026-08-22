from __future__ import annotations

"""
FastRTC/WebRTC 接入层。

当前只负责把实时音频入口和 RealtimeAgentPipeline 解耦，
具体 STT/TTS/Avatar 实现通过依赖注入接入。
"""


class FastRTCServerAdapter:
    def __init__(self, pipeline):
        self.pipeline = pipeline

    async def handle_audio_frame(self, audio_frame):
        """处理来自 WebRTC 的音频帧。"""
        return await self._run_pipeline(audio_frame)

    async def _run_pipeline(self, audio):
        result = self.pipeline.process_audio(audio)
        return result



def create_fastrtc_server(pipeline):
    """创建 FastRTC 服务适配器入口。"""
    return FastRTCServerAdapter(pipeline)
