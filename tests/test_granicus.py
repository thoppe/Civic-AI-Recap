from CAIR import Granicus

examples = [
    "https://sacramento.granicus.com/viewpublisher.php?view_id=22",
    #    "sacramento.granicus.com/viewpublisher.php?view_id=22",
    "https://tracy-ca.granicus.com/player/camera/2?publish_id=8&redirect=true",
]

for url in examples:
    g = Granicus(url)
    print(g.url)
    g.scan_view_ids()
    print(g.valid_page_idx)
