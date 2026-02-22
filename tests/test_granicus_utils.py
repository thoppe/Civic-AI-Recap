import unittest
from unittest.mock import patch, Mock

from CAIR.granicus_utils import Granicus, cache_channel, find_viewpublisher_url


class FakeResponse:
    def __init__(self, text: str, url: str, status_code: int = 200):
        self.text = text
        self.url = url
        self.status_code = status_code
        self.ok = status_code < 400

    def raise_for_status(self):
        return None


class TestFindViewPublisherUrl(unittest.TestCase):
    def test_returns_direct_viewpublisher_url(self):
        url = "https://pwcgov.granicus.com/ViewPublisher.php?view_id=23"
        self.assertEqual(find_viewpublisher_url(url), url)

    @patch("CAIR.granicus_utils.requests.get")
    def test_finds_case_insensitive_viewpublisher_url_in_html(self, mock_get):
        source_url = "https://www.pwcva.gov/department/board-county-supervisors/live-video-briefs-archives"
        expected = "https://pwcgov.granicus.com/ViewPublisher.php?view_id=23"
        html = f"""
        <html>
            <body>
                <a href="{expected}">Live and Archived Meetings</a>
            </body>
        </html>
        """
        mock_get.return_value = FakeResponse(text=html, url=source_url)

        result = find_viewpublisher_url(source_url)
        self.assertEqual(result, expected)

    @patch("CAIR.granicus_utils.requests.get")
    def test_returns_empty_string_when_not_found(self, mock_get):
        source_url = "https://example.gov/meetings"
        html = '<html><body><a href="/calendar">Calendar</a></body></html>'
        mock_get.return_value = FakeResponse(text=html, url=source_url)

        result = find_viewpublisher_url(source_url)
        self.assertEqual(result, "")


