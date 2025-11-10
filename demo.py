import pandas as pd
from CAIR import Channel, Video, Transcription, Analyze

# video_id = "OoqYjxkjsRU"
#video_id = "7Bho2wwBhOw"
#video_id = "l-HO22OaHsU"
video_id = "2PnYYb_xj3U"

vid = Video(video_id)
channel = Channel(vid.channel_id)

# print(vid.title)
# print(channel.title, channel.n_videos)

#df = pd.DataFrame(channel.get_uploads())
# print(df)

f_audio = f"{video_id}.mp4"
vid.download_audio(f_audio)

df = Transcription().transcribe(f_audio, text_only=False)
df.to_csv(f"output/{video_id}_transcription.csv")
print(df)

txt = '\n'.join(df['text'].values.tolist())
with open(f"output/{video_id}_transcription.txt", 'w') as FOUT:
    FOUT.write(txt)
print(txt)

model = Analyze()
stext = model.summarize(df["text"])
outline = model.outline(stext)

with open(f"output/{video_id}_summary.txt", 'w') as FOUT:
    FOUT.write(stext)

exit()

outline = model.align_sections(df["text"], outline)

dx = outline
dx["t0"] = [df.iloc[i]["start"] for i in dx.starting_index]
dx["t1"] = [df.iloc[i]["end"] for i in dx.ending_index]

dx["duration"] = dx["t1"] - dx["t0"]
print(dx["duration"])
print(dx["duration"].sum())
print(df["end"].max())
print(stext)
print(outline)
exit()

# js = vid.get_extended_metadata()
# print(js)

# exit()
# import json
# print(json.dumps(js, indent=2))
# exit()
# print(vid.download_english_captions())
# exit()

text = Transcription().transcribe(f_audio)
with open("OoqYjxkjsRU.txt", "w") as FOUT:
    FOUT.write(text)

print(text[:1000])
exit()

data = Transcription().transcribe(f_audio, text_only=False)
df = pd.DataFrame(data["segments"])[["start", "end", "text"]]
df.to_csv(f"{video_id}.csv")


model_name = "gpt-4-0125-preview"
model = Analyze(model_name)
print(model.summarize(text))

# print(Analyze("gpt-4-1106-preview").outline(text))

# print(Analyze().summarize(text))
# print(Analyze().outline(text))
