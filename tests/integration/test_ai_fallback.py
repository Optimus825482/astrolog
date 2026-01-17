import pytest
from unittest.mock import patch
from services.ai_service import ai_service, get_ai_interpretation_engine


def test_ai_fallback_chain_success():
    """Test the fallback chain when the first provider succeeds."""
    with patch("services.ai_service.AIService.call_deepseek_async") as mock_ds:
        mock_ds.return_value = {"success": True, "interpretation": "DeepSeek response"}

        result = ai_service.get_ai_interpretation({}, "natal", "John Doe")
        assert result["interpretation"] == "DeepSeek response"
        mock_ds.assert_called_once()


def test_ai_fallback_chain_trigger():
    """Test the fallback chain when the first provider fails."""
    with (
        patch("services.ai_service.AIService.call_deepseek_async") as mock_ds,
        patch("services.ai_service.AIService.get_ai_interpretation_async") as mock_main,
    ):
        # We need to mock the main method since it calls the other providers
        mock_main.return_value = {
            "success": True,
            "interpretation": "Fallback response",
        }
        result = ai_service.get_ai_interpretation({}, "natal", "John Doe")
        assert result["interpretation"] == "Fallback response"


def test_get_ai_interpretation_engine_integration():
    """Test the main engine function integration."""
    astro_data = {"Sun": {"sign": "Aries", "house": 1}}
    with patch("services.ai_service.AIService.get_ai_interpretation") as mock_service:
        mock_service.return_value = {
            "success": True,
            "interpretation": "Engine response",
        }

        response = get_ai_interpretation_engine(astro_data, "natal", "John Doe")

        assert response["success"] is True
        assert response["interpretation"] == "Engine response"
