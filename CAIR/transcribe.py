import diskcache
import pandas as pd
from wasabi import msg

from .s3_utils import s3_location_to_audio_numpy

# key_name = "HF_ACCESS_TOKEN"
# HF_API_KEY = os.environ.get(key_name)

# Using source adudio of 4000 seconds
# Using Whisper this takes  : 1415 seconds
# Using faster_whisper takes: 146 seconds
# Using Whisperx this takes : 108+38+... seconds (alignment)


def post_process_transcription_result(result, text_only=True):
    df = pd.DataFrame(result["segments"])

    if text_only:
        return "\n".join(df["text"].str.strip())

    df = df[["start", "end", "text"]].copy()
    df["text"] = df["text"].str.strip()
    return df


class Transcription:
    def __init__(
        self,
        method="whisper",
        model_size="turbo",
        language="en",
    ):
        if method != "whisper":
            raise ValueError(
                "Only method='whisper' is supported."
            )

        self.method = method
        self.model = None
        self.model_size = model_size
        self.language = language
        self.device = self._get_device()
        self.cache = diskcache.Cache(
            f"cache/transcription/{method}/{model_size}", size_limit=int(1e11)
        )
        self.compute_method_call = self.compute_whisper

    def _get_device(self):
        """Automatically detect the best available device (CUDA, MPS, or CPU)."""
        try:
            import torch

            if torch.cuda.is_available():
                return "cuda"
            elif (
                hasattr(torch.backends, "mps")
                and torch.backends.mps.is_available()
            ):
                return "mps"
            else:
                return "cpu"
        except ImportError:
            return "cpu"

    def load_STT_model(self):
        if self.model is not None:
            return

        msg.warn(f"Loading transcription method {self.method}:{self.model_size}")

        import whisper

        # Whisper has compatibility issues with MPS on macOS
        # Use CPU for whisper to avoid PyTorch MPS compatibility issues
        whisper_device = "cpu" if self.device == "mps" else self.device
        self.model = whisper.load_model(
            self.model_size, device=whisper_device
        )

    def compute_whisper(self, f_audio):
        self.load_STT_model()
        result = self.model.transcribe(f_audio, language=self.language)
        return result

    def transcribe(self, f_audio, text_only=True):
        if f_audio not in self.cache:
            result = self.compute_method_call(f_audio)

            self.cache[f_audio] = result

        result = self.cache[f_audio]
        return post_process_transcription_result(
            result, text_only=text_only
        )

    def transcribe_s3(self, s3_location, text_only=True):
        if s3_location not in self.cache:
            audio = s3_location_to_audio_numpy(s3_location)
            result = self.compute_method_call(audio)
            self.cache[s3_location] = result

        result = self.cache[s3_location]
        return post_process_transcription_result(
            result, text_only=text_only
        )
