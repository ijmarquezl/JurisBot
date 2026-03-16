import pytest
from jurisconsultor.app.agents.adversarial import AdversarialAgent

def test_adversarial_initialization():
    agent = AdversarialAgent()
    assert agent.model == "openai/gpt-oss-20b:free"
    assert agent.agent_name == "AdversarialAgent"

def test_adversarial_execute():
    agent = AdversarialAgent()
    task = {"type": "adversarial_review", "sintesis_argumento": "Existen riesgos inminentes"}
    result = agent.execute(task)
    
    assert result["status"] == "success"
    assert len(result["debilidades_identificadas"]) > 0
    # Because 'riesgo' is in sintesis_argumento, risk should be 'alto'
    assert result["nivel_riesgo"] == "alto"
    
def test_adversarial_execute_low_risk():
    agent = AdversarialAgent()
    task = {"type": "adversarial_review", "sintesis_argumento": "Todo es un camino seguro"}
    result = agent.execute(task)
    
    assert result["status"] == "success"
    assert result["nivel_riesgo"] == "medio" # Default
