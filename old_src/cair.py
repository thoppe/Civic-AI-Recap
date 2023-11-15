import pandas as pd
import json
import subprocess
from pathlib import Path
import argparse

# Create a command line argparser
parser = argparse.ArgumentParser(description="CAIR. Civic AI Recap")

possible_models = [
    "gpt-3.5-turbo-1106",
    "gpt-4-1106-preview",
]

# Add the string argument
parser.add_argument("--video_id", type=str, help="YoutubeID")
parser.add_argument(
    "--model_name",
    choices=possible_models,
    help="Type of ChatGPT model to use.",
)

parser.add_argument(
    "--download_only",
    action="store_true",
    help="Set this flag to only download",
)
parser.add_argument(
    "--transcribe_only",
    action="store_true",
    help="Set this flag to only download/transcribe",
)

# Parse the arguments
args = parser.parse_args()
video_id = args.video_id
model_name = args.model_name

########################################################################


class CAIR:
    """
    Civic AI Recap. Set of tools to download, transcribe, and parse
    Federal, State, and local government youtube videos.
    """

    def __init__(self, video_id, model_name, storage_directory="data"):
        self.video_id = video_id
        self.storage_directory = storage_directory
        self.model_name = model_name

    def create_directory(self, names):
        if isinstance(names, str):
            names = [names]

        save_dest = Path(self.storage_directory)
        for name in names:
            save_dest = save_dest / name

        if not save_dest.exists():
            save_dest.mkdir(exist_ok=True, parents=True)

        return save_dest

    def get_name(self, names, suffix):
        assert suffix.startswith(".")
        load_dest = self.create_directory(names)
        f_data = load_dest / f"{self.video_id}{suffix}"
        return f_data

    def download_video_metadata(self):
        URL = f"https://www.youtube.com/watch?v={self.video_id}"
        cmd = f'yt-dlp -j --skip-download "{URL}"'
        output = subprocess.check_output(cmd, shell=True, text=True)
        js = json.loads(output)

        # Remove some info we don't need

        unneeded_keys = ["automatic_captions", "thumbnails"]
        for key in unneeded_keys:
            if key in js:
                del js[key]

        unneeded_keys = [
            "url",
            "manifest_url",
            "http_headers",
            "fragments",
            "downloader_options",
        ]
        for x in js["formats"]:
            for key in unneeded_keys:
                if key in x:
                    del x[key]

        return js

    def load_video_metadata(self):
        f_metadata = self.get_name("metadata", ".json")

        if not f_metadata.exists():
            js = self.download_video_metadata()
            with open(f_metadata, "w") as FOUT:
                FOUT.write(json.dumps(js, indent=2))

        with open(f_metadata) as FIN:
            return json.load(FIN)

    def load_audio(self):
        f_audio = self.get_name("audio", ".mp4")
        if not f_audio.exists():
            self.download_audio(f_audio)
        return f_audio

    def download_audio(self, f_audio):
        js = self.load_video_metadata()

        df = pd.DataFrame(js["formats"])
        df = df[df["audio_ext"] == "mp4"]
        if not len(df):
            raise ValueError(f"No mp4 formats on youtube video {self.video_id}")

        # Pick the first mp4 format ID and download
        format_id = df["format_id"].values[0]

        URL = f"https://www.youtube.com/watch?v={self.video_id}"
        cmd = f"yt-dlp -f {format_id} -o {f_audio} {URL}"
        subprocess.call(cmd, shell=True)

    def load_transcript(self):
        f_transcript = self.get_name("transcript", ".txt")
        if not f_transcript.exists():
            f_audio = self.load_audio()
            self.compute_transcript(f_audio, f_transcript)

        text = []
        with open(f_transcript) as FIN:
            for line in FIN:
                line = " ".join(line.split(" ")[4:]).strip()
                text.append(line)
        text = "\n".join(text)
        return text

    def compute_transcript(self, f_audio, f_transcript):
        save_dest = f_transcript.parent
        model_size = "medium"
        language = "en"
        cmd = (
            f"whisperx --model large --language {language} "
            # f"whisper --model {model_size} --language {language} "
            f"-o {save_dest} -f all {f_audio}"
        )
        subprocess.call(cmd, shell=True)

    def compute_text_summary(self):
        text = self.load_transcript()
        lines = text.split("\n")
        blocks = ["\n".join(x) for x in tokenized_sampler(lines, 4_000)]

        q = "\n".join(
            [
                "Give a detailed summary from the following transcript of a meeting.",
                "Speak in a declarative voice and get directly to the point.",
                "{response}",
            ]
        )

        GPT = ChatGPT(max_tokens=1024 * 4, model_name=model_name)
        result = "\n".join(GPT.multiASK(q, "text", response=blocks))
        return result

    def load_text_summary(self):
        f_summary = self.get_name([model_name, "summary_full"], ".md")
        if not f_summary.exists():
            result = self.compute_text_summary()
            with open(f_summary, "w") as FOUT:
                FOUT.write(result)

        with open(f_summary, "r") as FIN:
            return FIN.read()

    def compute_text_outline(self):
        text = self.load_text_summary()
        lines = text.split("\n")
        blocks = ["\n".join(x) for x in tokenized_sampler(lines, 4_000)]

        q = "\n".join(
            [
                "Clean, organize, and format the notes below using markdown:",
                "{response}",
            ]
        )

        GPT = ChatGPT(max_tokens=1024 * 4, model_name=model_name)
        result = "\n".join(GPT.multiASK(q, "text", response=blocks))
        return result

    def load_text_outline(self):
        f_summary = self.get_name([model_name, "summary_md"], ".md")

        if not f_summary.exists():
            result = self.compute_text_outline()
            with open(f_summary, "w") as FOUT:
                FOUT.write(result)

        with open(f_summary, "r") as FIN:
            return FIN.read()


if __name__ == "__main__":
    clf = CAIR(video_id, model_name=model_name)

    clf.load_video_metadata()
    clf.load_audio()

    if args.download_only:
        exit(0)

    clf.load_transcript()

    if args.transcribe_only:
        exit(0)

    from src.cache_GPT import ChatGPT
    from src.utils import tokenized_sampler

    clf.compute_text_summary()
    clf.compute_text_outline()

    f_md_outline = clf.get_name([clf.model_name, "summary_md"], ".md")
    cmd = f"glow {f_md_outline}"
    subprocess.call(cmd, shell=True)
