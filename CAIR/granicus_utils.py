"""
Granicus websites are characterized by a URL like:

https://tracy-ca.granicus.com/player/camera/2?publish_id=8&redirect=true
https://sacramento.granicus.com/viewpublisher.php?view_id=22

"""

import time
import re
from typing import Dict, List, Tuple
from html import unescape
from urllib.parse import urljoin, urlparse

import diskcache
import requests
from bs4 import BeautifulSoup
from random_user_agent.params import OperatingSystem, SoftwareName
from random_user_agent.user_agent import UserAgent
from tqdm import tqdm

cache_channel = diskcache.Cache("cache/granicus/channel")
# expire_time = 7 * 60 * 60 * 24


class Granicus:

    SLEEP_TIME: float = 0.25

    def __init__(
        self,
        homepage_url: str,
    ):

        self.homepage_url = homepage_url
        self.url = self._parse_homepage(homepage_url)

        self.valid_page_idx = set()

        self.session = requests.Session()
        software_names = [
            SoftwareName.CHROME.value,
            SoftwareName.FIREFOX.value,
            SoftwareName.SAFARI.value,
        ]
        operating_systems = [
            OperatingSystem.WINDOWS.value,
            OperatingSystem.LINUX.value,
            OperatingSystem.MAC.value,
        ]
        user_agent_rotator = UserAgent(
            software_names=software_names,
            operating_systems=operating_systems,
            limit=100,
        )
        self.user_agent = user_agent_rotator.get_random_user_agent()
        self.session.headers.update({"User-Agent": self.user_agent})

    def _parse_homepage(self, homepage_url: str) -> str:
        if not homepage_url or not isinstance(homepage_url, str):
            raise ValueError("homepage_url must be a non-empty string.")

        url = homepage_url.strip()
        parsed = urlparse(url)
        if not parsed.scheme:
            parsed = urlparse(f"https://{url}")

        if not parsed.netloc:
            raise ValueError(f"Invalid Granicus homepage URL: {homepage_url}")

        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]

        if not host.endswith("granicus.com"):
            raise ValueError(f"Not a Granicus domain, trying running find_viewpublisher_url against this url: {homepage_url}")

        self.host = host
        self.base_url = f"{parsed.scheme or 'https'}://{host}"
        return self.base_url

    def _scan_id(self, idx):

        key = (self.url, idx)
        if key in cache_channel:
            return cache_channel[key]

        r = self.session.get(
            f"{self.url}/viewpublisher.php",
            params={"view_id": idx},
        )

        result = {
            "id": idx,
            "payload": None,
        }

        result["status_code"] = r.status_code
        result["is_ok"] = r.ok
        time.sleep(self.SLEEP_TIME)

        if not r.ok:
            if r.status_code in [404, 403]:
                pass
            else:
                raise ValueError(f"Failed with {r.status_code}")
        else:
            result["payload"] = r.content

        print(f"{r.url} {r.status_code}")
        cache_channel[key] = result
        return result

    def scan_view_ids(self, start: int = 1, end: int = 120):
        for i in tqdm(range(start, end + 1)):
            result = self._scan_id(i)

            if result["is_ok"]:
                self.valid_page_idx.add(i)

    def _get_homepage_html(self) -> str:
        key = ("Granicus._get_homepage_html", self.homepage_url)
        cached = cache_channel.get(key, default=None)
        if cached is not None:
            return cached

        print(f"Downloading Granicus URL (cache miss): {self.homepage_url}")
        response = self.session.get(self.homepage_url)
        response.raise_for_status()
        html = response.text
        cache_channel[key] = html
        return html

    @property
    def title(self):
        html = self._get_homepage_html()
        match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        return _clean_html_text(match.group(1))

    @property
    def description(self):
        html = self._get_homepage_html()
        return _extract_text_by_id(html, "intro")

    @property
    def rss(self):
        html = self._get_homepage_html()
        return _extract_href_by_id(html, "RSS")

    def build_info(self):
        return {
            "channel_id": self.homepage_url,
            "homepage_url": self.homepage_url,
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "rss": self.rss,
        }

    def get_uploads(self):
        # Cache parsed uploads for this page URL to avoid re-parsing on repeat calls.
        key = ("Granicus.get_uploads", self.homepage_url)
        cached = cache_channel.get(key, default=None)
        if cached is not None:
            return cached

        # Reuse homepage HTML fetch/caching logic used by title/description/rss.
        html = self._get_homepage_html()
        # Parse the DOM with BeautifulSoup so we can robustly inspect table rows/cells.
        soup = BeautifulSoup(html, "html.parser")
        # Granicus pages generally store one meeting/video item per <tr>.
        rows = soup.find_all("tr")

        uploads = []
        for row in rows:
            # Convert one table row into the normalized upload mapping.
            parsed = _parse_upload_row(row, self.base_url)
            if parsed is not None:
                uploads.append(parsed)

        # Persist parsed result so future calls are immediate.
        cache_channel[key] = uploads
        return uploads


