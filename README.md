# Civic-AI-Recap (CAIR)
Tools to digitize, transcribe, and analyze public hearings, committees, and symposiums on youtube.

    git clone https://github.com/thoppe/Civic-AI-Recap/
    cd Civic-AI-Recap
    pip install .

Set required environment variables:

- `YOUTUBE_API_KEY` for fetching metadata via the YouTube Data API.
- `OPENAI_API_KEY` for LLM-powered analysis (used by `Analyze`).

Optional speech-to-text backends (Whisper/faster-whisper/whisperx) can be installed with:

```
pip install ".[transcription]"
```


``` python
import pandas as pd
from CAIR import Channel, Video, Transcription, Analyze

video_id = "P0rxq42sckU"
vid = Video(video_id)
channel = Channel(vid.channel_id)
df = pd.DataFrame(channel.get_uploads())

print(vid.title)
print(channel.title, channel.n_videos)
print(df)

'''
SEP 30, 2025 |  City Council
City of San Jose, CA 1741

         start       end                                               text
0         0.00     29.28                                         All right.
1        29.28     30.28                                    Good afternoon.
2        30.28     31.28                                 Welcome, everyone.
3        31.28     36.40  I'm pleased to call to order this meeting of t...
4        36.40     38.10                                 of September 30th.
...        ...       ...                                                ...
3682  19872.78  19874.34  I thought he was waiting to speak. Back to cou...
3683  19876.92  19879.92  Thank you. That concludes our meeting. Thank you.
3684  19881.48  19911.46                                         Thank you.
3685  19911.48  19912.20                                         Thank you.
'''

f_audio = f"{video_id}.mp3"
vid.download_audio(f_audio)
df = Transcription().transcribe(f_audio, text_only=False)
print(df)

'''
      youtube_id                                              title           publishedAt
0    CisZ6m-_lRw  Superintendent Thurmond's 2023 Digital Citizen...  2023-11-09T01:12:16Z
1    rqXdw30u6Rc  Digital Citizenship and Digital Safety - 2023 ...  2023-11-07T18:55:35Z
2    s_x12A3843A  Digital Citizenship and Mental Health - 2023 D...  2023-11-07T18:52:55Z
3    RQjrFZoCIIo  Digital Citizenship and Assistive Technology -...  2023-11-07T18:50:20Z
4    O35efka1PWg  Digital Citizenship and Inclusive Technologies...  2023-11-07T18:45:15Z
..           ...                                                ...                   ...
873  4HaAwQa7Q_A  Chapter 8: Supporting Transitional Kindergarte...  2013-10-22T18:01:33Z
874  JEokucRJeC0  Local Educational Agency (LEA) Plan Evidence o...  2013-08-29T17:44:51Z
875  g5cYubdeh8U  Transition to Assessments Based on Common Core...  2013-08-21T20:47:21Z
876  zGMRdS11nJg  California School for the Deaf, Riverside (CSD...  2013-05-29T20:56:18Z
877  _H-EylSk-sM     Black Women...on the Move!...Image of the 80's  2012-02-28T01:12:20Z
'''

f_audio = f"{video_id}.mp4"
vid.download_audio(f_audio)

model = Analyze(model_name="gpt-5-mini")
text = model.preprocess_text(df)
streamline = model.streamline(text)
summary = model.executive_summary(streamline)
print(summary)

'''
1. Bottom Line Up Front (BLUF)
San Jose’s council advanced an ambitious, data-driven “Focus Area 2.0” performance model while
approving near-term actions with statewide implications: significant police labor concessions
to stabilize staffing, a city amicus joining litigation in defense of Planned Parenthood, an
ordinance limiting masked identities for law-enforcement/immigration agents, major downtown
land acquisition to preserve future convention/sports options, and a large subsidized downtown
workforce housing loan — all overlapping statewide priorities on public safety, homelessness,
housing affordability, labor enforcement, and immigrant/community trust.

2. Key State-Level Themes and Implications
- Homelessness and shelter operations are shifting from capacity-building to systems/integration
issues (throughput, CalAIM billing, HMIS integration, county coordination). San Jose’s
[...]
'''
```

Channel metadata and videos can be acessed:

