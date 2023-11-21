from pathlib import Path
from CAIR import Video
from dspipe import Pipe
from wasabi import msg


def compute(f0, f1):
    # Check if the transcript exists, if so we can exit early
    f2 = Path("data/transcript/") / f0.with_suffix(".csv").name
    if f2.exists():
        msg.warn(f"Transcript already exists for {f0}, skipping audio download")
        return

    try:
        Video(f0.stem).download_audio(f1)
    except Exception as EX:
        print(f"Failed with {EX}")


Pipe("data/video_metadata", "data/audio", output_suffix=".mp4")(compute, 2)
