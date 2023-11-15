import pandas as pd
import json
import os
from pathlib import Path
from dspipe import Pipe

f_ID_list = "targets/sample_youtube_IDs.txt"
f_ID_list = "targets/CA_StateBoard.txt"

model_name = "gpt-3.5-turbo-1106"
# model_name = "gpt-4-1106-preview"
load_dest = Path("data") / model_name


def download_video(video_id, f1):
    cmd = f'python cair.py --video_id="{video_id}" --download_only'
    os.system(cmd)


with open(f_ID_list) as FIN:
    video_ids = [line.strip() for line in FIN]

Pipe(video_ids, "data/audio", output_suffix=".mp4")(download_video, 2)

exit()


#######################################################################


def add_link(row):
    url = f"https://www.youtube.com/watch?v={row.Youtube_Id}"

    f_link = Path("data") / "transcript" / (row.Youtube_Id + ".txt")
    assert f_link.exists()
    link = f"[{row.Title}]({url}) [🎤]({f_link})"

    return link


def add_recap_links(row):
    load_dest = Path("data") / model_name

    link = []

    f_link = load_dest / "summary_md" / (row.Youtube_Id + ".md")
    if f_link.exists():
        link.append(f"[🎯]({f_link})")

    # f_link = load_dest / "summary_news" / (row.Youtube_Id + ".md")
    # if f_link.exists():
    #    link.append(f"[💬]({f_link})")

    f_link = load_dest / "summary_full" / (row.Youtube_Id + ".md")
    if f_link.exists():
        link.append(f"[📜]({f_link})")

    link = " ".join(link)

    return link


exit()

df.columns = [x.title() for x in df.columns]
df["Title"] = df.apply(add_link, axis=1)

model_name = "gpt-3.5-turbo-1106"
df["Recap GPT-3.5"] = df.apply(add_recap_links, axis=1)

model_name = "gpt-4-1106-preview"
df["Recap GPT-4.0"] = df.apply(add_recap_links, axis=1)

del df["Youtube_Id"]

df = df.set_index("Title")
df_out = df.to_markdown()

with open("README.md") as FIN:
    text = FIN.read()

marker = "## Reports"
text = text.split(marker)[0] + marker + "\n" + df_out
with open("README.md", "w") as FOUT:
    FOUT.write(text)

print(df_out)
