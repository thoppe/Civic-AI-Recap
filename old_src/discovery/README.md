Use this section to find new potential target videos & channels

> pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

## Notes:

+ It's possible to get the channel_ID from a metadata download of a video
+ Search from channel ID seems to be limited to 500?
+ Can search by date to get the remaining numbers https://developers.google.com/youtube/v3/docs/search/list#forDeveloper
+ Can see the total number in:

      "statistics": {
        "viewCount": "6687405",
        "subscriberCount": "27100",
        "hiddenSubscriberCount": false,
        "videoCount": "3424"
      },