from CAIR import Video
from dspipe import Pipe


def compute(f0, f1):
    Video(f0.stem).download_audio(f1)


Pipe("data/video_metadata", "data/audio", output_suffix=".mp4")(compute, 1)
