from tqdm import tqdm
import pandas as pd
from src.utils import TTS
from pathlib import Path

# import argparse

# Create a command line argparser
# parser = argparse.ArgumentParser(description="TTS")
# parser.add_argument("youtube_id", type=str, help="YoutubeID")
# args = parser.parse_args()
# youtube_ID = args.youtube_id

youtube_id = "PlZFODj_Mq4"

# model_id = "gpt-3.5-turbo-1106"
model_id = "gpt-4-1106-preview"
summary_type = "full"

load_dest = Path("data") / model_id / f"summary_{summary_type}"
f_summary = load_dest / f"{youtube_id}.md"

save_dest = Path("data") / "TTS" / model_id / summary_type / youtube_id
save_dest.mkdir(exist_ok=True, parents=True)

with open(f_summary) as FIN:
    text = FIN.read()

data = []
for k, chunk in enumerate(text.split("\n")):
    chunk = chunk.strip()
    if not chunk:
        continue
    data.append({"text_chunk": chunk})

df = pd.DataFrame(data)
df["k"] = range(len(df))
df["f_chunk_audio"] = df.k.apply(lambda k: save_dest / f"{k:08d}.mp3")
df["is_exists"] = df["f_chunk_audio"].apply(lambda x: x.exists())

dx = df[df.is_exists == False]
for _, row in tqdm(dx.iterrows()):
    raw_mp3 = TTS(row.text_chunk)

    with open(row.f_chunk_audio, "wb") as FOUT:
        FOUT.write(raw_mp3)

print(df)


f_mp3_concat = save_dest / f"{youtube_id}.mp3"
if not f_mp3_concat.exists():
    from pydub import AudioSegment

    # Initialize an empty AudioSegment to store the concatenated audio
    output_audio = AudioSegment.empty()

    for f_mp3 in tqdm(df["f_chunk_audio"]):
        audio_segment = AudioSegment.from_mp3(f_mp3)
        output_audio += audio_segment

    # Export the concatenated audio to a single MP3 file
    output_audio.export(f_mp3_concat, format="mp3")