class TestGranicusMetadataProperties(unittest.TestCase):
    def test_title_description_rss_and_build_info(self):
        g = Granicus("https://sacramento.granicus.com/viewpublisher.php?view_id=22")
        html = """
        <html>
            <head>
                <title>Meeting Portal</title>
            </head>
            <body>
                <div id="intro">Live and archived board meetings.</div>
                <a id="RSS" href="https://sacramento.granicus.com/rss">RSS Feed</a>
            </body>
        </html>
        """
        g.session.get = lambda _url: FakeResponse(text=html, url=g.homepage_url)

        self.assertEqual(g.title, "Meeting Portal")
        self.assertEqual(g.description, "Live and archived board meetings.")
        self.assertEqual(g.rss, "https://sacramento.granicus.com/rss")

        info = g.build_info()
        self.assertEqual(info["channel_id"], g.homepage_url)
        self.assertEqual(info["homepage_url"], g.homepage_url)
        self.assertEqual(info["url"], g.url)
        self.assertEqual(info["title"], "Meeting Portal")
        self.assertEqual(info["description"], "Live and archived board meetings.")
        self.assertEqual(info["rss"], "https://sacramento.granicus.com/rss")

    @patch("builtins.print")
    def test_homepage_fetch_prints_once_on_cache_miss(self, mock_print):
        homepage_url = "https://unit-test-cache.granicus.com/viewpublisher.php?view_id=1"
        key = ("Granicus._get_homepage_html", homepage_url)
        if key in cache_channel:
            del cache_channel[key]

        g = Granicus(homepage_url)
        html = """
        <html>
            <head><title>Cached Once</title></head>
            <body>
                <div id="intro">Intro text</div>
                <a id="RSS" href="https://unit-test-cache.granicus.com/rss">RSS</a>
            </body>
        </html>
        """
        g.session.get = Mock(return_value=FakeResponse(text=html, url=homepage_url))

        _ = g.title
        _ = g.description
        _ = g.rss

        g.session.get.assert_called_once_with(homepage_url)
        mock_print.assert_any_call(f"Downloading Granicus URL (cache miss): {homepage_url}")

    def test_rss_id_match_is_case_insensitive(self):
        g = Granicus("https://case-rss.granicus.com/viewpublisher.php?view_id=9")
        html = """
        <html>
            <body>
                <a id="Rss" href="https://case-rss.granicus.com/feed.xml">Feed</a>
            </body>
        </html>
        """
        g.session.get = Mock(return_value=FakeResponse(text=html, url=g.homepage_url))
        self.assertEqual(g.rss, "https://case-rss.granicus.com/feed.xml")

    def test_get_uploads_parses_meeting_rows(self):
        homepage_url = "https://uploads-test.granicus.com/ViewPublisher.php?view_id=22"
        g = Granicus(homepage_url)

        key_uploads = ("Granicus.get_uploads", homepage_url)
        key_html = ("Granicus._get_homepage_html", homepage_url)
        if key_uploads in cache_channel:
            del cache_channel[key_uploads]
        if key_html in cache_channel:
            del cache_channel[key_html]

        html = """
        <html>
            <body>
                <table>
                    <tr class="even" odd>
                        <td class="listItem" headers="Name">1:00 PM City Council (Closed Session) (Special Meeting)</td>
                        <td class="listItem Date" headers="Date">Aug 12, 2025</td>
                        <td class="listItem Watch">
                            <a class="watchLink" href="javascript:void(0);" onClick="window.open('//sacramento.granicus.com/MediaPlayer.php?view_id=22&clip_id=6479','player')">Watch</a>
                        </td>
                        <td class="listItem Duration" headers="Duration">00h&nbsp;01m</td>
                        <td class="listItem Agenda"><a href="//sacramento.granicus.com/AgendaViewer.php?view_id=22&clip_id=6479">Agenda</a></td>
                        <td class="listItem Minutes"></td>
                        <td class="listItem"><a href="https://archive-video.granicus.com/sacramento/sacramento_2b928371-7a70-481a-a73c-72844347b630.mp3">MP3 Audio</a></td>
                    </tr>
                    <tr class="even" odd>
                        <td class="listItem" headers="Name">Board of County Supervisors - Joint Meeting with the School Board</td>
                        <td class="listItem" headers="Date Board-of-County-Supervisors---Joint-Meeting-with-the-School-Board"><span style="display:none;">1764748800</span>Dec 3, 2025</td>
                        <td class="listItem" headers="Duration Board-of-County-Supervisors---Joint-Meeting-with-the-School-Board">01h&nbsp;23m</td>
                        <td class="listItem"><a href="//pwcgov.granicus.com/AgendaViewer.php?view_id=23&clip_id=3752" target="_blank">Agenda</a></td>
                        <td class="listItem"><a href="//pwcgov.granicus.com/MinutesViewer.php?view_id=23&clip_id=3752" target="_blank">Briefs</a></td>
                        <td class="listItem" headers="VideoLink Board-of-County-Supervisors---Joint-Meeting-with-the-School-Board">
                            <a href="javascript:void(0);" onclick="window.open('//pwcgov.granicus.com/MediaPlayer.php?view_id=23&clip_id=3752','player')">Watch Now</a>
                        </td>
                        <td class="listItem" headers="MP4Link Board-of-County-Supervisors---Joint-Meeting-with-the-School-Board">
                            <a href="https://archive-video.granicus.com/pwcgov/pwcgov_39759471-57e8-4963-9d09-e5f118e2ae92.mp4">Download MP4</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
        g.session.get = Mock(return_value=FakeResponse(text=html, url=homepage_url))

        uploads = g.get_uploads()
        self.assertEqual(len(uploads), 2)

        first = uploads[0]
        self.assertEqual(first["title"], "1:00 PM City Council (Closed Session) (Special Meeting)")
        self.assertEqual(first["publishedAt"], "Aug 12, 2025")
        self.assertEqual(first["Duration"], "00h 01m")
        self.assertEqual(
            first["video_id"],
            "https://archive-video.granicus.com/sacramento/sacramento_2b928371-7a70-481a-a73c-72844347b630.mp3",
        )
        self.assertIn("Agenda", first["additional_items"])

        second = uploads[1]
        self.assertEqual(
            second["title"],
            "Board of County Supervisors - Joint Meeting with the School Board",
        )
        self.assertEqual(second["publishedAt"], "1764748800 Dec 3, 2025")
        self.assertEqual(second["Duration"], "01h 23m")
        self.assertEqual(
            second["video_id"],
            "https://archive-video.granicus.com/pwcgov/pwcgov_39759471-57e8-4963-9d09-e5f118e2ae92.mp4",
        )
        self.assertIn("Briefs", second["additional_items"])

    def test_get_uploads_handles_listing_row_with_mediaplayer_only(self):
        homepage_url = "https://tracy-ca.granicus.com/ViewPublisher.php?view_id=2"
        g = Granicus(homepage_url)

        key_uploads = ("Granicus.get_uploads", homepage_url)
        key_html = ("Granicus._get_homepage_html", homepage_url)
        if key_uploads in cache_channel:
            del cache_channel[key_uploads]
        if key_html in cache_channel:
            del cache_channel[key_html]

        html = """
        <html>
            <body>
                <table>
                    <tr class="listingRow">
                        <td class="listItem" headers="Name" id="Closed-Session-Meeting" scope="row">
                            Closed Session Meeting
                        </td>
                        <td class="listItem" headers="Date Closed-Session-Meeting">
                            Feb&nbsp;17,&nbsp;2026
                            -
                            05:25&nbsp;PM
                        </td>
                        <td class="listItem" headers="Duration Closed-Session-Meeting">00h&nbsp;30m</td>
                        <td class="listItem"></td>
                        <td class="listItem">&nbsp;</td>
                        <td class="listItem" headers="VideoLink Closed-Session-Meeting">
                            <a href="javascript:void(0);" onClick="window.open('//tracy-ca.granicus.com/MediaPlayer.php?view_id=2&clip_id=1779','player')">
                                Video
                            </a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
        g.session.get = Mock(return_value=FakeResponse(text=html, url=homepage_url))

        uploads = g.get_uploads()
        self.assertEqual(len(uploads), 1)

        item = uploads[0]
        self.assertEqual(item["title"], "Closed Session Meeting")
        self.assertEqual(item["publishedAt"], "Feb 17, 2026 - 05:25 PM")
        self.assertEqual(item["Duration"], "00h 30m")
        self.assertEqual(
            item["video_id"],
            "https://tracy-ca.granicus.com/MediaPlayer.php?view_id=2&clip_id=1779",
        )
