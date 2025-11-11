import os
from googleapiclient.discovery import build

key_name = "YOUTUBE_API_KEY"
API_KEY = os.environ.get(key_name)
if API_KEY is None:
    print(f"Set {key_name} in as an ENV variable")
    exit(1)

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
