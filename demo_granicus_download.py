from CAIR import download_granicus_video, resolve_granicus_video_url

url = "https://loudoun.granicus.com/MediaPlayer.php?view_id=92&clip_id=1366"

print(f"input url: {url}")

resolved = resolve_granicus_video_url(url)
print(f"player page url: {resolved.player_page_url}")
print(f"playlist url: {resolved.playlist_url}")
print(f"media playlist url: {resolved.media_playlist_url}")
print(f"derived mp4 url: {resolved.mp4_url}")

result = download_granicus_video(url, output_dir="downloads")
print(f"saved to: {result.output_path}")
print(f"ffmpeg command: {' '.join(result.ffmpeg_command)}")
