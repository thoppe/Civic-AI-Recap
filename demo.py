import datetime
import json
from CAIR import Channel, Video, Transcription, Analyze

video_id = "P0rxq42sckU"
video_id = "dvQxuqVqsoM"  # Short CDC video for testing

vid = Video(video_id)
channel = Channel(vid.channel_id)

print(channel)
print(vid.title)
print(channel.title, channel.n_videos)

# Look at the channel info
two_months_ago = datetime.date.today() - datetime.timedelta(days=60)
recent_uploads = channel.get_uploads(stop_before=two_months_ago)
print(recent_uploads[["video_id", "title", "publishedAt"]])
print(json.dumps(channel.get_metadata(), indent=2))

exit()

f_audio = f"{video_id}.mp3"
vid.download_audio(f_audio)

df = Transcription(
    method="faster_whisper",
    model_size="distil-large-v3",
    compute_vad=True,
).transcribe(f_audio, text_only=False)

# df = df[df["is_vad"]==True]
print(df)


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
if clf.usage:
    print(clf.usage[0])
else:
    print("No usage recorded.")
