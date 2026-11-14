import pvporcupine
import os

ACCESS_KEY = "sJ3o1UrBk9GI9M9HzmBiw7Zrto30ZIgzOZD9d1nJhNI1GxJ74odRCw=="      
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WAKEWORD_PATH = os.path.join(BASE_DIR, "aurix.ppn")
#WAKEWORD_PATH = "./aurix.ppn"    


porcupine = pvporcupine.create(
    access_key=ACCESS_KEY,
    keyword_paths=[WAKEWORD_PATH]
)

sample_rate = porcupine.sample_rate
frame_length = porcupine.frame_length

