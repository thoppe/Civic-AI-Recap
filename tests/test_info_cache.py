import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import diskcache

from CAIR import info


class DummyProgressBar:
    def update(self, _n=1):
        return None

    def close(self):
        return None


class FakeRequest:
    def __init__(self, parent, key, response):
        self.parent = parent
        self.key = key
        self.response = response

    def execute(self):
        self.parent.execute_counts[self.key] += 1
        return self.response


class FakeSearchAPI:
    def __init__(self, parent):
        self.parent = parent

    def list(self, **kwargs):
        self.parent.last_search_kwargs = kwargs
        q = kwargs["q"]
        items = [{"snippet": {"query": q}}]
        return FakeRequest(self.parent, "search.list", {"items": items})


class FakeVideosAPI:
    def __init__(self, parent):
        self.parent = parent

    def list(self, **kwargs):
        video_id = kwargs["id"]
        response = {
            "items": [
                {
                    "snippet": {
                        "channelId": "channel-1",
                        "title": f"title-{video_id}",
                        "description": "desc",
                        "publishedAt": "2024-01-01T00:00:00Z",
                    },
                    "contentDetails": {"duration": "PT1M2S"},
                    "statistics": {},
                }
            ]
        }
        return FakeRequest(self.parent, "videos.list", response)


class FakeCaptionsAPI:
    def __init__(self, parent):
        self.parent = parent

    def list(self, **kwargs):
        _ = kwargs["videoId"]
        response = {
            "items": [{"id": "cap-1", "snippet": {"language": "en", "trackKind": "asr"}}]
        }
        return FakeRequest(self.parent, "captions.list", response)

    def download(self, **kwargs):
        self.parent.last_caption_download_kwargs = kwargs
        return FakeRequest(self.parent, "captions.download", {"status": "ok"})


class FakeChannelsAPI:
    def __init__(self, parent):
        self.parent = parent

    def list(self, **kwargs):
        part = kwargs.get("part", "")
        if part == "contentDetails":
            response = {
                "items": [
                    {"contentDetails": {"relatedPlaylists": {"uploads": "uploads-1"}}}
                ]
            }
            return FakeRequest(self.parent, "channels.uploads", response)

        response = {
            "items": [
                {
                    "snippet": {
                        "title": "Channel Title",
                        "description": "Channel Description",
                        "customUrl": "@channel",
                        "publishedAt": "2024-01-01T00:00:00Z",
                    },
                    "statistics": {
                        "videoCount": "60",
                        "viewCount": "1200",
                        "subscriberCount": "33",
                    },
                    "contentDetails": {},
                }
            ]
        }
        return FakeRequest(self.parent, "channels.metadata", response)


class FakePlaylistItemsAPI:
    def __init__(self, parent):
        self.parent = parent

    def list(self, **kwargs):
        self.parent.last_playlist_kwargs = kwargs
        _ = kwargs["playlistId"]
        response = {
            "items": [
                {
                    "snippet": {
                        "resourceId": {"videoId": "v1"},
                        "title": "Video One",
                        "publishedAt": "2024-01-02T00:00:00Z",
                    }
                }
            ]
        }
        return FakeRequest(self.parent, "playlistItems.list", response)


class FakeYouTubeClient:
    def __init__(self):
        self.execute_counts = {
            "search.list": 0,
            "videos.list": 0,
            "captions.list": 0,
            "captions.download": 0,
            "channels.metadata": 0,
            "channels.uploads": 0,
            "playlistItems.list": 0,
        }
        self.last_search_kwargs = None
        self.last_caption_download_kwargs = None
        self.last_playlist_kwargs = None

    def search(self):
        return FakeSearchAPI(self)

    def videos(self):
        return FakeVideosAPI(self)

    def captions(self):
        return FakeCaptionsAPI(self)

    def channels(self):
        return FakeChannelsAPI(self)

    def playlistItems(self):
        return FakePlaylistItemsAPI(self)


