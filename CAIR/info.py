from pathlib import Path
import math
from tqdm import tqdm
import pandas as pd
import datetime
from .youtube_utils import youtube
import diskcache
import yt_dlp
from wasabi import msg
import subprocess
import isodate

cache_video = diskcache.Cache("cache/youtube/videos")
cache_channel = diskcache.Cache("cache/youtube/channels")
cache_search = diskcache.Cache("cache/youtube/search")
expire_time = 7 * 60 * 60 * 24


class Search:
    def __init__(self):
        pass

    @cache_search.memoize(expire=expire_time)
    def __call__(self, q, max_results=1_000, v_type="video", duration="any"):
        # msg.info(f"Searching '{q}'")

        search_info = []
        next_page_token = None
        progress_bar = tqdm()

        while True:
            request = youtube.search().list(
                part="snippet",
                q=q,
                maxResults=max_results,
                type=v_type,
                videoDuration=duration,
                eventType="completed",
                pageToken=next_page_token,
            )
            response = request.execute()
            next_page_token = response.get("nextPageToken")
            items = response.get("items", [])

            for item in items:
                search_info.append(item["snippet"])

            if next_page_token is None or len(search_info) >= max_results:
                break

            print(len(search_info))

            progress_bar.update()

        return search_info


class Video:
    def __init__(self, video_id):
        self.video_id = video_id

    @cache_video.memoize(expire=expire_time)
    def get_caption_list(self):
        msg.info(f"Downloading caption metadata {self.video_id}")
        caption_list_response = (
            youtube.captions().list(part="snippet", videoId=self.video_id).execute()
        )
        return caption_list_response

    @cache_video.memoize(expire=expire_time)
    def get_metadata(self):
        msg.info(f"Downloading video metadata {self.video_id}")

        request = youtube.videos().list(
            part="snippet,contentDetails,statistics", id=self.video_id
        )
        meta = request.execute()
        meta["download_date"] = datetime.datetime.now().isoformat()
        return meta

    @cache_video.memoize(expire=expire_time)
    def get_extended_metadata(self):
        # Uses yt-dlp to download
        msg.info(f"Downloading video metadata using yt-dlp {self.video_id}")

        with yt_dlp.YoutubeDL({}) as ydl:
            info = ydl.extract_info(self.URL, download=False)

        # ydl.sanitize_info makes the info json-serializable
        info = ydl.sanitize_info(info)
        return info

    def download_english_captions(self):
        caption_metadata = self.get_caption_list()

        for item in caption_metadata["items"]:
            if (
                item["snippet"]["language"] == "en"
                and item["snippet"]["trackKind"] == "asr"
            ):
                caption_id = item["id"]
                break
        else:
            err = f"Automatic English captions not found. {self.video_id}"
            raise ValueError(err)

        caption_response = (
            youtube.captions()
            .download(id=caption_id, tfmt="srt")  # or 'vtt' for WebVTT format
            .execute()
        )

        print(caption_response)

    def download_audio(self, f_audio):
        cmd = f"yt-dlp -f bestaudio -x --audio-format mp3 --audio-quality 0 -o {f_audio} {self.URL}"

        f_audio = Path(f_audio)
        if f_audio.exists():
            return f_audio

        msg.info(f"Downloading audio {self.video_id}")
        subprocess.call(cmd, shell=True)

        # Old code here, we don't need it anymore
        """
        meta = self.get_extended_metadata()
        dx = pd.DataFrame(meta["formats"])
        dx = dx[(dx["audio_ext"] == "mp4") | (dx["audio_ext"] == "m4a")]

        if not len(dx):
            err = f"No mp4 formats on youtube video {self.video_id}"

            raise ValueError(err)

        # Pick the first mp4/m4a format ID and download
        format_id = dx["format_id"].values[0]

        cmd = f"yt-dlp -f {format_id} -o {f_audio} {self.URL}"
        subprocess.call(cmd, shell=True)
        """

    @property
    def URL(self):
        return f"https://www.youtube.com/watch?v={self.video_id}"

    @property
    def channel_id(self):
        meta = self.get_metadata()
        return meta["items"][0]["snippet"]["channelId"]

    @property
    def title(self):
        meta = self.get_metadata()
        return meta["items"][0]["snippet"]["title"]

    @property
    def description(self):
        meta = self.get_metadata()
        return meta["items"][0]["snippet"]["description"]

    @property
    def published_at(self):
        meta = self.get_metadata()
        return meta["items"][0]["snippet"]["publishedAt"]

    @property
    def duration(self):
        # Returns the duration in seconds
        meta = self.get_metadata()
        duration = meta["items"][0]["contentDetails"]["duration"]
        duration = isodate.parse_duration(duration)
        return int(duration.total_seconds())

    def build_info(self):
        return {
            "video_id": self.video_id,
            "description": self.description,
            "published_at": self.published_at,
            "title": self.title,
            "duration": self.duration,
            "channel_id": self.channel_id,
        }


