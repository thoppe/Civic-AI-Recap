from dspipe import Pipe
from CAIR import Transcription
import pandas as pd

clf = Transcription(method="whisperx")


def compute(f0, f1):
    print(f"Processing {f0}")
    result = clf.transcribe(f0, text_only=False)
    df = pd.DataFrame(result["segments"])
    del df["words"]
    df.to_csv(f1, index=False)


Pipe("data/audio", "data/transcript", output_suffix=".csv")(compute, 1)
