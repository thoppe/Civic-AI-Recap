from CAIR import Granicus, find_viewpublisher_url
import pandas as pd

# Testing against different views
examples = [
#    "https://sacramento.granicus.com/viewpublisher.php?view_id=22",
    "https://tracy-ca.granicus.com/ViewPublisher.php?view_id=2"
]

# Testing a secondary page
source_url = "https://www.pwcva.gov/department/board-county-supervisors/live-video-briefs-archives"
granicus_url = find_viewpublisher_url(source_url)
#examples.append(granicus_url)

for url in examples:
    g = Granicus(url)
    print(g.build_info())

    df = pd.DataFrame(g.get_uploads())
    df = df.dropna(subset=["video_id"])
    print(df)
    print(df.iloc[0])
    print(df.iloc[0]["video_id"])
    
