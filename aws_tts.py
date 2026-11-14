import boto3
from pygame import mixer
import os
import time
import config

polly = boto3.client("polly", region_name="us-east-1")


def speak_text(text, voice_id="Matthew"):
    try:
        # Try 'neural' first for better quality
        # If your region doesn't support it, change to 'standard'
        config.IS_TALKING = True
        response = polly.synthesize_speech(
            Engine="neural", Text=text, OutputFormat="mp3", VoiceId=voice_id
        )

        filename = "speech.mp3"
        with open(filename, "wb") as f:
            f.write(response["AudioStream"].read())

        mixer.init()
        # Small delay to let the Pi audio hardware initialize
        time.sleep(0.2)
        mixer.music.load(filename)
        mixer.music.play()

        while mixer.music.get_busy():
            time.sleep(0.1)

        mixer.quit()
        os.remove(filename)
        config.IS_TALKING = False

    except Exception as e:
        print(f"Error: {e}")
