import pandas as pd
from CAIR import Channel, Video, Transcription, Analyze

video_id = "OoqYjxkjsRU"
vid = Video(video_id)
channel = Channel(vid.channel_id)

print(vid.title)
print(channel.title, channel.n_videos)

df = pd.DataFrame(channel.get_uploads())
print(df)

f_audio = f"{video_id}.mp4"
vid.download_audio(f_audio)

text = Transcription().transcribe(f_audio)
with open("OoqYjxkjsRU.txt", "w") as FOUT:
    FOUT.write(text)

print(text[:500])

data = Transcription().transcribe(f_audio, text_only=False)
df = pd.DataFrame(data["segments"])[["start", "end", "text"]]
df.to_csv(f"{video_id}.csv")


model_name = "gpt-4-0125-preview"
model = Analyze(model_name)
print(model.summarize(text))

# print(Analyze("gpt-4-1106-preview").outline(text))

# print(Analyze().summarize(text))
# print(Analyze().outline(text))
