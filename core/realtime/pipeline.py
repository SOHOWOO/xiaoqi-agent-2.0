from __future__ import annotations


class RealtimeAgentPipeline:
    """
    小七实时交互流水线。
    """


    def __init__(
        self,
        speech_recognizer,
        chat_service,
        tts_engine,
        avatar_engine,
    ):
        self.speech_recognizer = speech_recognizer
        self.chat_service = chat_service
        self.tts_engine = tts_engine
        self.avatar_engine = avatar_engine



    def process_audio(
        self,
        audio,
    ):

        # 1. Whisper识别
        transcript = (
            self.speech_recognizer
            .transcribe(audio)
        )


        # 2. Chat Core
        reply = (
            self.chat_service
            .handle_and_respond(
                transcript.text
            )
        )


        # 3. TTS
        audio_result = (
            self.tts_engine
            .speak(reply)
        )


        # 4. Avatar嘴型
        avatar_event = (
            self.avatar_engine
            .play_voice(
                audio_result.audio_path
            )
        )


        return avatar_event
