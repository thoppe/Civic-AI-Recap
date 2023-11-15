import os
import time
from pathlib import Path
import random

# model_name = "gpt-3.5-turbo-1106"

while True:
    load_dest = Path("data/audio/")
    F_AUDIO = list(load_dest.glob("*.mp4"))
    random.shuffle(F_AUDIO)

    for f_audio in F_AUDIO:
        video_id = f_audio.stem
        f_transcript = Path("data/transcript/") / f"{video_id}.txt"
        if f_transcript.exists():
            continue

        # print(f_transcript)
        cmd = f'python cair.py --video_id="{video_id}" --transcribe_only'

        print(cmd)
        # os.system(cmd)
    exit()

    time.sleep(2)
