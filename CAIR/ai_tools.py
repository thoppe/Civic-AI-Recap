import os
from pathlib import Path
from typing import Literal

import tiktoken
from diskcache import Cache
from openai import OpenAI

# Effort types from docs
ReasoningEffort = Literal["low", "medium", "high"]
Gpt5ReasoningEffort = Literal["minimal", "low", "medium", "high"]
encoding = tiktoken.get_encoding("cl100k_base")


def chat_with_openai(
    model: str,
    system_prompt: str,
    user_prompt: str,
    reasoning_effort: Gpt5ReasoningEffort | None,
    seed: int = None,
    cache_expire: int = 60 * 60,
):
    """
    Call OpenAI ChatGPT with a chosen model, system prompt, and user prompt.

    Args:
        model (str): The model name, e.g., "gpt-4o-mini" or "gpt-4.1".
        system_prompt (str): The system role instructions.
        user_prompt (str): The user input prompt.
        reasoning_effort: ["minimal", "low", "medium", "high"]
        seed (int): Random state for chatgpt
        cache_expire (int): Pull value from cache, set to None to force.

    Returns:
        str: The assistant's reply.
    """

    # Return a cached answer if possible
    cache_location = Path("cache") / model
    cache = Cache(cache_location, expire=cache_expire)
    key = (model, system_prompt, user_prompt, reasoning_effort)
    if key in cache and cache_expire is not None:
        return cache[key]

    # Make sure we don't have too many input tokens
    system_n = len(encoding.encode(system_prompt))
    prompt_n = len(encoding.encode(user_prompt))
    total_tokens = system_n + prompt_n
    if total_tokens > 400_000:
        raise ValueError(f"Used {total_tokens} tokens, limit 400,000")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Missing OPENAI_API_KEY in environment variables."
        )

    client = OpenAI(api_key=api_key)

    request_kwargs = {
        "model": model,
        "seed": seed,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    if reasoning_effort:
        request_kwargs["reasoning_effort"] = reasoning_effort

    response = client.chat.completions.create(**request_kwargs)

    cache[key] = response.choices[0].message.content
    return cache[key]
