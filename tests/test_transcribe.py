import numpy as np
import pandas as pd

from CAIR.transcribe import Transcription, post_process_transcription_result


def _fake_whisper_result():
    return {
        "segments": [
            {"start": 0.0, "end": 1.0, "text": "  hello "},
            {"start": 1.0, "end": 2.5, "text": " world  "},
        ]
    }


def test_post_process_transcription_result_text_and_dataframe():
    result = _fake_whisper_result()

    text = post_process_transcription_result(result, text_only=True)
    assert text == "hello\nworld"

    df = post_process_transcription_result(result, text_only=False)
    assert list(df.columns) == ["start", "end", "text"]
    assert df["text"].tolist() == ["hello", "world"]


def test_transcribe_s3_streams_and_caches(monkeypatch):
    audio = np.array([0.1, -0.2, 0.3], dtype=np.float32)
    state = {"s3_calls": 0, "compute_calls": 0}

    def fake_s3_loader(s3_location):
        assert s3_location == "s3://bucket/example.wav"
        state["s3_calls"] += 1
        return audio

    def fake_compute(f_audio):
        state["compute_calls"] += 1
        assert np.array_equal(f_audio, audio)
        return _fake_whisper_result()

    monkeypatch.setattr("CAIR.transcribe.s3_location_to_audio_numpy", fake_s3_loader)

    t = Transcription(method="whisper")
    t.compute_method_call = fake_compute

    text_1 = t.transcribe_s3("s3://bucket/example.wav", text_only=True)
    text_2 = t.transcribe_s3("s3://bucket/example.wav", text_only=True)
    df = t.transcribe_s3("s3://bucket/example.wav", text_only=False)

    assert text_1 == "hello\nworld"
    assert text_2 == "hello\nworld"
    assert isinstance(df, pd.DataFrame)
    assert df["text"].tolist() == ["hello", "world"]

    # Ensure the S3 fetch + model compute path is cached by S3 URI.
    assert state["s3_calls"] == 1
    assert state["compute_calls"] == 1
