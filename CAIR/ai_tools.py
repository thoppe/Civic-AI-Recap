import os
from pathlib import Path
from typing import Literal, Optional

import tiktoken
from diskcache import Cache
from openai import OpenAI
from pydantic import BaseModel, ConfigDict

# Effort types from docs
Gpt5ReasoningEffort = Literal["minimal", "low", "medium", "high"]
ServiceTier = Literal["auto", "default", "flex", "priority"]
encoding = tiktoken.get_encoding("cl100k_base")


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    completion_tokens_details: Optional[dict] = None
    prompt_tokens_details: Optional[dict] = None

    class Config:
        extra = "allow"


class CallParameters(BaseModel):
    # Pydantic v2 protects the `model_` prefix; allow `model_name` intentionally.
    model_config = ConfigDict(protected_namespaces=())
    model_name: str
    reasoning_effort: Optional[Gpt5ReasoningEffort] = None
    service_tier: Optional[ServiceTier] = None
    was_cached: bool


class OpenAIResponse(BaseModel):
    content: str
    usage: Usage
    call_parameters: CallParameters


def chat_with_openai(
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    reasoning_effort: Gpt5ReasoningEffort | None,
    seed: int = None,
    timeout: int = 60 * 10,
    service_tier: ServiceTier = "default",
    force: bool = False,
    cache_result: bool = True,
) -> dict:
    """
    Call OpenAI ChatGPT with a chosen model, system prompt, and user prompt.

    Args:
        model_name (str): The model name, e.g., "gpt-4o-mini" or "gpt-4.1".
        system_prompt (str): The system role instructions.
        user_prompt (str): The user input prompt.
        reasoning_effort: Optional; one of ["minimal", "low", "medium", "high"].
        seed (int): Optional random state for chatgpt.
        timeout (int): Request timeout in seconds.
        service_tier (str): "auto", "default", "flex", or "priority".
        force (bool): If True, skip cache reads and writes.
        cache_result (bool): If True, store the response in cache.

    Returns:
        dict: Similar to an OpenAIResponse payload.
    """

    # Return a cached answer if possible
    cache = None
    cache_key = None
    if not force or cache_result:
        cache_location = Path("cache") / model_name
        cache = Cache(cache_location)
        cache_key = (
            model_name,
            system_prompt,
            user_prompt,
            reasoning_effort,
            seed,
        )
        if not force and cache_key in cache:
            cached_value = cache[cache_key]
            cached_value["call_parameters"]["was_cached"] = True
            return cached_value

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
        "model": model_name,
        "seed": seed,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    if reasoning_effort:
        request_kwargs["reasoning_effort"] = reasoning_effort

    if service_tier:
        request_kwargs["service_tier"] = service_tier

    response = client.chat.completions.create(
        **request_kwargs,
        timeout=timeout,
    )

    # Build a structured response
    content = response.choices[0].message.content

    usage = dict(response.usage)

    # Cast these objects into a dict
    for key in ["prompt_tokens_details", "completion_tokens_details"]:
        if key in usage:
            usage[key] = dict(usage[key])

    call_parameters = CallParameters(
        model_name=model_name,
        reasoning_effort=reasoning_effort,
        service_tier=service_tier,
        was_cached=False,
    )

    output_model = OpenAIResponse(
        content=content,
        usage=Usage(**usage),
        call_parameters=call_parameters,
    )
    output = output_model.model_dump()
    if cache is not None and cache_key is not None and cache_result:
        cache[cache_key] = output

    return output
