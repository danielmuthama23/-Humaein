import pytest
from ..email_action_agent import EmailAgent, mock_llm_parse_instruction

def test_mock_llm_parse_instruction():
    instruction = "Send an email to alice@example.com about the meeting at 2pm"
    params = mock_llm_parse_instruction(instruction)
    assert params['to'] == "alice@example.com"
    assert params['subject'] == "Automated Email"
    assert "meeting at 2pm" in params['body']

# Note: Full Selenium tests require a browser environment; use mocking libraries like `unittest.mock`
def test_agent_init():
    agent = EmailAgent("gmail")
    assert agent.provider == "gmail"
    assert agent.driver is not None