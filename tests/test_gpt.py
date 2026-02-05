import pytest
from unittest.mock import MagicMock
from src.gpt import ChatGPTService


@pytest.fixture
def gpt_service():
    return ChatGPTService(token="fake_token")


def test_set_prompt(gpt_service):
    mock_context = MagicMock()
    mock_context.user_data = {}
    gpt_service.set_prompt(mock_context, "Test Prompt")
    history = mock_context.user_data["gpt_history"]
    assert len(history) == 1
    assert history[0]["role"] == "system"
    assert history[0]["content"] == "Test Prompt"


@pytest.mark.asyncio
async def test_send_question(gpt_service, mocker):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="AI Response"))]

    mocker.patch.object(gpt_service.client.chat.completions, 'create', return_value=mock_response)

    result = await gpt_service.send_question("System prompt", "User question")

    assert result == "AI Response"