def _is_viewpublisher_path(path: str) -> bool:
    if not path:
        return False

    normalized = path.lower().rstrip("/")
    return normalized.endswith("viewpublisher.php")


def _clean_html_text(value: str) -> str:
    if value is None:
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_text_by_id(html: str, element_id: str):
    pattern = (
        r"<(?P<tag>[a-zA-Z0-9:_-]+)[^>]*\bid\s*=\s*['\"]"
        + re.escape(element_id)
        + r"""['"][^>]*>(?P<content>.*?)</(?P=tag)>"""
    )
    match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return _clean_html_text(match.group("content"))


def _extract_href_by_id(html: str, element_id: str):
    open_tag_pattern = (
        r"<[a-zA-Z0-9:_-]+[^>]*\bid\s*=\s*['\"]"
        + re.escape(element_id)
        + r"""['"][^>]*>"""
    )
    open_tag_match = re.search(open_tag_pattern, html, flags=re.IGNORECASE | re.DOTALL)
    if not open_tag_match:
        return None

    open_tag = open_tag_match.group(0)
    href_match = re.search(r"""href\s*=\s*['"]([^'"]+)['"]""", open_tag, flags=re.IGNORECASE)
    if not href_match:
        return None
    return href_match.group(1).strip()


def _normalize_candidate_url(candidate: str, source_url: str) -> str:
    value = candidate.strip().strip("\"'()[]{}<>")
    if not value:
        return ""

    parsed = urlparse(value)
    if not parsed.scheme:
        value = urljoin(source_url, value)
        parsed = urlparse(value)

    if not parsed.scheme or not parsed.netloc:
        return ""

    if not _is_viewpublisher_path(parsed.path):
        return ""

    return value


