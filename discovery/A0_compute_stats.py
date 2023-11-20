from dspipe import Pipe
import pandas as pd


def get_transcript(f0):
    df = pd.read_csv(f0)
    df["video_id"] = f0.stem
    return df


# Pipe('data/transcript/', input_suffix='.csv')(get_transcript_duration)

df = pd.concat(Pipe("data/transcript/")(get_transcript))
g = df.groupby("video_id")
hours = g["end"].max() / 3600.0
total_hours = hours.sum()
print(
    f"Total transcribed hours {total_hours:0.1f}, ({total_hours/24:0.1f} days)"
)

n_chars = df["text"].str.len().sum()
print(f"Total characters {n_chars:,}")

estimated_tokens = n_chars // 4
cost_per_1K_tokens = 0.0010

estimated_cost = (estimated_tokens / 1000) * cost_per_1K_tokens
print(f"Estimated cost ${estimated_cost:0.2f}")


# df = df.sample(n=100)
# encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
# n_tokens = df['text'].apply(encoding.encode).apply(len).sum()
# print(f"Total tokens {n_tokens:,}")
