from pathlib import Path
import subprocess

import pytest

from CAIR.granicus import (
    _resolve_media_playlist_url,
    download_granicus_video,
    resolve_granicus_video_url,
    validate_granicus_media_player_url,
)


class _FakeResponse:
    def __init__(self, url: str, text: str):
        self.url = url
        self.text = text

    def raise_for_status(self):
        return None


def test_resolve_granicus_video_url_uses_player_and_playlist_fixtures(monkeypatch):
    fixtures_root = Path("tests/fixtures/granicus")
    player_html = (fixtures_root / "loudoun_clip_1366_player.html").read_text()
    playlist_text = (fixtures_root / "loudoun_clip_1366_playlist.m3u8").read_text()

    input_url = "https://loudoun.granicus.com/MediaPlayer.php?view_id=92&clip_id=1366"
    redirected_url = (
        "https://loudoun.granicus.com/player/clip/1366?view_id=92&redirect=true"
    )
    playlist_url = (
        "https://archive-stream.granicus.com/OnDemand/_definst_/mp4:archive/loudoun/"
        "loudoun_eaa2025b-cb01-4ede-b444-79096c717e57.mp4/playlist.m3u8"
    )

    def fake_get(url: str, timeout: int = 30):
        if url == input_url:
            return _FakeResponse(redirected_url, player_html)
        if url == playlist_url:
            return _FakeResponse(playlist_url, playlist_text)
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr("CAIR.granicus.requests.get", fake_get)

    resolved = resolve_granicus_video_url(input_url)

    assert resolved.input_url == input_url
    assert resolved.player_page_url == redirected_url
    assert resolved.playlist_url == playlist_url
    assert resolved.media_playlist_url == (
        "https://archive-stream.granicus.com/OnDemand/_definst_/mp4:archive/loudoun/"
        "loudoun_eaa2025b-cb01-4ede-b444-79096c717e57.mp4/chunklist.m3u8"
    )
    assert resolved.mp4_url == (
        "https://archive-stream.granicus.com/OnDemand/_definst_/mp4:archive/loudoun/"
        "loudoun_eaa2025b-cb01-4ede-b444-79096c717e57.mp4"
    )


def test_resolve_media_playlist_url_accepts_media_playlist_fixture():
    fixtures_root = Path("tests/fixtures/granicus")
    chunklist_text = (fixtures_root / "loudoun_clip_1366_chunklist.m3u8").read_text()
    chunklist_url = (
        "https://archive-stream.granicus.com/OnDemand/_definst_/mp4:archive/loudoun/"
        "loudoun_eaa2025b-cb01-4ede-b444-79096c717e57.mp4/chunklist.m3u8"
    )

    assert _resolve_media_playlist_url(chunklist_text, chunklist_url) == chunklist_url


def test_validate_granicus_media_player_url_accepts_expected_shape():
    assert validate_granicus_media_player_url(
        "https://contra-costa.granicus.com/MediaPlayer.php?view_id=2&clip_id=3888"
    ) == ("2", "3888")


@pytest.mark.parametrize(
    ("url", "message"),
    [
        ("https://example.com/MediaPlayer.php?view_id=2&clip_id=3888", "granicus.com"),
        (
            "https://contra-costa.granicus.com/player/clip/3888?view_id=2",
            "/MediaPlayer.php",
        ),
        (
            "https://contra-costa.granicus.com/MediaPlayer.php?clip_id=3888",
            "view_id",
        ),
        (
            "https://contra-costa.granicus.com/MediaPlayer.php?view_id=2",
            "clip_id",
        ),
    ],
)
def test_validate_granicus_media_player_url_rejects_invalid_shape(url: str, message: str):
    with pytest.raises(ValueError, match=message):
        validate_granicus_media_player_url(url)


def test_download_granicus_video_uses_ffmpeg_with_media_playlist(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "CAIR.granicus.resolve_granicus_video_url",
        lambda url, timeout=30: type(
            "Resolved",
            (),
            {
                "media_playlist_url": "https://archive-stream.granicus.com/path/chunklist.m3u8",
            },
        )(),
    )
    monkeypatch.setattr("CAIR.granicus.shutil.which", lambda name: "/usr/bin/ffmpeg")

    recorded = {}

    def fake_run(command, check=False):
        recorded["command"] = command
        recorded["check"] = check
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("CAIR.granicus.subprocess.run", fake_run)

    result = download_granicus_video(
        "https://contra-costa.granicus.com/MediaPlayer.php?view_id=2&clip_id=3888",
        output_dir=tmp_path,
    )

    expected_path = tmp_path / "contra_costa_granicus_com_clip_3888.mp4"
    assert result.view_id == "2"
    assert result.clip_id == "3888"
    assert result.media_playlist_url == (
        "https://archive-stream.granicus.com/path/chunklist.m3u8"
    )
    assert result.output_path == expected_path
    assert recorded["command"] == (
        "/usr/bin/ffmpeg",
        "-n",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-i",
        "https://archive-stream.granicus.com/path/chunklist.m3u8",
        "-c",
        "copy",
        str(expected_path),
    )
    assert result.ffmpeg_command == recorded["command"]


def test_download_granicus_video_rejects_existing_file_without_overwrite(
    monkeypatch, tmp_path
):
    download_path = tmp_path / "existing.mp4"
    download_path.write_bytes(b"existing")

    monkeypatch.setattr(
        "CAIR.granicus.resolve_granicus_video_url",
        lambda url, timeout=30: type(
            "Resolved", (), {"media_playlist_url": "https://x/y.m3u8"}
        )(),
    )

    with pytest.raises(FileExistsError, match="overwrite=True"):
        download_granicus_video(
            "https://contra-costa.granicus.com/MediaPlayer.php?view_id=2&clip_id=3888",
            download_path=download_path,
        )


def test_download_granicus_video_requires_ffmpeg(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "CAIR.granicus.resolve_granicus_video_url",
        lambda url, timeout=30: type(
            "Resolved", (), {"media_playlist_url": "https://x/y.m3u8"}
        )(),
    )
    monkeypatch.setattr("CAIR.granicus.shutil.which", lambda name: None)

    with pytest.raises(RuntimeError, match="Install ffmpeg or pass ffmpeg_path explicitly"):
        download_granicus_video(
            "https://contra-costa.granicus.com/MediaPlayer.php?view_id=2&clip_id=3888",
            output_dir=tmp_path,
        )


def test_download_granicus_video_prefers_download_path_over_output_dir(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        "CAIR.granicus.resolve_granicus_video_url",
        lambda url, timeout=30: type(
            "Resolved", (), {"media_playlist_url": "https://x/y.m3u8"}
        )(),
    )
    monkeypatch.setattr("CAIR.granicus.shutil.which", lambda name: "/usr/bin/ffmpeg")

    recorded = {}

    def fake_run(command, check=False):
        recorded["command"] = command
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("CAIR.granicus.subprocess.run", fake_run)

    download_path = tmp_path / "custom-name.mp4"
    result = download_granicus_video(
        "https://contra-costa.granicus.com/MediaPlayer.php?view_id=2&clip_id=3888",
        output_dir=tmp_path / "ignored-dir",
        download_path=download_path,
    )

    assert result.output_path == download_path
    assert recorded["command"][-1] == str(download_path)
