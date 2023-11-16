from dspipe import Pipe
from CAIR import Transcription
import pandas as pd

clf = Transcription(method="whisperx")


def compute(f0, f1):
    print(f"Processing {f0}")
    result = clf.transcribe(f0)
    df = pd.DataFrame(result["segments"])
    df.to_csv(f1)


Pipe("data/audio", "data/transcript", output_suffix=".csv")(compute, 1)
