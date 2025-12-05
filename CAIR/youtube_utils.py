import os
from functools import lru_cache

from googleapiclient.discovery import build

key_name = "YOUTUBE_API_KEY"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


@lru_cache(maxsize=1)
def get_youtube_client():
    api_key = os.environ.get(key_name)
    if api_key is None:
        raise EnvironmentError(
            f"Set {key_name} in your environment to use the YouTube Data API."
        )

    return build(
        YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=api_key
    )
