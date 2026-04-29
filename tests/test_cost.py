from unittest.mock import patch

import pandas as pd

from CAIR import Analyze


def _fake_result(content: str, prompt_tokens: int, completion_tokens: int, seed: int):
    return {
        "content": content,
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "prompt_tokens_details": {"cached_tokens": 0},
            "completion_tokens_details": {"reasoning_tokens": 0},
        },
        "call_parameters": {
            "model_name": "gpt-5-mini",
            "reasoning_effort": "high",
            "service_tier": "default",
            "was_cached": False,
            "seed": seed,
        },
    }


@patch("CAIR.understand.chat_with_openai")
def test_analyze_usage_log_can_be_loaded_into_dataframe(mock_chat):
    mock_chat.side_effect = [
        _fake_result("first", prompt_tokens=11, completion_tokens=7, seed=2),
        _fake_result("second", prompt_tokens=13, completion_tokens=5, seed=3),
    ]

    analyze = Analyze(model_name="gpt-5-mini", reasoning_effort="high")

    first = analyze("prompt", "system", seed=2)
    second = analyze("prompt", "system", seed=3)

    assert first == "first"
    assert second == "second"
    assert len(analyze.usage) == 2

    df = pd.DataFrame(analyze.usage)

    assert df["seed"].tolist() == [2, 3]
    assert df["prompt_tokens"].tolist() == [11, 13]
    assert df["completion_tokens"].tolist() == [7, 5]
    assert df["total_tokens"].tolist() == [18, 18]
    assert df["prompt_tokens_details"].tolist() == [{"cached_tokens": 0}] * 2
    assert df["completion_tokens_details"].tolist() == [{"reasoning_tokens": 0}] * 2


@patch("CAIR.understand.chat_with_openai")
def test_analyze_forwards_seed_override_to_chat_with_openai(mock_chat):
    mock_chat.return_value = _fake_result(
        "ok", prompt_tokens=1, completion_tokens=1, seed=7
    )

    analyze = Analyze(model_name="gpt-5-mini", reasoning_effort="high", seed=2)
    analyze("prompt", "system", seed=7)

    assert mock_chat.call_args.kwargs["seed"] == 7
