import pytest
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage
from jurisconsultor.app.agents.redaccion import RedaccionAgent

def test_redaccion_initialization():
    agent = RedaccionAgent()
    assert agent.model == "anthropic/claude-3.5-sonnet"
    assert agent.agent_name == "RedaccionAgent"

def test_redaccion_execute_low_risk():
    agent = RedaccionAgent()
    agent.llm.invoke = MagicMock(return_value=AIMessage(content="# Dictamen Legal\\nI. Antecedentes\\nSin novedades."))

    sintesis = {"sintesis_argumento": "Este es el argumento."}
    adversarial = {"nivel_riesgo": "bajo"}
    result = agent.execute(sintesis, adversarial)
    
    assert result["status"] == "success"
    assert "ADVERTENCIA DE RIESGO ALTO" not in result["documento"]

def test_redaccion_execute_high_risk():
    agent = RedaccionAgent()
    agent.llm.invoke = MagicMock(return_value=AIMessage(content="# Dictamen Legal\\n**ADVERTENCIA DE RIESGO ALTO**\\nFalla A detectada."))

    sintesis = {"sintesis_argumento": "Este es el argumento."}
    adversarial = {"nivel_riesgo": "alto", "escenarios_riesgo": ["Falla A", "Falla B"]}
    result = agent.execute(sintesis, adversarial)
    
    assert result["status"] == "success"
    assert "ADVERTENCIA DE RIESGO ALTO" in result["documento"]
    assert "Falla A" in result["documento"]
