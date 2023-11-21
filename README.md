# Civic-AI-Recap (CAIR)
Tools to digitize, transcribe, and analyze public hearings, committees, and symposiums on youtube.

    git clone https://github.com/thoppe/Civic-AI-Recap/
    cd Civic-AI-Recap
    pip install .


``` python
import pandas as pd
from CAIR import Channel, Video, Transcription, Analyze

video_id = "A0HVwoagKPc"
vid = Video(video_id)
channel = Channel(vid.channel_id)

print(vid.title)
print(channel.title, channel.n_videos)
df = pd.DataFrame(channel.get_uploads())
print(df)

'''
State Board of Education Meeting May 19, 2023
California Department of Education 879

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

text = Transcription().transcribe(f_audio)
print(Analyze().summarize(text))
print(Analyze().outline(text))

'''
# Meeting Notes

**Meeting Reconvened:**
- The meeting reconvened from closed session to discuss legal matters and to consider waiver consent items W1 through W11.
- Public comment was taken both in person and via phone, with no callers in the queue.

**Recommendations from California Department of Education and Advisory Commission on Charter Schools:**
- The California Department of Education recommended that the state board approve 20 charter schools' funding determination at 100%, approve seven at 85%, and approve seven charter schools' funding determinations at the level for which they are qualified based on their reported expenditures.
[...]
'''
```

## Thoughts and ideas

+ Pull in a large corpus of text to analyze (NISS? State Ed. Board Meetings?)
+ Work on RAG analysis of corpus ([Private GPT](https://github.com/imartinez/privateGPT)?)

## Dev notes

To get [whisperx](https://github.com/m-bain/whisperX) to run:

     export PATH=~/anaconda3/bin:$PATH
     source activate
     conda activate whisperx
