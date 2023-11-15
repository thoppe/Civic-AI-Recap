import pandas as pd
from CAIR import Channel, Video, Transcription, Analyze

video_id = "A0HVwoagKPc"
vid = Video(video_id)
channel = Channel(vid.channel_id)

print(vid.title)
print(channel.title, channel.n_videos)

df = pd.DataFrame(channel.get_uploads())
print(df)

f_audio = f"{video_id}.mp4"
vid.download_audio(f_audio)

text = Transcription().transcribe(f_audio)
print(Analyze().summarize(text))
print(Analyze().outline(text))
