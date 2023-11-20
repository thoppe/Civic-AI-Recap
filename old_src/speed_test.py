from CAIR import Transcription
from time import time

"""
Timing tests:
+ Whisper        364.63 sec (23 load) (35% vtop)
+ Whisperx       47.68  sec (19.94 load)
+ faster-whisper 60.57  sec (3.78 load)
+ insane-whisper 23.47  sec sec (42 load)
+ insane-whisper 17.41  sec sec (42 load) *2
+ insane-whisper 12.75  sec sec (42 load) *4
+ insane-whisper 13.08  sec sec (42 load) *8
"""


f_video = "bNs9y5z1PY8.mp4"
# method = "whisper"
# method = "insanely-fast-whisper"
# method = 'whisperx'
method = "faster-whisper"

clf = Transcription(method=method)
t0 = time()
clf.load_STT_model()
print(f"Total time to load model {method} {time()-t0:0.2f}")

t0 = time()
clf.transcribe(f_video)
print(f"Total time to transcribe {time()-t0:0.2f}")