class Channel:
    def __init__(self, channel_id):
        self.channel_id = channel_id

    @cache_channel.memoize(expire=expire_time)
    def get_metadata(self):
        msg.info(f"Downloading channel metadata {self.channel_id}")
        parts = [
            "id",
            "snippet",
            "statistics",
            "contentDetails",
            "contentOwnerDetails",
            "brandingSettings",
            "status",
            "topicDetails",
        ]
        parts = ",".join(parts)
        request = youtube.channels().list(part=parts, id=self.channel_id)
        meta = request.execute()
        meta["download_date"] = datetime.datetime.now().isoformat()
        return meta

    @property
    def title(self):
        meta = self.get_metadata()
        return meta["items"][0]["snippet"]["title"]

    @property
    def description(self):
        meta = self.get_metadata()
        return meta["items"][0]["snippet"]["description"]

    @property
    def custom_url(self):
        meta = self.get_metadata()
        return meta["items"][0]["snippet"]["customUrl"]

    @property
    def published_at(self):
        meta = self.get_metadata()
        return meta["items"][0]["snippet"]["publishedAt"]

    @property
    def n_videos(self):
        meta = self.get_metadata()
        return int(meta["items"][0]["statistics"]["videoCount"])

    @property
    def n_views(self):
        meta = self.get_metadata()
        return int(meta["items"][0]["statistics"]["viewCount"])

    @property
    def n_subscribers(self):
        meta = self.get_metadata()
        return int(meta["items"][0]["statistics"]["subscriberCount"])

    def build_info(self):
        return {
            "channel_id": self.channel_id,
            "description": self.description,
            "title": self.title,
            "published_at": self.published_at,
            "custom_url": self.custom_url,
            "n_videos": self.n_videos,
            "n_subscribers": self.n_subscribers,
            "n_views": self.n_views,
        }

    @property
    @cache_channel.memoize(expire=expire_time)
    def upload_playlist_id(self):
        # Get the "Uploads" playlist ID
        channel_request = youtube.channels().list(
            part="contentDetails",
            id=self.channel_id,
            fields="items/contentDetails/relatedPlaylists/uploads",
        )
        response = channel_request.execute()
        response = response["items"][0]["contentDetails"]

        upload_playlist_id = response["relatedPlaylists"]["uploads"]
        return upload_playlist_id

    @cache_channel.memoize(expire=expire_time)
    def get_uploads(self):
        playlist_id = self.upload_playlist_id
        msg.info(f"Getting upload playlist videos {playlist_id}")

        # Fetch videos from the "Uploads" playlist
        video_info = []
        next_page_token = None
        fields = ",".join(
            [
                "nextPageToken",
                "items(snippet(publishedAt,resourceId(videoId),title))",
            ]
        )

        # Download is chunked by 50
        n_pages = math.ceil(self.n_videos / 50)
        progress_bar = tqdm(total=n_pages)
        max_results = 100_000

        while True:
            playlist_request = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=max_results,
                pageToken=next_page_token,
                fields=fields,
            )
            playlist_response = playlist_request.execute()
            items = playlist_response.get("items", [])

            for item in items:
                video_id = item["snippet"]["resourceId"]["videoId"]
                video_info.append(
                    {
                        "video_id": video_id,
                        "title": item["snippet"]["title"],
                        "publishedAt": item["snippet"]["publishedAt"],
                    }
                )

            next_page_token = playlist_response.get("nextPageToken")

            if next_page_token is None or len(video_info) >= max_results:
                break
            progress_bar.update()

        progress_bar.close()

        df = pd.DataFrame(video_info)
        df["channel_id"] = self.channel_id
        return df
