from CAIR import Video
from dspipe import Pipe

"""
from pathlib import Path
import os
def compute(f0, f1):
    load_dest = Path('/home/travis/COPY_CIVIC_AI/data/audio')
    f0 = load_dest / (f0.stem+'.mp4')
    if f0.exists():
        os.system(f'cp {f0} {f1}')
    print(f1)
"""


def compute(f0, f1):
    Video(f0.stem).download_audio(f1)


Pipe("data/video_metadata", "data/audio", output_suffix=".mp4")(compute, 4)
