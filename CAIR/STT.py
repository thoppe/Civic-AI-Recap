import diskcache
import pandas as pd

cache_whisper = diskcache.Cache(
    "cache/transcription/whisper", size_limit=int(1e11)
)
# key_name = "HF_ACCESS_TOKEN"
# HF_API_KEY = os.environ.get(key_name)

# Using source adudio of 4000 seconds
# Using Whisper this takes  : 1415 seconds
# Using faster_whisper takes: 146 seconds
# Using Whisperx this takes : 108+38+... seconds (alignment)


class Transcription:
    def __init__(self, method="whisperx", model_size="large", language="en"):
        self.method = method

        self.model = None
        self.model_size = model_size
        self.language = language
        self.device = "cuda"

    def load_STT_model(self):
        if self.model is not None:
            return

        if self.method == "faster_whisper":
            from faster_whisper import WhisperModel

            self.model = WhisperModel(
                self.model_size, device=self.device, compute_type="float16"
            )

        if self.method == "whisper":
            import whisper

            self.model = whisper.load_model(self.model_size, device=self.device)

        if self.method == "whisperx":
            import whisperx

            # self.diarize_model = whisperx.DiarizationPipeline(
            #    use_auth_token=HF_API_KEY, device=self.device
            # )

            self.model = whisperx.load_model(
                self.model_size,
                device=self.device,
                language=self.language,
            )
            self.align_model, self.align_meta = whisperx.load_align_model(
                language_code=self.language, device=self.device
            )

    def compute_whisperx(self, f_audio):
        import whisperx

        self.load_STT_model()

        audio = whisperx.load_audio(f_audio)
        result = self.model.transcribe(audio, language=self.language)

        result = whisperx.align(
            result["segments"],
            self.align_model,
            self.align_meta,
            audio,
            self.device,
            return_char_alignments=False,
        )

        # Skipping diarize
        # diarize_segments = self.diarize_model(audio)
        # result = whisperx.assign_word_speakers(diarize_segments, result)
        # print(f"Align {time.time() - t0:0.2f}")

        return result

    def transcribe(self, f_audio, text_only=True):
        if f_audio not in cache_whisper:
            result = self.compute_whisperx(f_audio)
            cache_whisper[f_audio] = result

        # For faster_whisper
        # segments, info = self.model.transcribe(
        #    f_audio, vad_filter=True, language="en", beam_size=5
        # )
        # print(info)
        # print(segments)
        # for seg in segments:
        #    print(seg)

        # For whisper
        # result = self.model.transcribe(f_audio, language=self.language)

        result = cache_whisper[f_audio]

        if text_only:
            df = pd.DataFrame(result["segments"])
            result = "\n".join(df["text"].str.strip())

        return result
