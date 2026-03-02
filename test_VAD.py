from rich import print_json
from CAIR import Channel, Video, Transcription, Analyze

#f_audio = "silent_track_then_speaking.wav"
f_audio = "jRsHeQxjnrU.webm"

model_size = "turbo"
model_size = "large"

method = "faster_whisper"

model_size = "distil-large-v3"
#model_size = "large-v3"

clf = Transcription(method=method, model_size=model_size, compute_vad=True, output_progress=True)
df = clf.transcribe(f_audio, text_only=False)
#df = df[df["is_vad"]==True]
print(df)
df.to_csv(f"VAD_test2_{method}_{model_size}.csv", index=False)
