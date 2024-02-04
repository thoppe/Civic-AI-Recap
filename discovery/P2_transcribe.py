from dspipe import Pipe
from CAIR import Transcription
import pandas as pd

clf = Transcription("whisperx")


def compute(f0, f1):
    print(f"Transcribing {f0}")
    result = clf.transcribe(f0, text_only=False)
    df = pd.DataFrame(result["segments"])
    if "words" in df:
        del df["words"]
    else:
        # Handle a case where there are no words??
        print(df)
        return
    df.to_csv(f1, index=False)


Pipe(
    "data/audio",
    "data/transcript",
    shuffle=True,
    input_suffix="*.mp4",
    output_suffix=".csv",
)(compute, 1)
