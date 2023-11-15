import json
import pandas as pd
from dspipe import Pipe
from P0_download_channel_listing import *
from urllib.parse import urlparse, parse_qs

df = pd.read_csv("data/StateEdBoard.csv")


def download_video_metadata(video_id, f1):
    print(video_id)
    js = get_video_metadata(video_id)
    js = json.dumps(js, indent=2)
    with open(f1, "w") as FOUT:
        FOUT.write(js)


def download_channel_metadata(channel_id, f1):
    print(channel_id)
    js = get_channel_metadata(channel_id)
    js = json.dumps(js, indent=2)
    with open(f1, "w") as FOUT:
        FOUT.write(js)


def get_channel_ID(f0):
    with open(f0) as FIN:
        js = json.load(FIN)
    js = js["items"][0]
    return {
        "video_id": f0.stem,
        "channel_id": js["snippet"]["channelId"],
    }


def clean_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get("v", [None])[0]


def download_channel_uploads(channel_id, f1):
    channel_name = df.loc[channel_id]["channel_name"]
    print(channel_id, channel_name)

    upload_playlist_id = get_channel_upload_id(channel_id)
    data = get_channel_uploads(upload_playlist_id)

    dx = pd.DataFrame(data).set_index("youtube_id")
    dx["channel_name"] = channel_name
    dx.to_csv(f1)


df = df.dropna(subset=["SampleVideo"])
df["video_id"] = df["SampleVideo"].apply(clean_url)
del df["SampleVideo"]

Pipe(df.video_id, "data/video_metadata", output_suffix=".json")(
    download_video_metadata, 1
)

info = pd.DataFrame(Pipe("data/video_metadata/")(get_channel_ID))
info = info.set_index("video_id")
df = df.set_index("video_id")
df["channel_id"] = info["channel_id"]
print(df)

Pipe(df.channel_id, "data/channel_metadata", output_suffix=".json")(
    download_channel_metadata, 1
)


def read_meta_json(f0):
    with open(f0) as FIN:
        js = json.load(FIN)["items"][0]["snippet"]
        return {"channel_name": js["title"], "channel_id": f0.stem}


df = df.set_index("channel_id")
info = pd.DataFrame(Pipe("data/channel_metadata/")(read_meta_json))
info = info.set_index("channel_id")
df["channel_name"] = info["channel_name"]
df = df[~df.index.duplicated(keep="first")]

Pipe(df.index, "data/channel_upload_list/", output_suffix=".csv")(
    download_channel_uploads, 1
)
