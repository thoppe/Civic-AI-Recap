from dspipe import Pipe
from CAIR import Analyze
import pandas as pd

clf = Analyze("gpt-3.5-turbo-1106", parallel_threads=4)


def compute(f0, f1):
    df = pd.read_csv(f0)
    text = "\n".join([line.strip() for line in df["text"]])
    # outline = clf.outline(text)
    print(clf.summarize(text))
    exit()


Pipe("data/transcript", "data/outline", output_suffix=".json")(compute, 1)
