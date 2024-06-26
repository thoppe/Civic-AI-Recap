import diskcache
import pandas as pd
from wasabi import msg

# key_name = "HF_ACCESS_TOKEN"
# HF_API_KEY = os.environ.get(key_name)

# Using source adudio of 4000 seconds
# Using Whisper this takes  : 1415 seconds
# Using faster_whisper takes: 146 seconds
# Using Whisperx this takes : 108+38+... seconds (alignment)


class Transcription:
    def __init__(
        self,
        method="whisperx",
        model_size="large",
        language="en",
    ):
        self.method = method
        self.model = None
        self.model_size = model_size
        self.language = language
        self.device = "cuda"
        self.cache = diskcache.Cache(
            f"cache/transcription/{method}", size_limit=int(1e11)
        )

        self.compute_method_call = {
            "insanely-fast-whisper": self.compute_insane_whisper,
            "whisper": self.compute_whisper,
            "whisperx": self.compute_whisperx,
            "faster-whisper": self.compute_faster_whisper,
        }[self.method]

    def load_STT_model(self):
        if self.model is not None:
            return

        msg.warn(f"Loading transcription method {self.method}")

        if self.method == "insanely-fast-whisper":
            from transformers import pipeline
            import torch

            self.model = pipeline(
                "automatic-speech-recognition",
                "openai/whisper-large-v2",
                torch_dtype=torch.float16,
                device=self.device,
            )

        elif self.method == "faster-whisper":
            from faster_whisper import WhisperModel

            self.model = WhisperModel(
                self.model_size, device=self.device, compute_type="float16"
            )

        elif self.method == "whisper":
            import whisper

            self.model = whisper.load_model(self.model_size, device=self.device)

        elif self.method == "whisperx":
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
        else:
            raise KeyError(f"Model {self.method} not found")

    def compute_whisper(self, f_audio):
        result = self.model.transcribe(f_audio, language=self.language)
        return result

    def compute_faster_whisper(self, f_audio):
        segments, info = self.model.transcribe(
            f_audio, vad_filter=True, language="en", beam_size=5
        )
        segments = list(segments)
        print(segments)
        return segments

    def compute_whisperx(self, f_audio, batch_size=24 * 2):
        import whisperx

        self.load_STT_model()

        audio = whisperx.load_audio(f_audio)
        result = self.model.transcribe(
            audio, language=self.language, batch_size=batch_size
        )

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

    def compute_insane_whisper(self, f_audio, batch_size=24 * 2):
        self.load_STT_model()
        outputs = self.model(
            f_audio,
            chunk_length_s=30,
            batch_size=batch_size,
            return_timestamps=True,
        )
        return outputs

    def transcribe(self, f_audio, text_only=True):
        if f_audio not in self.cache:
            result = self.compute_method_call(f_audio)

            self.cache[f_audio] = result

        result = self.cache[f_audio]

        if self.method == "whisperx":
            df = pd.DataFrame(result["segments"])

        elif self.method == "whisper":
            df = pd.DataFrame(result["segments"])

        elif self.method == "insanely-fast-whisper":
            df = pd.DataFrame(result["chunks"])

        else:
            raise KeyError(f"{self.method}")

        if text_only:
            result = "\n".join(df["text"].str.strip())
            return result

        df = df[["start", "end", "text"]]
        df["text"] = df["text"].str.strip()

        return df
