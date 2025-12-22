from pathlib import Path
from typing import Optional

import pandas as pd

from .ai_tools import Gpt5ReasoningEffort, ServiceTier, chat_with_openai


def _read_prompt(prompt_name: str) -> str:
    prompts_dir = Path(__file__).resolve().parent / "prompts"
    prompt_path = prompts_dir / prompt_name
    return prompt_path.read_text()


class Analyze:
    def __init__(
        self,
        model_name: str = "gpt-5-mini",
        reasoning_effort: Optional[Gpt5ReasoningEffort] = "low",
        seed: Optional[int] = None,
        timeout: int = 60 * 10,
        service_tier: ServiceTier = "default",
    ):
        """
        Analyzer wrapper around OpenAI chat calls.

        Args:
            model_name (str): OpenAI model to use.
            reasoning_effort (Optional[str]): Reasoning effort hint for GPT‑5 family.
            seed (Optional[int]): Random seed for deterministic outputs.
            timeout (int): Request timeout in seconds (default 600).
            service_tier (ServiceTier): Service tier to use
                for requests (default "default").
        """
        self.model_name = model_name
        self.reasoning_effort = reasoning_effort
        self.seed = seed
        self.timeout = timeout
        self.service_tier = service_tier
        self._usage_log = []

    def __call__(
        self,
        prompt: str,
        system_prompt: str,
        seed: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> str:
        """
        Execute a single analysis request.

        Args:
            prompt (str): User prompt content.
            system_prompt (str): System instructions to guide the model.
            reasoning_effort (Optional[str]): Override reasoning effort for this call.
            seed (Optional[int]): Override random seed for this call.
            timeout (Optional[int]): Override timeout (seconds) for this call.
            service_tier (Optional[ServiceTier]): Override service tier for this call.
        """
        result = chat_with_openai(
            self.model_name,
            system_prompt=system_prompt,
            user_prompt=prompt,
            reasoning_effort=self.reasoning_effort,
            service_tier=self.service_tier,
            seed=seed if seed is not None else self.seed,
            timeout=timeout or self.timeout,
        )

        result_usage = dict(result["usage"]) | dict(result["call_parameters"])
        self._usage_log.append(result_usage)

        return result["content"]

    @property
    def usage(self) -> pd.DataFrame:
        df = pd.DataFrame(self._usage_log)
        keys = [
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "model_name",
            "service_tier",
            "reasoning_effort",
        ]
        df = df[keys]
        return df

    def preprocess_text(self, transcript: pd.DataFrame) -> str:
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