def _clean_cell_text(value: str) -> str:
    # Normalize HTML-decoded text so all spacing is single-space and trimmed.
    if value is None:
        return ""
    text = unescape(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_link(href: str, base_url: str):
    # Turn raw href values into absolute URLs where possible.
    if not href:
        return None
    value = href.strip()
    if not value:
        return None
    # Protocol-relative URL: //host/path -> https://host/path (or page scheme).
    if value.startswith("//"):
        parsed_base = urlparse(base_url)
        scheme = parsed_base.scheme or "https"
        return f"{scheme}:{value}"
    # Handle relative URLs such as /AgendaViewer.php?... against the channel base URL.
    return urljoin(base_url, value)


def _extract_window_open_url(value: str):
    # Many Granicus "Watch" links use javascript window.open('...MediaPlayer.php...')
    # instead of a direct href. Pull the opened URL out so we can track it.
    if not value:
        return None
    match = re.search(r"""window\.open\(\s*['"]([^'"]+)['"]""", value, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def _is_downloadable_media_url(url: str) -> bool:
    # Treat common downloadable/streamable media extensions as media IDs.
    if not url:
        return False
    media_exts = (
        ".mp3",
        ".mp4",
        ".m4a",
        ".wav",
        ".aac",
        ".webm",
        ".ogg",
        ".asx",
        ".m3u8",
    )
    parsed = urlparse(url.lower())
    return parsed.path.endswith(media_exts)


def _parse_upload_row(row, base_url: str):
    # Each meeting entry is expected to be table cells inside one <tr>.
    cells = row.find_all("td")
    if not cells:
        return None

    # Output shape requested by caller.
    title = None
    published_at = None
    duration = None
    video_id = None
    # Catch-all for links like Agenda, Minutes, Briefs, etc.
    additional_items = {}
    # Collect media-like links and pick the best one at the end.
    media_candidates = []

    for cell in cells:
        # BeautifulSoup may return `headers` as list or string depending on parser behavior.
        # Normalize both to one lowercase string for consistent matching.
        headers_attr = cell.get("headers")
        if isinstance(headers_attr, list):
            headers = " ".join(headers_attr).lower()
        else:
            headers = (headers_attr or "").lower()
        # Normalize class names for simple case-insensitive checks.
        class_names = [c.lower() for c in (cell.get("class") or [])]
        # Flatten cell text, resolving entities like &nbsp; and collapsing whitespace.
        cell_text = _clean_cell_text(cell.get_text(" ", strip=True))
        # Link tags often carry agenda/minutes/media URLs.
        links = cell.find_all("a")

        # Title is usually in the Name column.
        if title is None and ("name" in headers or "listitem" in class_names):
            if cell_text:
                title = cell_text

        # Published date is usually in a Date column/header.
        if published_at is None and "date" in headers:
            if cell_text:
                published_at = cell_text

        # Duration is usually explicit via header/class naming.
        if duration is None and ("duration" in headers or "duration" in class_names):
            if cell_text:
                duration = cell_text

        for link in links:
            # Granicus uses a mix of direct href links and javascript onclick handlers.
            href = link.get("href") or ""
            on_click = link.get("onclick") or link.get("onClick") or ""
            link_text = _clean_cell_text(link.get_text(" ", strip=True))

            normalized_href = _normalize_link(href, base_url)
            # Ignore javascript pseudo-hrefs here; they are handled via onclick parsing below.
            if normalized_href and not href.lower().startswith("javascript:"):
                # Direct media URL (mp3/mp4/etc): candidate for video_id.
                if _is_downloadable_media_url(normalized_href):
                    media_candidates.append(normalized_href)
                else:
                    # Non-media link goes into additional_items (Agenda, Minutes, Briefs, ...).
                    additional_items[link_text or normalized_href] = normalized_href

            # Parse window.open(...) links, commonly used for MediaPlayer pages.
            opened = _extract_window_open_url(on_click)
            normalized_opened = _normalize_link(opened, base_url)
            if normalized_opened:
                # MediaPlayer URL is still a valid media reference if no direct mp4/mp3 exists.
                if "mediaplayer.php" in normalized_opened.lower():
                    media_candidates.append(normalized_opened)
                else:
                    additional_items[link_text or normalized_opened] = normalized_opened

    # Skip rows that do not resemble meeting/video records.
    if not title and not media_candidates and not additional_items:
        return None

    # Prefer downloadable media URLs over player pages when both are present.
    if media_candidates:
        downloadable = [u for u in media_candidates if _is_downloadable_media_url(u)]
        if downloadable:
            video_id = downloadable[0]
        else:
            video_id = media_candidates[0]

    # Final normalized record for this row.
    return {
        "title": title,
        "publishedAt": published_at,
        "Duration": duration,
        "video_id": video_id,
        "additional_items": additional_items,
    }


def find_viewpublisher_url(url: str, timeout: float = 15.0) -> str:
    """
    Return the first URL that points to ViewPublisher.php.

    The URL match is case-insensitive and supports query parameters.
    If the provided URL is already a ViewPublisher.php URL, it is returned.
    Returns an empty string when no match is found.
    """
    if not url or not isinstance(url, str):
        raise ValueError("url must be a non-empty string")

    direct_match = _normalize_candidate_url(url, url)
    if direct_match:
        return direct_match

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    html = response.text

    matches = re.findall(r"""https?://[^\s"'<>]+|/[^\s"'<>]*viewpublisher\.php[^\s"'<>]*""", html, flags=re.IGNORECASE)
    for candidate in matches:
        normalized = _normalize_candidate_url(candidate, response.url)
        if normalized:
            return normalized

    return ""
