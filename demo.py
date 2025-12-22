from rich import print_json
from CAIR import Channel, Video, Transcription, Analyze

video_id = "P0rxq42sckU"
video_id = "dvQxuqVqsoM"  # Short CDC video for testing

vid = Video(video_id)
channel = Channel(vid.channel_id)

print(channel)
print(vid.title)
print(channel.title, channel.n_videos)

# Look at the channel info
print(channel.get_uploads()[["video_id", "title", "publishedAt"]])
print_json(data=channel.get_metadata())

f_audio = f"{video_id}.mp3"
vid.download_audio(f_audio)

df = Transcription().transcribe(f_audio, text_only=False)
print(df)
print(len(df))

clf = Analyze(
    model_name="gpt-5-mini",
    reasoning_effort="low",
    service_tier="flex",
)
instructions = "Explain the transcript like I'm 6."
text = clf.preprocess_text(df)
print(text)
print("************************************************")
print(instructions)
print("************************************************")
result = clf(
    prompt=text,
    system_prompt=instructions,
)
print(result)
print(clf.usage.iloc[0].to_dict())
