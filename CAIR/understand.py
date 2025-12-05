from pathlib import Path
from typing import Optional

import pandas as pd

from .ai_tools import chat_with_openai


def _read_prompt(prompt_name: str) -> str:
    prompts_dir = Path(__file__).resolve().parent / "prompts"
    prompt_path = prompts_dir / prompt_name
    return prompt_path.read_text()


class Analyze:
    def __init__(
        self,
        model_name: str = "gpt-5-mini",
        reasoning_effort: Optional[str] = "low",
    ):
        self.model_name = model_name
        self.reasoning_effort = reasoning_effort

    def __call__(
        self, prompt: str, system_prompt: str, reasoning_effort: Optional[str]
    ) -> str:
        result = chat_with_openai(
            self.model_name,
            system_prompt=system_prompt,
            user_prompt=prompt,
            reasoning_effort=reasoning_effort,
        )
        return result

    def preprocess_text(self, transcript) -> str:
        """Flatten a transcript DataFrame into raw text for prompting."""
        if isinstance(transcript, pd.DataFrame):
            if "text" not in transcript.columns:
                raise ValueError(
                    "Transcript DataFrame must include a 'text' column."
                )
            text_series = transcript["text"].astype(str).str.strip()
            return "\n".join(text_series[text_series != ""])

        if isinstance(transcript, str):
            return transcript

        raise TypeError(
            "Transcript must be a pandas DataFrame with a 'text' column or a raw string."
        )

    def streamline(self, transcript: str) -> str:
        """Filter filler language while keeping meeting content in order."""
        prompt = _read_prompt("streamline_meeting.txt")
        return chat_with_openai(
            self.model_name,
            system_prompt=prompt,
            user_prompt=transcript,
            reasoning_effort=self.reasoning_effort,
        )

    def executive_summary(self, streamlined_text: str) -> str:
        """Create a governor-ready executive summary."""
        prompt = _read_prompt("exec_summary.txt")
        return chat_with_openai(
            self.model_name,
            system_prompt=prompt,
            user_prompt=streamlined_text,
            reasoning_effort=self.reasoning_effort,
        )
