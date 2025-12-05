from rich import print_json
from CAIR import Channel, Video, Transcription, Analyze

# import pandas as pd

video_id = "P0rxq42sckU"

vid = Video(video_id)
channel = Channel(vid.channel_id)

print(channel)
print(vid.title)
print(channel.title, channel.n_videos)

f_audio = f"{video_id}.mp3"
vid.download_audio(f_audio)

df = Transcription().transcribe(f_audio, text_only=False)
print(df)
print(len(df))

model = Analyze(model_name="gpt-5-mini")
text = model.preprocess_text(df)
streamline = model.streamline(text)

esum = model.executive_summary(streamline)
print(esum)

print(len(text), len(streamline), len(esum))
print(len(text.split()), len(streamline.split()), len(esum.split()))

# Look at the channel info
print(channel.get_uploads()[["video_id", "title", "publishedAt"]])


print_json(data=channel.get_metadata())
