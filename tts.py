import boto3
import subprocess
from pathlib import Path
import threading
import config

# ----------------------
# Paths
# ----------------------
BEDROCK_WAV = Path("/tmp/bedrock_tts.wav")

# ----------------------
# Playback lock
# ----------------------
_play_lock = threading.Lock()

# ----------------------
# Amazon Bedrock TTS function
# ----------------------
def tts_bedrock(text: str, voice: str = "alloy"):
    """
    Generate speech using Amazon Bedrock TTS and save as WAV.
    """
    try:
        client = boto3.client("bedrock-runtime")  # Make sure AWS creds are configured
        response = client.invoke_model(
            modelId="amazon.titan-tts",  # Amazon TTS model
            contentType="application/json",
            accept="audio/wav",
            body=f'{{"text": "{text}", "voice": "{voice}"}}'
        )

        audio_stream = response["body"].read()
        BEDROCK_WAV.write_bytes(audio_stream)
        return BEDROCK_WAV
    except Exception as e:
        print(f"❌ Bedrock TTS error: {e}")
        return None

# ----------------------
# Play WAV asynchronously
# ----------------------
def play_wav_async(wav_path: Path):
    def _play():
        with _play_lock:
            try:
                # Force USB speaker
                subprocess.run(["aplay", "-D", "plughw:0,0", str(wav_path)])
            except Exception as e:
                print(f"❌ Playback error: {e}")

    threading.Thread(target=_play, daemon=True).start()

# ----------------------
# Speak text function
# ----------------------
def speak_text(text: str):
    print("🔊 Speaking...")
    wav = tts_bedrock(text)
    if not wav:
        print("❌ TTS generation failed")
        return

    config.IS_TALKING = True
    play_wav_async(wav)
    # IS_TALKING will reset when playback finishes in the thread
