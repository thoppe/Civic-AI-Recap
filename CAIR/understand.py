# from .cache_GPT import ChatGPT
# import pandas as pd
from .ai_tools import chat_with_openai
from pathlib import Path
import numpy as np
import diskcache

cache_align = diskcache.Cache("cache/understand/alignment")

current_file_path = Path(__file__).parent
prompt_file_path = current_file_path / "prompts"


class Analyze:
    def __init__(
        self,
        model_name="gpt-5",
        # parallel_threads=1,
        # embed_model_name="sentence-transformers/all-MiniLM-L6-v2",
    ):
        # self.GPT = ChatGPT(
        #    max_tokens=max_tokens,
        #    model_name=model_name,
        #    parallel_threads=parallel_threads,
        # )
        self.model_name = model_name
        # self.page_size = 1_204 * 50
        # self.embed_model_name = embed_model_name

    def preprocess_text(self, df) -> str:
        """
        Given an input dataframe, remove empty and repeated lines.
        """
        df["text"] = df["text"].str.strip()
        df["text"] = df["text"].replace("", np.nan)
        df.dropna(subset=["text"], inplace=True)
        df.drop_duplicates(subset=["text"], inplace=True, keep="first")
        text = "\n".join(df["text"].tolist())
        return text

    def streamline(self, text: str) -> str:
        f_instructions = prompt_file_path / "streamline_meeting.txt"
        with open(f_instructions) as FIN:
            instructions = FIN.read().strip()

        result = chat_with_openai(self.model_name, instructions, text, "low")
        return result

    def executive_summary(self, text: str) -> str:
        f_instructions = prompt_file_path / "exec_summary.txt"
        with open(f_instructions) as FIN:
            instructions = FIN.read().strip()

        result = chat_with_openai(self.model_name, instructions, text, "high")
        return result

    def __call__(self, prompt: str, system_prompt: str, reasoning_effort: str) -> str:
        result = chat_with_openai(
            self.model_name,
            system_prompt=system_prompt,
            user_prompt=prompt,
            reasoning_effort=reasoning_effort,
        )
        return result

    '''
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
    '''
