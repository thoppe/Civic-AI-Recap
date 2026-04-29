from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import parse_qs, urljoin, urlparse

import requests

_VIDEO_URL_RE = re.compile(r'video_url\s*=\s*"([^"]+)"')
_BANDWIDTH_RE = re.compile(r"BANDWIDTH=(\d+)")


@dataclass(frozen=True)
class GranicusResolvedVideo:
    input_url: str
    player_page_url: str
    playlist_url: str
    media_playlist_url: str
    mp4_url: str | None


@dataclass(frozen=True)
class GranicusDownloadResult:
    input_url: str
    view_id: str
    clip_id: str
    media_playlist_url: str
    output_path: Path
    ffmpeg_command: tuple[str, ...]


def resolve_granicus_video_url(url: str, timeout: int = 30) -> GranicusResolvedVideo:
    player_response = requests.get(url, timeout=timeout)
    player_response.raise_for_status()

    playlist_url = _extract_playlist_url(player_response.text, player_response.url)

    playlist_response = requests.get(playlist_url, timeout=timeout)
    playlist_response.raise_for_status()

    return GranicusResolvedVideo(
        input_url=url,
        player_page_url=str(player_response.url),
        playlist_url=playlist_url,
        media_playlist_url=_resolve_media_playlist_url(
            playlist_response.text,
            playlist_url,
        ),
        mp4_url=_derive_mp4_url(playlist_url),
    )


def download_granicus_video(
    url: str,
    output_dir: str | Path = ".",
    *,
    download_path: str | Path | None = None,
    output_path: str | Path | None = None,
    ffmpeg_path: str | None = None,
    overwrite: bool = False,
    timeout: int = 30,
) -> GranicusDownloadResult:
    view_id, clip_id = validate_granicus_media_player_url(url)
    resolved = resolve_granicus_video_url(url, timeout=timeout)
    destination = _determine_output_path(
        url, clip_id, output_dir, download_path, output_path
    )

    if destination.exists() and not overwrite:
        raise FileExistsError(
            f"Refusing to overwrite existing file: {destination}. "
            "Pass overwrite=True to replace it."
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_binary = ffmpeg_path or shutil.which("ffmpeg")
    if not ffmpeg_binary:
        raise RuntimeError(
            "ffmpeg is required to download Granicus videos. "
            "Install ffmpeg or pass ffmpeg_path explicitly."
        )

    command = (
        ffmpeg_binary,
        "-y" if overwrite else "-n",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-i",
        resolved.media_playlist_url,
        "-c",
        "copy",
        str(destination),
    )
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"ffmpeg exited with status {completed.returncode}")

    return GranicusDownloadResult(
        input_url=url,
        view_id=view_id,
        clip_id=clip_id,
        media_playlist_url=resolved.media_playlist_url,
        output_path=destination,
        ffmpeg_command=command,
    )


def validate_granicus_media_player_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Granicus MediaPlayer URLs must use http or https.")
    if not parsed.netloc.endswith("granicus.com"):
        raise ValueError("URL host must be a granicus.com domain.")
    if not parsed.path.endswith("/MediaPlayer.php"):
        raise ValueError("URL path must end with /MediaPlayer.php.")

    query = parse_qs(parsed.query)
    view_id = query.get("view_id", [""])[0]
    clip_id = query.get("clip_id", [""])[0]
    if not view_id:
        raise ValueError("Granicus MediaPlayer URL must include a non-empty view_id.")
    if not clip_id:
        raise ValueError("Granicus MediaPlayer URL must include a non-empty clip_id.")
    return view_id, clip_id


def _extract_playlist_url(html: str, player_page_url: str) -> str:
    match = _VIDEO_URL_RE.search(html)
    if not match:
        raise ValueError("No embedded video playlist URL found in Granicus player page.")
    return urljoin(player_page_url, match.group(1))


def _resolve_media_playlist_url(playlist_text: str, playlist_url: str) -> str:
    lines = [line.strip() for line in playlist_text.splitlines() if line.strip()]
    if any(line.startswith("#EXTINF") for line in lines):
        return playlist_url

    variants: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        if not line.startswith("#EXT-X-STREAM-INF"):
            continue
        bandwidth_match = _BANDWIDTH_RE.search(line)
        bandwidth = int(bandwidth_match.group(1)) if bandwidth_match else -1
        for next_line in lines[index + 1 :]:
            if next_line.startswith("#"):
                continue
            variants.append((bandwidth, urljoin(playlist_url, next_line)))
            break

    if not variants:
        raise ValueError("No media playlist entries found in Granicus playlist.")

    variants.sort(key=lambda item: item[0], reverse=True)
    return variants[0][1]


def _derive_mp4_url(playlist_url: str) -> str | None:
    if not playlist_url.endswith("/playlist.m3u8"):
        return None
    derived = playlist_url.removesuffix("/playlist.m3u8")
    if ".mp4" not in derived:
        return None
    return derived


def _determine_output_path(
    url: str,
    clip_id: str,
    output_dir: str | Path,
    download_path: str | Path | None,
    output_path: str | Path | None,
) -> Path:
    if download_path is not None:
        return Path(download_path)
    if output_path is not None:
        return Path(output_path)

    host = re.sub(r"[^a-z0-9]+", "_", urlparse(url).netloc.lower()).strip("_")
    return Path(output_dir) / f"{host}_clip_{clip_id}.mp4"
