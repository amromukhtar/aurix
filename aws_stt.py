import asyncio
import time
import numpy as np
import sounddevice as sd
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler

# Your specified limits
MAX_DURATION = 30  # Stop after 30 seconds total
END_SILENCE_MS = 800  # Stop if silent for 0.8s after speaking
SILENCE_TIMEOUT = 5  # Stop if no speech at all for 5s
SILENCE_THRESHOLD = 500  # Volume threshold (adjust for your USB mic)


class MyEventHandler(TranscriptResultStreamHandler):
    def __init__(self, output_stream):
        super().__init__(output_stream)
        self.final_transcript = ""

    async def handle_transcript_event(self, transcript_event):
        results = transcript_event.transcript.results
        for result in results:
            if not result.is_partial:
                for alt in result.alternatives:
                    self.final_transcript += alt.transcript + " "


async def mic_stream(stop_event):
    """Missing Mic Logic: Captures from Pi hardware and checks limits"""
    print("🎤 AWS Streaming Active...")
    loop = asyncio.get_event_loop()
    input_queue = asyncio.Queue()

    def callback(indata, frame_count, time_info, status):
        loop.call_soon_threadsafe(input_queue.put_nowait, (bytes(indata), status))

    # Standard AWS Transcribe settings: 16kHz, Mono, 16-bit PCM
    stream = sd.RawInputStream(
        channels=1, samplerate=16000, callback=callback, blocksize=2048, dtype="int16"
    )

    start_time = time.time()
    last_voice_time = time.time()
    has_started_speaking = False

    with stream:
        while not stop_event.is_set():
            # 1. Check 30s Limit
            if (time.time() - start_time) > MAX_DURATION:
                stop_event.set()
                break

            indata, status = await input_queue.get()
            audio_data = np.frombuffer(indata, dtype=np.int16)
            rms = np.sqrt(np.mean(audio_data.astype(float) ** 2))

            curr = time.time()
            if rms > SILENCE_THRESHOLD:
                last_voice_time = curr
                has_started_speaking = True

            # 2. Check 800ms End-Silence or 5s Initial-Silence
            silence_duration = (curr - last_voice_time) * 1000
            if (has_started_speaking and silence_duration > END_SILENCE_MS) or (
                not has_started_speaking and (curr - last_voice_time) > SILENCE_TIMEOUT
            ):
                stop_event.set()
                break

            yield indata


async def write_chunks(stream, stop_event):
    """Missing Write Logic: Pipes mic data to AWS"""
    async for chunk in mic_stream(stop_event):
        await stream.input_stream.send_audio_event(audio_chunk=chunk)
    await stream.input_stream.end_stream()


# Global client instance
transcribe_client = TranscribeStreamingClient(region="us-east-1")


async def get_aws_transcription():
    """Main Caller"""
    try:
        stream = await transcribe_client.start_stream_transcription(
            language_code="en-US", media_sample_rate_hz=16000, media_encoding="pcm"
        )
        stop_event = asyncio.Event()
        handler = MyEventHandler(stream.output_stream)

        await asyncio.gather(write_chunks(stream, stop_event), handler.handle_events())
        return handler.final_transcript.strip()
    except Exception as e:
        print(f"AWS Transcribe Error: {e}")
        return None
