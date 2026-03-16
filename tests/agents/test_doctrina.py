import pytest
from jurisconsultor.app.agents.doctrina import DoctrinaAgent

def test_doctrina_initialization():
    agent = DoctrinaAgent()
    assert agent.model == "openai/gpt-oss-20b:free"
    assert agent.agent_name == "DoctrinaAgent"

def test_doctrina_execute():
    agent = DoctrinaAgent()
    task = {"type": "doctrina_query", "query": "costas en juicios civiles"}
    result = agent.execute(task)
    
    assert result["status"] == "success"
    assert len(result["tesis_jurisprudencia"]) > 0
    assert "tendencia_actual" in result
