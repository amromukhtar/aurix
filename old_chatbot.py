#!/usr/bin/env python3
"""
Voice Chatbot (USB Mic + Bluetooth/Analog Speaker) — Whisper + Piper TTS + Ollama + PipeWire

Replaces Kokoro TTS with Piper (CLI). Piper produces WAV files which are played via PipeWire (pw-play).
This keeps the rest of your original logic intact (VAD, Whisper transcription, Ollama LLM).

Run:
  python3 chatbot.py
  python3 chatbot.py --mic-target <source-id-or-name>
  MIC_TARGET=<source-id-or-name> python3 chatbot.py
  python3 chatbot.py --test
"""

import sys
import signal
import time
import sounddevice as sd
import struct
import queue
import config
import threading

from rag.query_data import query_rag
from groq_model import (
    generate_response,
    generate_rag_response,
    extract_emotion_and_clean_text,
)

# from llm import init_ollama, generate_response
from stt import (
    init_stt,
    transcribe_audio,
    record_with_vad,
    save_wav,
    record_fixed_seconds,
)
from tts import PiperTTS, TTS_MODEL_EN, TEMP_WAV, speak_text
from face import render_face
from arduino import MotorController
from wake_word import porcupine, sample_rate, frame_length
from camera import ObjectDetector


AWAKE_TIME = 90

# ===== Init =====
event_queue = queue.Queue()
control = {"thread": False, "start_time": time.time()}


def init_models():
    print("🚀 Starting Voice Chatbot...")
    print("📦 Loading models (this may take a moment the first time)...")

    whisper = init_stt()
    tts = PiperTTS(TTS_MODEL_EN)
    detector = ObjectDetector()
    # init_ollama()

    print("✅ All models loaded successfully!\n")

    return whisper, tts, detector


# ===== Main =====
def main():

    def shutdown_handler(sig, frame):
        print("\n\n👋 Shutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    config.TIME_TO_SLEEP = time.time()
    whisper_model, tts_pipeline, detector = init_models()
    motor_controller = MotorController("/dev/ttyUSB0", 9600)

    print("\n" + "=" * 50)
    print("🤖 AURIX IS READY!")
    print("=" * 50)

    def wakeUp():
        config.TIME_TO_SLEEP = time.time()

        a = detector.detect()
        print("DETECTED\n", a)

        speak_text(tts_pipeline, "Yes ?")
        audio_data, rate, ch = record_with_vad()

        if audio_data:
            save_wav(audio_data, TEMP_WAV, sample_rate=rate, channels=ch)
            user_text = transcribe_audio(whisper_model, TEMP_WAV)

            if user_text:
                print(f'📝 You said: "{user_text}"')

                reply = generate_response(user_text)
                print(f'🤖 Assistant: "{reply}"\n')

                if any(w in reply for w in ["SHUTDOWN"]):
                    speak_text(tts_pipeline, "Goodbye!")
                    config.EMOTION = "sleep"
                    return

                elif any(w in reply for w in ["TAWUNIYA_QUERY"]):
                    context = query_rag(user_text)
                    print("QUERY\n", context)
                    reply = generate_rag_response(user_text, context)
                    speak_text(tts_pipeline, reply)
                    print(f'🤖 Assistant: "{reply}"\n')

                elif any(
                    w in reply
                    for w in [
                        "MOVE",
                        "TURN",
                        "FORWARD",
                        "BACKWARD",
                        "LEFT",
                        "RIGHT",
                        "STOP",
                    ]
                ):
                    speak_text(tts_pipeline, "Okay")
                    motor_controller.execute_llm_command(reply)
                else:
                    text, emotion = extract_emotion_and_clean_text(reply)
                    config.EMOTION = emotion
                    speak_text(tts_pipeline, text)

                print("Ready...\n")
                return
            else:
                print("\n❓ No speech detected in the captured audio\n")
        else:
            print("\n💤 No speech detected, still listening...\n")
            time.sleep(0.5)
            return

    def callback(indata, frames, time, status):
        pcm = struct.unpack_from("h" * frame_length, indata)
        result = porcupine.process(pcm)
        if result >= 0:
            event_queue.put("WAKE")

    with sd.RawInputStream(
        samplerate=sample_rate,
        blocksize=frame_length,
        channels=1,
        dtype="int16",
        callback=callback,
    ):

        while True:
            if (
                time.time() - config.TIME_TO_SLEEP
            ) > AWAKE_TIME and config.EMOTION != "sleep":
                config.EMOTION = "sleep"

            render_face(config.EMOTION, config.IS_TALKING, 0.1)

            try:
                event = event_queue.get_nowait()
                if event == "WAKE":
                    with threading.Lock():
                        if not config.LLM_VOICE_THREAD:
                            config.LLM_VOICE_THREAD = True
                            config.EMOTION = (
                                config.EMOTION
                                if config.EMOTION != "sleep"
                                else "neutral"
                            )
                            motor_controller.execute_llm_command("STOP")

                            def worker():
                                wakeUp()
                                config.LLM_VOICE_THREAD = False

                            threading.Thread(target=worker, daemon=True).start()
            except queue.Empty:
                pass

            time.sleep(0.01)

    print("\n👋 Goodbye!")
    print("=" * 50)


if __name__ == "__main__":
    main()
