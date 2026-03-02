import unittest
from types import SimpleNamespace
from unittest.mock import patch

from CAIR.ai_tools import chat_with_openai
from CAIR.understand import Analyze


class FakeCompletions:
    def __init__(self):
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
            usage={
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "total_tokens": 2,
            },
        )


class FakeResponses:
    def __init__(self):
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return SimpleNamespace(
            output_text="ok",
            usage={
                "input_tokens": 1,
                "output_tokens": 1,
                "total_tokens": 2,
                "input_tokens_details": {"cached_tokens": 0},
                "output_tokens_details": {"reasoning_tokens": 0},
            },
        )


class FakeClient:
    def __init__(self):
        self.chat = SimpleNamespace(completions=FakeCompletions())
        self.responses = FakeResponses()


class TestWebSearchOption(unittest.TestCase):
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("CAIR.ai_tools.OpenAI")
    def test_chat_with_openai_includes_tools_when_websearch_true(self, mock_openai):
        fake_client = FakeClient()
        mock_openai.return_value = fake_client

        chat_with_openai(
            model_name="gpt-5-mini",
            system_prompt="system",
            user_prompt="user",
            reasoning_effort="low",
            websearch=True,
            force=True,
            cache_result=False,
        )

        self.assertIn("tools", fake_client.responses.last_kwargs)
        self.assertEqual(
            fake_client.responses.last_kwargs["tools"],
            [{"type": "web_search"}],
        )
        self.assertIsNone(fake_client.chat.completions.last_kwargs)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("CAIR.ai_tools.OpenAI")
    def test_chat_with_openai_omits_tools_when_websearch_false(
        self, mock_openai
    ):
        fake_client = FakeClient()
        mock_openai.return_value = fake_client

        chat_with_openai(
            model_name="gpt-5-mini",
            system_prompt="system",
            user_prompt="user",
            reasoning_effort="low",
            websearch=False,
            force=True,
            cache_result=False,
        )

        self.assertNotIn("tools", fake_client.chat.completions.last_kwargs)

    @patch("CAIR.understand.chat_with_openai")
    def test_analyze_passes_websearch_to_chat_with_openai(self, mock_chat):
        mock_chat.return_value = {
            "content": "ok",
            "usage": {
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "total_tokens": 2,
            },
            "call_parameters": {
                "model_name": "gpt-5-mini",
                "reasoning_effort": "low",
                "service_tier": "default",
                "was_cached": False,
            },
        }

        analyze = Analyze(websearch=True)
        analyze(prompt="user", system_prompt="system")

        self.assertTrue(mock_chat.call_args.kwargs["websearch"])
