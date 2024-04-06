import pandas as pd
from CAIR import Channel, Video, Transcription, Analyze

# video_id = "OoqYjxkjsRU"
video_id = "7Bho2wwBhOw"
vid = Video(video_id)
channel = Channel(vid.channel_id)

print(vid.title)
print(channel.title, channel.n_videos)

df = pd.DataFrame(channel.get_uploads())
print(df)

f_audio = f"{video_id}.mp4"
vid.download_audio(f_audio)

df = Transcription().transcribe(f_audio, text_only=False)
print(df)
df.to_csv(f"{video_id}.csv", index=False)
exit()

text = Transcription().transcribe(f_audio)
print(text[:2000])

model_name = "gpt-3.5-turbo-0125"

model = Analyze(model_name)
sum_text = model.summarize(text)
print(sum_text[:1000])
outline_text = model.outline(
    sum_text,
)
print(outline_text)

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
