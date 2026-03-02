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


def post_process_transcription_result(
    result,
    text_only=True,
    vad_filter=False,
):
    df = pd.DataFrame(result["segments"])
    df = df[["start", "end", "text"]].copy()
    df["start"] = pd.to_numeric(df["start"], errors="coerce")
    df["end"] = pd.to_numeric(df["end"], errors="coerce")
    df["text"] = df["text"].astype(str).str.strip()

    if vad_filter and "VAD" not in result:
        raise KeyError("VAD not present in transcription")

    if vad_filter:
        
        vad_df = pd.DataFrame(result["VAD"])
        if not {"start", "end"}.issubset(vad_df.columns):
            raise KeyError("VAD")

        vad_df = vad_df[["start", "end"]].copy()
        vad_df["start"] = pd.to_numeric(vad_df["start"], errors="coerce")
        vad_df["end"] = pd.to_numeric(vad_df["end"], errors="coerce")
        vad_df = vad_df.dropna(subset=["start", "end"])

        if vad_df.empty:
            df["is_vad"] = False
        else:
            vad_starts = vad_df["start"]
            vad_ends = vad_df["end"]
            df["is_vad"] = [
                bool(((seg_start < vad_ends) & (seg_end > vad_starts)).any())
                for seg_start, seg_end in zip(df["start"], df["end"])
            ]

    if text_only:
        return "\n".join(df["text"])

    return df


