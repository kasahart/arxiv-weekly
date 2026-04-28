import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from model_utils import supports_custom_temperature, build_token_kwargs, build_chat_kwargs


class TestSupportsCustomTemperature:
    def test_gpt4o_supports_temperature(self):
        assert supports_custom_temperature("gpt-4o") is True

    def test_gpt4o_mini_supports_temperature(self):
        assert supports_custom_temperature("gpt-4o-mini") is True

    def test_gpt5_does_not_support_temperature(self):
        assert supports_custom_temperature("gpt-5") is False

    def test_gpt5_turbo_does_not_support_temperature(self):
        assert supports_custom_temperature("gpt-5-turbo") is False

    def test_o1_supports_temperature(self):
        # o1 does not start with gpt-5, so supports temperature
        assert supports_custom_temperature("o1") is True


class TestBuildTokenKwargs:
    def test_gpt4o_uses_max_tokens(self):
        result = build_token_kwargs("gpt-4o", 1000)
        assert result == {"max_tokens": 1000}

    def test_gpt5_uses_max_completion_tokens(self):
        result = build_token_kwargs("gpt-5", 500)
        assert result == {"max_completion_tokens": 500}

    def test_o1_uses_max_completion_tokens(self):
        result = build_token_kwargs("o1", 200)
        assert result == {"max_completion_tokens": 200}

    def test_o3_uses_max_completion_tokens(self):
        result = build_token_kwargs("o3", 100)
        assert result == {"max_completion_tokens": 100}

    def test_o4_uses_max_completion_tokens(self):
        result = build_token_kwargs("o4", 300)
        assert result == {"max_completion_tokens": 300}


class TestBuildChatKwargs:
    def test_gpt4o_with_temperature(self):
        result = build_chat_kwargs("gpt-4o", 1000, temperature=0.3)
        assert result == {"max_tokens": 1000, "temperature": 0.3}

    def test_gpt4o_without_temperature(self):
        result = build_chat_kwargs("gpt-4o", 1000)
        assert result == {"max_tokens": 1000}
        assert "temperature" not in result

    def test_gpt5_ignores_temperature(self):
        result = build_chat_kwargs("gpt-5", 500, temperature=0.5)
        assert result == {"max_completion_tokens": 500}
        assert "temperature" not in result

    def test_temperature_none_is_excluded(self):
        result = build_chat_kwargs("gpt-4o", 800, temperature=None)
        assert "temperature" not in result