class FakeYoutubeDL:
    calls = 0

    def __init__(self, _opts):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def extract_info(self, url, download=False):
        FakeYoutubeDL.calls += 1
        return {"url": url, "download": download}

    def sanitize_info(self, payload):
        return payload


class TestInfoCaching(unittest.TestCase):
    def setUp(self):
        self.temp_root = tempfile.TemporaryDirectory()
        self.fake_client = FakeYouTubeClient()
        FakeYoutubeDL.calls = 0

        self.original_cache_video = info.cache_video
        self.original_cache_channel = info.cache_channel
        self.original_cache_search = info.cache_search

        cache_root = Path(self.temp_root.name)
        info.cache_video = diskcache.Cache(str(cache_root / "video"))
        info.cache_channel = diskcache.Cache(str(cache_root / "channel"))
        info.cache_search = diskcache.Cache(str(cache_root / "search"))

        self.p_get_client = patch.object(
            info, "get_youtube_client", return_value=self.fake_client
        )
        self.p_tqdm = patch.object(info, "tqdm", side_effect=lambda *args, **kwargs: DummyProgressBar())
        self.p_ydl = patch.object(info.yt_dlp, "YoutubeDL", FakeYoutubeDL)

        self.p_get_client.start()
        self.p_tqdm.start()
        self.p_ydl.start()

    def tearDown(self):
        self.p_ydl.stop()
        self.p_tqdm.stop()
        self.p_get_client.stop()

        info.cache_video.close()
        info.cache_channel.close()
        info.cache_search.close()

        info.cache_video = self.original_cache_video
        info.cache_channel = self.original_cache_channel
        info.cache_search = self.original_cache_search

        self.temp_root.cleanup()

    def _assert_ttl_close(self, cache, key, expected_ttl, tolerance=5):
        cached_value, expire_at = cache.get(key, expire_time=True)
        self.assertIsNotNone(cached_value)
        remaining = expire_at - time.time()
        self.assertLessEqual(abs(remaining - expected_ttl), tolerance)

    def test_search_default_expire_and_cache_hit(self):
        search = info.Search()
        result_1 = search("cities", max_results=25)
        result_2 = search("cities", max_results=25)

        self.assertEqual(result_1, result_2)
        self.assertEqual(self.fake_client.execute_counts["search.list"], 1)
        key = ("Search.__call__", "cities", 25, "video", "any")
        self._assert_ttl_close(info.cache_search, key, info.DEFAULT_EXPIRE_TIME)

    def test_video_custom_expire_across_methods(self):
        ttl = 30
        video = info.Video("video-1", expire_time=ttl)

        video.get_caption_list()
        video.get_caption_list()
        video.get_metadata()
        video.get_metadata()
        video.get_extended_metadata()
        video.get_extended_metadata()

        self.assertEqual(self.fake_client.execute_counts["captions.list"], 1)
        self.assertEqual(self.fake_client.execute_counts["videos.list"], 1)
        self.assertEqual(FakeYoutubeDL.calls, 1)

        self._assert_ttl_close(
            info.cache_video, ("Video.get_caption_list", "video-1"), ttl, tolerance=3
        )
        self._assert_ttl_close(
            info.cache_video, ("Video.get_metadata", "video-1"), ttl, tolerance=3
        )
        self._assert_ttl_close(
            info.cache_video, ("Video.get_extended_metadata", "video-1"), ttl, tolerance=3
        )

    def test_channel_default_expire_across_methods(self):
        channel = info.Channel("channel-1")

        _ = channel.get_metadata()
        _ = channel.get_metadata()
        _ = channel.upload_playlist_id
        _ = channel.upload_playlist_id
        uploads_1 = channel.get_uploads()
        uploads_2 = channel.get_uploads()

        self.assertEqual(self.fake_client.execute_counts["channels.metadata"], 1)
        self.assertEqual(self.fake_client.execute_counts["channels.uploads"], 1)
        self.assertEqual(self.fake_client.execute_counts["playlistItems.list"], 1)
        self.assertEqual(len(uploads_1), len(uploads_2))

        self._assert_ttl_close(
            info.cache_channel,
            ("Channel.get_metadata", "channel-1"),
            info.DEFAULT_EXPIRE_TIME,
        )
        self._assert_ttl_close(
            info.cache_channel,
            ("Channel.upload_playlist_id", "channel-1"),
            info.DEFAULT_EXPIRE_TIME,
        )
        self._assert_ttl_close(
            info.cache_channel,
            ("Channel.get_uploads", "channel-1"),
            info.DEFAULT_EXPIRE_TIME,
        )

    def test_search_collects_multiple_pages_and_respects_max_results(self):
        class PagedSearchAPI:
            def __init__(self, parent):
                self.parent = parent

            def list(self, **kwargs):
                self.parent.last_search_kwargs = kwargs
                token = kwargs.get("pageToken")
                if token is None:
                    response = {
                        "items": [
                            {"snippet": {"query": kwargs["q"], "idx": 1}},
                            {"snippet": {"query": kwargs["q"], "idx": 2}},
                        ],
                        "nextPageToken": "PAGE-2",
                    }
                else:
                    response = {
                        "items": [
                            {"snippet": {"query": kwargs["q"], "idx": 3}},
                            {"snippet": {"query": kwargs["q"], "idx": 4}},
                        ]
                    }
                return FakeRequest(self.parent, "search.list", response)

        self.fake_client.search = lambda: PagedSearchAPI(self.fake_client)

        search = info.Search()
        result = search("cities", max_results=3)

        self.assertEqual(self.fake_client.execute_counts["search.list"], 2)
        self.assertEqual(len(result), 3)
        self.assertEqual([row["idx"] for row in result], [1, 2, 3])

    def test_search_forwards_expected_arguments(self):
        search = info.Search()
        _ = search("policy", max_results=25, v_type="video", duration="short")
        kwargs = self.fake_client.last_search_kwargs
        self.assertIsNotNone(kwargs)
        self.assertEqual(kwargs["q"], "policy")
        self.assertEqual(kwargs["maxResults"], 25)
        self.assertEqual(kwargs["type"], "video")
        self.assertEqual(kwargs["videoDuration"], "short")
        self.assertEqual(kwargs["eventType"], "completed")

    def test_video_properties_and_build_info_mapping(self):
        video = info.Video("video-1")

        self.assertEqual(video.channel_id, "channel-1")
        self.assertEqual(video.title, "title-video-1")
        self.assertEqual(video.description, "desc")
        self.assertEqual(video.published_at, "2024-01-01T00:00:00Z")
        self.assertEqual(video.duration, 62)

        built = video.build_info()
        self.assertEqual(
            set(built.keys()),
            {"video_id", "description", "published_at", "title", "duration", "channel_id"},
        )
        self.assertEqual(built["video_id"], "video-1")
        self.assertEqual(built["duration"], 62)
        self.assertEqual(built["channel_id"], "channel-1")

    def test_download_english_captions_downloads_asr_track(self):
        video = info.Video("video-1")
        video.download_english_captions()
        self.assertEqual(self.fake_client.execute_counts["captions.list"], 1)
        self.assertEqual(self.fake_client.execute_counts["captions.download"], 1)
        self.assertEqual(
            self.fake_client.last_caption_download_kwargs, {"id": "cap-1", "tfmt": "srt"}
        )

    def test_download_english_captions_raises_when_asr_english_missing(self):
        class NoEnglishAsrCaptionsAPI(FakeCaptionsAPI):
            def list(self, **kwargs):
                _ = kwargs["videoId"]
                response = {
                    "items": [
                        {"id": "cap-2", "snippet": {"language": "en", "trackKind": "standard"}},
                        {"id": "cap-3", "snippet": {"language": "es", "trackKind": "asr"}},
                    ]
                }
                return FakeRequest(self.parent, "captions.list", response)

        self.fake_client.captions = lambda: NoEnglishAsrCaptionsAPI(self.fake_client)
        video = info.Video("video-1")
        with self.assertRaises(ValueError):
            video.download_english_captions()

    def test_download_audio_omits_js_runtimes_by_default(self):
        video = info.Video("video-1")
        f_audio = Path(self.temp_root.name) / "audio.mp3"
        with patch.object(info.subprocess, "call") as mock_call:
            video.download_audio(f_audio)
        cmd = mock_call.call_args[0][0]
        self.assertNotIn("--js-runtimes", cmd)
        self.assertIn("yt-dlp", cmd)
        self.assertIn(video.URL, cmd)

    def test_download_audio_passes_js_runtimes_when_provided(self):
        video = info.Video("video-1")
        f_audio = Path(self.temp_root.name) / "audio.mp3"
        js_runtimes = "node:/usr/bin/node"
        with patch.object(info.subprocess, "call") as mock_call:
            video.download_audio(f_audio, js_runtimes=js_runtimes)
        cmd = mock_call.call_args[0][0]
        self.assertIn("--js-runtimes", cmd)
        self.assertIn(js_runtimes, cmd)
        self.assertIn(video.URL, cmd)

    def test_channel_stats_are_ints_and_build_info_schema(self):
        channel = info.Channel("channel-1")
        self.assertEqual(channel.n_videos, 60)
        self.assertEqual(channel.n_views, 1200)
        self.assertEqual(channel.n_subscribers, 33)
        self.assertIsInstance(channel.n_videos, int)
        self.assertIsInstance(channel.n_views, int)
        self.assertIsInstance(channel.n_subscribers, int)

        built = channel.build_info()
        self.assertEqual(
            set(built.keys()),
            {
                "channel_id",
                "description",
                "title",
                "published_at",
                "custom_url",
                "n_videos",
                "n_subscribers",
                "n_views",
            },
        )
        self.assertEqual(built["channel_id"], "channel-1")

    def test_channel_upload_playlist_id_extraction(self):
        channel = info.Channel("channel-1")
        self.assertEqual(channel.upload_playlist_id, "uploads-1")

    def test_channel_get_uploads_dataframe_shape(self):
        channel = info.Channel("channel-1")
        df = channel.get_uploads()
        self.assertEqual(list(df.columns), ["video_id", "title", "publishedAt", "channel_id"])
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["video_id"], "v1")
        self.assertTrue((df["channel_id"] == "channel-1").all())

    def test_channel_get_uploads_forwards_playlist_request_args(self):
        channel = info.Channel("channel-1")
        _ = channel.get_uploads()
        kwargs = self.fake_client.last_playlist_kwargs
        self.assertIsNotNone(kwargs)
        self.assertEqual(kwargs["playlistId"], "uploads-1")
        self.assertEqual(kwargs["part"], "snippet")
        self.assertEqual(kwargs["maxResults"], 50)

    def test_search_caps_results_to_max_results(self):
        class PagedSearchAPI:
            def __init__(self, parent):
                self.parent = parent

            def list(self, **kwargs):
                token = kwargs.get("pageToken")
                if token is None:
                    response = {
                        "items": [
                            {"snippet": {"idx": 1}},
                            {"snippet": {"idx": 2}},
                        ],
                        "nextPageToken": "PAGE-2",
                    }
                else:
                    response = {
                        "items": [
                            {"snippet": {"idx": 3}},
                            {"snippet": {"idx": 4}},
                        ]
                    }
                return FakeRequest(self.parent, "search.list", response)

        self.fake_client.search = lambda: PagedSearchAPI(self.fake_client)
        search = info.Search()
        result = search("cities", max_results=3)
        self.assertEqual(len(result), 3)

    def test_search_uses_youtube_safe_max_results_per_request(self):
        search = info.Search()
        _ = search("policy", max_results=500)
        kwargs = self.fake_client.last_search_kwargs
        self.assertLessEqual(kwargs["maxResults"], 50)

    def test_channel_get_uploads_uses_youtube_safe_max_results_per_request(self):
        channel = info.Channel("channel-1")
        _ = channel.get_uploads()
        kwargs = self.fake_client.last_playlist_kwargs
        self.assertLessEqual(kwargs["maxResults"], 50)
