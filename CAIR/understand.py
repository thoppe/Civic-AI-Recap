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
        websearch: bool = False,
        seed: Optional[int] = None,
        timeout: int = 60 * 10,
        service_tier: ServiceTier = "default",
        force: bool = False,
        cache_result: bool = True,
    ):
        """
        Analyzer wrapper around OpenAI chat calls.

        Args:
            model_name (str): OpenAI model to use.
            reasoning_effort (Optional[str]): Reasoning effort hint for GPT‑5 family.
            websearch (bool): If True, enable OpenAI web_search tool.
            seed (Optional[int]): Random seed for deterministic outputs.
            timeout (int): Request timeout in seconds (default 600).
            service_tier (ServiceTier): Service tier to use
                for requests (default "default").
            force (bool): If True, skip cache reads but allow writes.
            cache_result (bool): If True, store the response in cache.
        """
        self.model_name = model_name
        self.reasoning_effort = reasoning_effort
        self.websearch = websearch
        self.seed = seed
        self.timeout = timeout
        self.service_tier = service_tier
        self.force = force
        self.cache_result = cache_result
        self._usage_log = []

    def __call__(
        self,
        prompt: str,
        system_prompt: str,
        seed: Optional[int] = None,
        timeout: Optional[int] = None,
        force: Optional[bool] = None,
        cache_result: Optional[bool] = None,
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
            force (Optional[bool]): Override cache read behavior for this call.
            cache_result (Optional[bool]): Override cache write behavior for this call.
        """
        result = chat_with_openai(
            self.model_name,
            system_prompt=system_prompt,
            user_prompt=prompt,
            reasoning_effort=self.reasoning_effort,
            websearch=self.websearch,
            service_tier=self.service_tier,
            seed=seed if seed is not None else self.seed,
            timeout=timeout or self.timeout,
            force=self.force if force is None else force,
            cache_result=(
                self.cache_result if cache_result is None else cache_result
            ),
        )
        result_usage = dict(result["usage"]) | dict(result["call_parameters"])
        self._usage_log.append(result_usage)

        return result["content"]

    @property
    def usage(self) -> list[dict]:
        return self._usage_log

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
