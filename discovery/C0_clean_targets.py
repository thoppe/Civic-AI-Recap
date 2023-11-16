from dspipe import Pipe
import pandas as pd
from urllib.parse import urlparse, parse_qs
from CAIR import Video, Channel

f_csv = "targets/US_education_boards.csv"
df = pd.read_csv(f_csv)
df = df.drop_duplicates(subset=["State", "Abbreviation"])

def get_video_id(url):
    if not url:
        return

    parsed_url = urlparse(url)

    # Extract the query string
    query_string = parsed_url.query
    parameters = parse_qs(query_string)

    if "v" not in parameters:
        raise KeyError(f"URL {url} doesn't look like a valid youtube video")

    return parameters["v"][0]


def build_url(video_id):
    if not video_id:
        return

    return f"https://www.youtube.com/watch?v={video_id}"


def get_video_information(video_id):
    if not video_id:
        return {}
    return Video(video_id).build_info()


def get_channel_id(video_id):
    if not video_id:
        return
    return Video(video_id).channel_id


# First clean any URLs
df["video_id"] = df["URL"].fillna("").apply(get_video_id)
df["URL"] = df["video_id"].apply(build_url)

df["channel_id"] = Pipe(df["video_id"])(get_channel_id, 1)

channels = df['channel_id'].dropna().drop_duplicates()
data = Pipe(channels)(lambda x: Channel(x).build_info(), 1)
dx = pd.DataFrame(data)

for key in ['description', 'title', 'n_videos']:
    if key in df:
        del df[key]

df = pd.merge(df, dx, on="channel_id", how="left")
df.to_csv(f_csv, index=False)
