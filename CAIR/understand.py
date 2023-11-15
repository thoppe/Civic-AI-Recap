from .openAI_utils import tokenized_sampler
from .cache_GPT import ChatGPT


class Analyze:
    def __init__(
        self,
        model_name="gpt-3.5-turbo-1106",
        max_tokens=1024 * 4,
        parallel_threads=1,
    ):
        self.GPT = ChatGPT(
            max_tokens=max_tokens,
            model_name=model_name,
            parallel_threads=parallel_threads,
        )
        self.page_size = 4_000

    def preprocess_text(self, text):
        assert isinstance(text, str)

        lines = text.split("\n")
        blocks = [
            "\n".join(x) for x in tokenized_sampler(lines, self.page_size)
        ]
        return blocks

    def summarize(self, text):
        q = """
        Give a detailed summary from the following transcript of a meeting.
        Speak in a declarative voice and get directly to the point.
        {response}
        """.strip()

        blocks = self.preprocess_text(text)
        result = "\n".join(self.GPT.multiASK(q, "text", response=blocks))
        return result

    def outline(self, text):
        q = """
         "Clean, organize, and format the notes below using markdown:
        {response}
        """.strip()

        # Summarize the text first
        text = self.summarize(text)

        blocks = self.preprocess_text(text)
        result = "\n".join(self.GPT.multiASK(q, "text", response=blocks))
        return result