``` python
uploads = channel.get_uploads()
print(uploads[['video_id', 'title', 'publishedAt']])

'''
         video_id                                              title           publishedAt
0     h1sCi9oiBSc  NOV 6, 2025 | Police & Fire Department Retirem...  2025-11-08T07:05:34Z
1     4mvGLqa-G70                       NOV 18, 2025 |  City Council  2025-11-05T22:27:04Z
2     BAvwrwjsnZM       18 NOVIEMBRE 2025 | Reunión del Ayuntamiento  2025-11-05T22:24:28Z
3     KGeDIw6vUDo  NOV 5, 2025 | Rules & Open Government/Committe...  2025-11-05T22:16:10Z
4     itaRH6GLzBw        4 NOVIEMBRE 2025 | Reunión del Ayuntamiento  2025-11-05T12:59:25Z
...           ...                                                ...                   ...
1747  BV2WEzVDrLw                    Fireworks Prevention en Español  2016-11-04T16:43:10Z
1748  nQWZLit5Kn0       Fireworks Prevention with Firefighter Alfred  2016-11-04T16:41:21Z
1749  2jH3dEH8gK0              SJ Journey To Fiscal SustainabilityHD  2016-11-04T00:02:36Z
1750  i2I98YY8btQ                   Bike Sharing arrives in San José  2016-11-03T23:59:27Z
1751  BpJ911ynFN0                     Parks & Rec. 2013 Junior Games  2016-11-03T23:57:56Z

'''
```

`channel.get_metadata()`

```json
{
  "kind": "youtube#channelListResponse",
  "etag": "I-t6Dq6TbsrHZb-C8Tvw3iLjn-0",
  "pageInfo": {
    "totalResults": 1,
    "resultsPerPage": 5
  },
  "items": [
    {
      "kind": "youtube#channel",
      "etag": "4WmqmG5PoRLHq5DgHM_Iix4UEJE",
      "id": "UCeDiMzJEUbPgaruDcXnD4Cg",
      "snippet": {
        "title": "City of San Jose, CA",
        "description": "With almost one million residents, San José is one of the safest, and most diverse cities in the United States. It is Northern California’s largest city and the 13th largest in the nation. Colloquially known as the Capital of Silicon Valley, San José’s transformation into a global innovation center has resulted in one of the nation’s highest concentrations of technology companies and expertise in the world.",
        "customUrl": "@cityofsanjosecalifornia",
        "publishedAt": "2013-07-15T19:52:00Z",
        "localized": {
          "title": "City of San Jose, CA",
          "description": "With almost one million residents, San José is one of the safest, and most diverse cities in the United States. It is Northern California’s largest city and the 13th largest in the nation. Colloquially known as the Capital of Silicon Valley, San José’s transformation into a global innovation center has resulted in one of the nation’s highest concentrations of technology companies and expertise in the world."
        },
        "country": "US"
      },
      "contentDetails": {
        "relatedPlaylists": {
          "likes": "",
          "uploads": "UUeDiMzJEUbPgaruDcXnD4Cg"
        }
      },
      "statistics": {
        "viewCount": "1428701",
        "subscriberCount": "5340",
        "hiddenSubscriberCount": false,
        "videoCount": "1741"
      },
      "topicDetails": {
        "topicIds": [
          "/m/098wr",
          "/m/05qt0"
        ],
        "topicCategories": [
          "https://en.wikipedia.org/wiki/Society",
          "https://en.wikipedia.org/wiki/Politics"
        ]
      },
      "status": {
        "privacyStatus": "public",
        "isLinked": true,
        "longUploadsStatus": "longUploadsUnspecified"
      },
      "brandingSettings": {
        "channel": {
          "title": "City of San Jose, CA",
          "description": "With almost one million residents, San José is one of the safest, and most diverse cities in the United States. It is Northern California’s largest city and the 13th largest in the nation. Colloquially known as the Capital of Silicon Valley, San José’s transformation into a global innovation center has resulted in one of the nation’s highest concentrations of technology companies and expertise in the world.",
          "unsubscribedTrailer": "mEd25UErtPw",
          "country": "US"
        },
        "image": {
          "bannerExternalUrl": "https://yt3.googleusercontent.com/Vp-n5GjLp9EkbgaWcJntExB2442KAHU3zYqo5NTMsJpiY2vCIxIlZwlLJxkeEE-EzvQ8oabm"
        }
      },
      "contentOwnerDetails": {}
    }
  ],
  "download_date": "2025-11-10T11:25:38.516298"
}


```

## Thoughts and ideas (TBD)

+ Pull in a large corpus of text to analyze (NISS? State Ed. Board Meetings?)
+ Work on RAG analysis of corpus ([Private GPT](https://github.com/imartinez/privateGPT)?)

## DEV notes

Prompts for summary and streamlining can be found [here](CAIR/prompts/).

To get [whisperx](https://github.com/m-bain/whisperX) to run:

     export PATH=~/anaconda3/bin:$PATH
     source activate
     conda activate whisperx
