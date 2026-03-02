from pathlib import Path
from CAIR import Transcription

s3_location = "s3://groundvue/testing_assets/Ln8UwPd1z20.webm"
s3_location = "s3://groundvue/source_media/youtube/0qiIn_mDGoE.webm"

#clf = Transcription(model_size="turbo")

clf = Transcription(
    method="faster_whisper",
    model_size="distil-large-v3",
    compute_vad=True,
    force=True,
)

#for _ in range(5):
df = clf.transcribe_s3(s3_location, text_only=False)
print(df)



'''
# I have a dream speech (~5 minutes)
video_id = "_IB0i6bJIjw"

# Caral Sagan's Cosmic Calendar
video_id = "Ln8UwPd1z20"

video = Video(video_id)

f_save = Path(f"test_assets/{video_id}.mp3")
if not f_save.exists():
    video.download_audio(f_save)

from CAIR import Transcription
clf = Transcription(method="whisper", model_size="turbo")
df = clf.transcribe(str(f_save))

print(df)
'''