class Transcription:
    """
    Transcribe audio with Whisper, optional Silero VAD pre-processing, and disk cache.

    This class manages model lifecycle (lazy load), optional voice-activity
    detection, and cached transcription results keyed by the audio source.

    Args:
        method (str): Speech-to-text backend. Supported:
            ``"whisper"`` and ``"faster_whisper"``.
        model_size (str): Whisper model variant to load (for example ``"turbo"``).
        language (str): Language hint passed to Whisper transcription.
        compute_vad (bool): Enable Silero VAD pass before Whisper.
        output_progress (bool): If True and method is ``"faster_whisper"``,
            show progress and emit per-segment tuples while consuming results.
        force (bool): Default cache-read policy. If True, recompute instead of
            reading cached results (while still writing new results to cache).
    """
    def __init__(
        self,
        method="whisper",
        model_size="turbo",
        language="en",
        compute_vad=False,
        output_progress=False,
        force=False,
    ):
        if method not in {"whisper", "faster_whisper"}:
            raise ValueError(
                "Supported methods are 'whisper' and 'faster_whisper'."
            )

        self.method = method
        self.model = None
        self.vad_model = None
        self.model_size = model_size
        self.language = language
        self.vad_filter = compute_vad
        self.output_progress = output_progress
        self.force = force
        self.device = self._get_device()
        self.cache = diskcache.Cache(
            f"cache/transcription/{method}/{model_size}", size_limit=int(1e11)
        )
        self.vad_cache = diskcache.Cache(
            "cache/transcription_vad/silero", size_limit=int(1e11)
        )
        
        if method == "whisper":
            self.compute_method_call = self.compute_whisper
        elif method == "faster_whisper":
            self.compute_method_call = self.compute_faster_whisper
        else:
            raise KeyError("Unknown method", self.compute_method_call)

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

    def load_faster_whisper_model(self):
        if self.model is not None:
            return

        msg.warn(f"Loading transcription method {self.method}:{self.model_size}")
        from faster_whisper import WhisperModel

        # faster-whisper supports cuda/cpu; fallback mps to cpu.
        faster_device = "cpu" if self.device == "mps" else self.device
        compute_type = "float16" # if faster_device == "cuda" else "int8"
        
        self.model = WhisperModel(
            self.model_size,
            device=faster_device,
            compute_type=compute_type,
        )

    def load_VAD_model(self):
        if self.vad_model is not None:
            return
        if not self.vad_filter:
            return

        msg.warn("Loading VAD model silero-vad")
        from silero_vad import load_silero_vad

        self.vad_model = load_silero_vad()

    def compute_vad_segments(self, f_audio):
        if not self.vad_filter:
            return None

        self.load_VAD_model()

        # Starting point: only run VAD for local audio-file paths.
        # S3 audio currently arrives as numpy arrays in transcribe_s3.
        if not isinstance(f_audio, str):
            return None

        from silero_vad import get_speech_timestamps, read_audio

        wav = read_audio(f_audio)
        return get_speech_timestamps(
            wav,
            self.vad_model,
            return_seconds=True,
        )

    def get_vad_segments(self, f_audio, force=None):
        if not self.vad_filter:
            return None

        # Starting point: only run VAD for local audio-file paths.
        # S3 audio currently arrives as numpy arrays in transcribe_s3.
        if not isinstance(f_audio, str):
            return None

        force_read = self.force if force is None else force
        if force_read or f_audio not in self.vad_cache:
            self.vad_cache[f_audio] = self.compute_vad_segments(f_audio)

        return self.vad_cache[f_audio]

    def compute_whisper(self, f_audio, force=None):
        vad_segments = self.get_vad_segments(f_audio, force=force)
        if self.vad_filter and vad_segments is not None:
            msg.info(f"VAD detected {len(vad_segments)} speech segments")

        self.load_STT_model()
        result = self.model.transcribe(f_audio, language=self.language)
 
        if self.vad_filter and vad_segments is not None:
            result["VAD"] = vad_segments
            
        return result

    def compute_faster_whisper(self, f_audio, force=None):
        vad_segments = self.get_vad_segments(f_audio, force=force)
        if self.vad_filter and vad_segments is not None:
            msg.info(f"VAD detected {len(vad_segments)} speech segments")

        self.load_faster_whisper_model()
        segments, info = self.model.transcribe(
            f_audio,
            language=self.language,
            beam_size=5,
        )
        if self.output_progress:
            from tqdm import tqdm

            segments_data = []
            for segment in tqdm(segments, desc="faster_whisper segments"):
                tqdm.write((segment.start, segment.end, segment.text).__repr__())
                segments_data.append(
                    {
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text,
                    }
                )
        else:
            segments_data = [
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                }
                for segment in segments
            ]
        result = {
            "segments": segments_data,
            "language": getattr(info, "language", None),
        }

        if self.vad_filter and vad_segments is not None:
            result["VAD"] = vad_segments

        return result

    def transcribe(self, f_audio, text_only=True, force=None):
        """
        Run transcription for a local audio input and return processed output.

        Args:
            f_audio (str | Any): Audio input accepted by the active backend.
            text_only (bool): If True, return one combined transcript string.
                If False, return a DataFrame with ``start``, ``end``, ``text``.
            force (bool | None): Per-call override for cache reads. ``True``
                skips reading from cache; ``None`` uses ``self.force``.

        Returns:
            str | pandas.DataFrame: Post-processed transcription result.
        """
        force_read = self.force if force is None else force
        if force_read or f_audio not in self.cache:
            result = self.compute_method_call(f_audio, force=force_read)

            self.cache[f_audio] = result

        result = self.cache[f_audio]
        if self.vad_filter:
            # Resolve VAD independently from transcription cache so older cached
            # transcription payloads without "VAD" can still be processed.
            vad_segments = self.get_vad_segments(f_audio, force=force_read)
            if vad_segments is not None:
                result = dict(result)
                result["VAD"] = vad_segments
                self.cache[f_audio] = result
        
        return post_process_transcription_result(
            result,
            text_only=text_only,
            vad_filter=self.vad_filter,
        )

    def transcribe_s3(self, s3_location, text_only=True, force=None):
        force_read = self.force if force is None else force
        if force_read or s3_location not in self.cache:
            audio = s3_location_to_audio_numpy(s3_location)
            result = self.compute_method_call(audio, force=force_read)
            self.cache[s3_location] = result

        result = self.cache[s3_location]
        return post_process_transcription_result(
            result,
            text_only=text_only,
            vad_filter=self.vad_filter,
        )
