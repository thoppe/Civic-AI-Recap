from .openAI_utils import tokenized_sampler
from .cache_GPT import ChatGPT
import pandas as pd
import numpy as np
import diskcache

cache_align = diskcache.Cache("cache/understand/alignment")


class Analyze:
    def __init__(
        self,
        model_name="gpt-4o",
        max_tokens=1024 * 4,
        parallel_threads=1,
        embed_model_name="sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.GPT = ChatGPT(
            max_tokens=max_tokens,
            model_name=model_name,
            parallel_threads=parallel_threads,
        )
        self.page_size = 1_204 * 50

        self.embed_model_name = embed_model_name

    def preprocess_text(self, text):
        if isinstance(text, pd.Series):
            text = text.str.cat(sep="\n")

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
        Clean, organize, and format the collective notes below using markdown. Only provide bullets.
        {response}
        """.strip()

        blocks = self.preprocess_text(text)
        result = self.GPT.multiASK(q, output="list", response=blocks)

        # Flatten
        result = [item for row in result for item in row]
        return result

    @cache_align.memoize()
    def align_sections(self, text_lines, outline, window_n=30):
        """
        Using DFW and an embedding, align the outline with the text.

        Will reload the model each time. May need to remove to own class.
        """

        from sentence_transformers import SentenceTransformer
        import dtw

        embed_model = SentenceTransformer(self.embed_model_name)

        # Concatenate adjacent sections for the embedding
        long_text = pd.Series(text_lines)
        long_text = [
            long_text[i : i + window_n].str.cat(sep=" ")
            for i in range(len(long_text))
        ]

        Ex = embed_model.encode(long_text)
        Ey = embed_model.encode(outline)

        Ex /= np.linalg.norm(Ex, axis=1, keepdims=True)
        Ey /= np.linalg.norm(Ey, axis=1, keepdims=True)
        score = 1 - (Ex @ Ey.T) ** 2

        result = dtw.dtw(
            score.copy().astype("double"),
            step_pattern="asymmetric",
            # open_end=True, open_begin=True,
        )

        df = pd.DataFrame()
        df["outline"] = outline

        dx = pd.DataFrame(data=result.index2)
        dx["order"] = dx.index

        df["starting_index"] = dx.groupby(0).order.min()
        df["ending_index"] = dx.groupby(0).order.max()

        for key in ["starting_index", "ending_index"]:
            df[key] = df[key].ffill().astype(int)

        df["ref_text"] = [long_text[i] for i in df.starting_index]
        return df
