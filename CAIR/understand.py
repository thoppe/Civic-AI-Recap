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
    ):
        self.model_name = model_name

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

    def __call__(
        self, prompt: str, system_prompt: str, reasoning_effort: str
    ) -> str:
        result = chat_with_openai(
            self.model_name,
            system_prompt=system_prompt,
            user_prompt=prompt,
            reasoning_effort=reasoning_effort,
        )
        return result
