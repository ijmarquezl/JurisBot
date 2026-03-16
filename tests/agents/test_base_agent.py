import pytest
from unittest.mock import patch, MagicMock
from jurisconsultor.app.agents.base import BaseAgent

class MockAgent(BaseAgent):
    def execute(self, task, context):
        return {"status": "success", "data": "mock_data"}

def test_base_agent_initialization():
    agent = MockAgent()
    assert agent.model == "openai/gpt-oss-20b:free"
    assert agent.agent_name == "MockAgent"
    
def test_base_agent_custom_model():
    agent = MockAgent(model="anthropic/claude-3.5-sonnet")
    assert agent.model == "anthropic/claude-3.5-sonnet"
    
def test_base_agent_execute():
    agent = MockAgent()
    task = {"type": "mock_task"}
    context = {}
    result = agent.execute(task, context)
    assert result["status"] == "success"
    assert result["data"] == "mock_data"

@patch('jurisconsultor.app.agents.base.logger')
def test_log_execution(mock_logger):
    agent = MockAgent()
    task = {"type": "test_type"}
    result = {"status": "success"}
    
    agent.log_execution(task, result)
    
    # Verify the logger was called
    mock_logger.info.assert_called_once_with("[MockAgent] Task: test_type | Status: success")
