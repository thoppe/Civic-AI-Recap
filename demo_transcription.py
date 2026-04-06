from pathlib import Path
import sys

from CAIR import Transcription


def parse_args(argv):
    audio_path = Path(argv[1]) if len(argv) > 1 else Path("test_assets/Ln8UwPd1z20.wav")
    method = argv[2] if len(argv) > 2 else "faster_whisper"
    model_size = argv[3] if len(argv) > 3 else "turbo"
    return audio_path, method, model_size


def run_demo(audio_path, method, model_size):
    if not audio_path.exists():
        raise FileNotFoundError(audio_path)

    t = Transcription(
        method=method,
        model_size=model_size,
        compute_vad=True,
        vad_progress=True,
        stitch_progress=True,
        output_progress=(method == "faster_whisper"),
    )

    print(f"audio path: {audio_path}")
    print(f"method: {method}")
    print(f"model size: {model_size}")
    print(f"device: {t.device}")

    df = t.transcribe(str(audio_path), text_only=False, force=True)

    print(f"resolved vad device: {t.vad_device}")
    print(f"audio length seconds: {t.audio_length_seconds:.2f}")
    print(f"rows: {len(df)}")
    if "is_vad" in df.columns:
        print(f"rows overlapping vad: {int(df['is_vad'].sum())}")

    print("\nhead:")
    print(df[["start", "end", "text", "is_vad"]].head(10).to_string(index=False))

    print("\ntail:")
    print(df[["start", "end", "text", "is_vad"]].tail(10).to_string(index=False))


audio_path, method, model_size = parse_args(sys.argv)
run_demo(audio_path, method, model_size)
