import pandas as pd
import json
from CAIR import Video
from dspipe import Pipe

df = pd.read_csv("targets/selected_US_education_boards.csv")
df = df[df.target == 1]


def compute(f0, f1):
    vid = Video(f0)
    meta = vid.build_info()
    js = json.dumps(meta, indent=2)
    with open(f1, "w") as FOUT:
        FOUT.write(js)


Pipe(df.video_id, "data/video_metadata", output_suffix=".json")(compute, 4)
