import pytest
from jurisconsultor.app.agents.sintesis import SintesisAgent

def test_sintesis_initialization():
    agent = SintesisAgent()
    assert agent.model == "anthropic/claude-3.5-sonnet"
    assert agent.agent_name == "SintesisAgent"

def test_sintesis_execute():
    agent = SintesisAgent()
    plan = {"type": "synthesis"}
    # Mocking results received from other agents
    context = {"results": [{"normas_aplicables": ["Art 1"]}, {"via_procesal": "Civil"}]}
    result = agent.execute(plan, context)
    
    assert result["status"] == "success"
    assert "Normativa Validada" in result["verificaciones_pasadas"]
    assert result["recomendacion"] in ["proceder", "solicitar_revision", "detener"]
