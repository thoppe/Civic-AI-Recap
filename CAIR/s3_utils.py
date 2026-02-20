
import subprocess
import threading

import boto3
import numpy as np


def s3_location_to_audio_numpy(s3_location: str) -> np.ndarray:
    """
    Stream and decode an audio object from S3 into Whisper-ready PCM samples.

    Args:
        s3_location: Full S3 URI in the form ``s3://<bucket>/<key>``.

    Returns:
        A 1-D ``np.ndarray`` of ``np.float32`` mono audio at 16,000 Hz.
        Audio is decoded by ffmpeg from the source codec and resampled with
        SoX-quality resampling (``aresample=16000:resampler=soxr``).
        We use SoX here because higher-quality resampling typically preserves
        speech detail better than default resampling, which can improve Whisper
        transcription accuracy on compressed or noisy inputs.
    """
    # Validate expected URI format before any network/process work.
    if not s3_location.startswith("s3://"):
        raise ValueError(f"Expected s3:// URI, got: {s3_location}")

    s3_path = s3_location[5:]
    if "/" not in s3_path:
        raise ValueError(f"Expected s3://<bucket>/<key>, got: {s3_location}")
    # Split once so keys can still contain additional slashes.
    bucket, key = s3_path.split("/", 1)

    s3_client = boto3.client("s3")
    # Body is a streaming object; we do not download the source file to disk.
    obj = s3_client.get_object(Bucket=bucket, Key=key)

    # Decode to mono 16 kHz float PCM for Whisper.
    process = subprocess.Popen(
        [
            "ffmpeg",
            "-i",
            "pipe:0",
            "-af",
            "aresample=16000:resampler=soxr",
            "-f",
            "f32le",
            "-ac",
            "1",
            "-ar",
            "16000",
            "pipe:1",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    # Accumulate decoded PCM output.
    pcm_bytes = bytearray()
    writer_error = None

    def write_s3_to_ffmpeg():
        nonlocal writer_error
        # Feed ffmpeg stdin in chunks while main thread drains stdout.
        for chunk in obj["Body"].iter_chunks(chunk_size=1024 * 1024):
            if not chunk:
                continue
            try:
                process.stdin.write(chunk)
            except BrokenPipeError as exc:
                # ffmpeg exited early; capture so caller gets a clear error.
                writer_error = exc
                break
        try:
            process.stdin.close()
        except BrokenPipeError:
            pass

    writer = threading.Thread(target=write_s3_to_ffmpeg, daemon=True)
    writer.start()

    try:
        while True:
            out_chunk = process.stdout.read(1024 * 1024)
            if not out_chunk:
                break
            pcm_bytes.extend(out_chunk)
    finally:
        # Always join writer and close S3 stream, even on read/decode failure.
        writer.join()
        obj["Body"].close()

    process.wait()
    if writer_error is not None:
        raise RuntimeError(f"ffmpeg pipe write failed for key: {s3_location}") from writer_error
    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg failed for key: {s3_location}")

    return np.frombuffer(bytes(pcm_bytes), np.float32)
