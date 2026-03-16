import pytest
from jurisconsultor.app.agents.normativo import NormativoAgent

def test_normativo_initialization():
    agent = NormativoAgent()
    assert agent.model == "openai/gpt-oss-20b:free"
    assert agent.agent_name == "NormativoAgent"

def test_normativo_execute():
    agent = NormativoAgent()
    task = {"type": "normative_search", "query": "leyes de divorcio"}
    result = agent.execute(task)
    
    assert result["status"] == "success"
    assert len(result["normas_aplicables"]) > 0
    assert "jerarquia_normativa" in result
    assert "fuentes_primarias" in result
