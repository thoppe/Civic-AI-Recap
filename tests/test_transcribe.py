import numpy as np
import pandas as pd
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import CAIR.transcribe as repo_transcribe

Transcription = repo_transcribe.Transcription
post_process_transcription_result = repo_transcribe.post_process_transcription_result
_compute_vad_overlap_flags = repo_transcribe._compute_vad_overlap_flags


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

    def fake_compute(f_audio, force=None):
        state["compute_calls"] += 1
        assert force is False
        assert np.array_equal(f_audio, audio)
        return _fake_whisper_result()

    monkeypatch.setattr("CAIR.transcribe.s3_location_to_audio_numpy", fake_s3_loader)

    t = Transcription(method="whisper")
    t.cache.clear()
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


def test_transcribe_force_does_not_recompute_vad_when_result_has_vad():
    state = {"vad_calls": 0}
    vad_segments = [{"start": 0.0, "end": 1.0}]

    t = Transcription(method="whisper", compute_vad=True)
    t.cache.clear()
    t.vad_cache.clear()

    def fake_get_vad_segments(f_audio, force=None, cache_key=None):
        del f_audio, force, cache_key
        state["vad_calls"] += 1
        return vad_segments

    def fake_compute(f_audio, force=None):
        return {
            "segments": [
                {"start": 0.0, "end": 1.0, "text": "hello"},
            ],
            "VAD": fake_get_vad_segments(f_audio, force=force),
        }

    t.get_vad_segments = fake_get_vad_segments
    t.compute_method_call = fake_compute

    df = t.transcribe("example.wav", text_only=False, force=True)

    assert df["is_vad"].tolist() == [True]
    assert state["vad_calls"] == 1


def test_transcribe_s3_force_does_not_recompute_vad_when_result_has_vad(
    monkeypatch,
):
    audio = np.array([0.1, -0.2, 0.3], dtype=np.float32)
    state = {"vad_calls": 0, "s3_calls": 0}
    vad_segments = [{"start": 0.0, "end": 1.0}]

    def fake_s3_loader(s3_location):
        assert s3_location == "s3://bucket/example.wav"
        state["s3_calls"] += 1
        return audio

    monkeypatch.setattr("CAIR.transcribe.s3_location_to_audio_numpy", fake_s3_loader)

    t = Transcription(method="whisper", compute_vad=True)
    t.cache.clear()
    t.vad_cache.clear()

    def fake_get_vad_segments(f_audio, force=None, cache_key=None):
        del f_audio, force, cache_key
        state["vad_calls"] += 1
        return vad_segments

    def fake_compute(f_audio, force=None):
        assert np.array_equal(f_audio, audio)
        return {
            "segments": [
                {"start": 0.0, "end": 1.0, "text": "hello"},
            ],
            "VAD": fake_get_vad_segments(f_audio, force=force),
        }

    t.get_vad_segments = fake_get_vad_segments
    t.compute_method_call = fake_compute

    df = t.transcribe_s3(
        "s3://bucket/example.wav",
        text_only=False,
        force=True,
    )

    assert df["is_vad"].tolist() == [True]
    assert state["vad_calls"] == 1
    assert state["s3_calls"] == 1


def test_compute_vad_overlap_flags_boundary_semantics():
    flags = _compute_vad_overlap_flags(
        segment_starts=np.array([0.0, 1.0, 2.0, 3.0]),
        segment_ends=np.array([1.0, 2.0, 3.0, 4.0]),
        vad_starts=np.array([1.0]),
        vad_ends=np.array([2.0]),
    )

    assert flags.tolist() == [False, True, False, False]


def test_compute_vad_overlap_flags_multiple_intervals():
    flags = _compute_vad_overlap_flags(
        segment_starts=np.array([0.0, 1.4, 2.2, 4.0]),
        segment_ends=np.array([0.8, 2.0, 3.0, 4.5]),
        vad_starts=np.array([0.5, 2.5, 5.0]),
        vad_ends=np.array([0.9, 2.7, 5.5]),
    )

    assert flags.tolist() == [True, False, True, False]


def test_post_process_transcription_result_with_vad_overlap_flags():
    result = {
        "segments": [
            {"start": 0.0, "end": 1.0, "text": " a "},
            {"start": 1.0, "end": 2.0, "text": " b "},
            {"start": 2.0, "end": 3.0, "text": " c "},
            {"start": 3.0, "end": 4.0, "text": " d "},
        ],
        "VAD": [
            {"start": 0.2, "end": 0.8},
            {"start": 1.0, "end": 2.0},
            {"start": 3.8, "end": 4.2},
        ],
    }

    df = post_process_transcription_result(
        result,
        text_only=False,
        vad_filter=True,
    )

    assert df["text"].tolist() == ["a", "b", "c", "d"]
    assert df["is_vad"].tolist() == [True, True, False, True]
