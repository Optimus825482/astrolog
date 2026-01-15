import pytest
from unittest.mock import patch
from ai_interpretations import call_llm_with_fallback, get_ai_interpretation_engine

def test_ai_fallback_chain_success():
    """Test the fallback chain when the first provider succeeds."""
    with patch("ai_interpretations.call_deepseek") as mock_ds:
        mock_ds.return_value = "DeepSeek response"

        result = call_llm_with_fallback("Test prompt")
        assert result == "DeepSeek response"
        mock_ds.assert_called_once()

def test_ai_fallback_chain_trigger():
    """Test the fallback chain when the first provider fails."""
    with patch("ai_interpretations.call_deepseek") as mock_ds, \
         patch("ai_interpretations.call_openrouter") as mock_openrouter:

        mock_ds.side_effect = Exception("DeepSeek Down")
        mock_openrouter.return_value = "OpenRouter rescue"

        result = call_llm_with_fallback("Test prompt")
        assert result == "OpenRouter rescue"
        assert mock_ds.call_count == 2  # 2 attempts per provider
        mock_openrouter.assert_called_once()

def test_get_ai_interpretation_engine_integration():
    """Test the main engine function integration."""
    astro_data = {"Sun": {"sign": "Aries", "house": 1}}
    with patch("ai_interpretations.call_llm_with_fallback") as mock_fallback:
        mock_fallback.return_value = "Engine response"

        response = get_ai_interpretation_engine(astro_data, "natal", "John Doe")

        assert response["success"] is True
        assert response["interpretation"] == "Engine response"
        assert response["interpretation_type"] == "natal"
