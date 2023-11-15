import numpy as np
import pandas as pd
from dspipe import Pipe


# Filter only for those with the word Board meeting in them
df = pd.concat(Pipe("data/channel_upload_list/")(pd.read_csv, -1))

# Keep a special set
dx = df[df["channel_name"] == "California Department of Education"]
dx = dx[dx["title"].str.lower().str.find("state board") > -1]
print(dx.title.tolist())
dx.to_csv("CA_board.csv")
exit()


org_counts = df.value_counts("channel_name")
print(org_counts)

whitelist_index = np.zeros(len(df))
for key in [
    "board",
    "SBOE",
]:
    idx = df["title"].str.lower().str.find("board") > -1
    whitelist_index = whitelist_index | idx

blacklist_index = np.zeros(len(df))
for key in [
    "news",
    "student",
    "childhood",
    "charter",
    "planning",
    "special",
    "interview",
    "boardroom",
    "dashboard",
    "jamboard",
]:
    idx = df["title"].str.lower().str.find(key) > -1
    blacklist_index = blacklist_index | idx

df = df[(whitelist_index) & (~blacklist_index)]
# print(df[df.channel_name=="DCSBOE"].title)

selected_counts = df.value_counts("channel_name")
# print(df['title'].values.tolist())

counts = pd.DataFrame([org_counts, selected_counts]).T.fillna(0).astype(int)
counts.columns = ["org", "selected"]
print(counts)
df.to_csv("filtered_SB_results.csv", index=False)
print(df)
