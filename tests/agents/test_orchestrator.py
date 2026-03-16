import pytest
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage
from jurisconsultor.app.agents.orchestrator import OrchestratorAgent

def test_orchestrator_initialization():
    agent = OrchestratorAgent()
    assert agent.model == "openai/gpt-oss-20b:free"
    assert agent.agent_name == "OrchestratorAgent"

def test_orchestrator_execute_civil():
    agent = OrchestratorAgent()
    mock_response = '{"area_derecho": "civil", "agentes_requeridos": ["normativo", "procedimental"], "plan_trabajo": [{"paso": 1, "agente": "normativo", "tarea": "leyes"}], "prioridad": "estándar"}'
    agent.llm.invoke = MagicMock(return_value=AIMessage(content=mock_response))
    
    task = {"type": "consultation", "consulta": "divorcio incausado en queretaro"}
    result = agent.execute(task)
    
    assert result["status"] == "success"
    assert result["area_derecho"] == "civil"
    assert "normativo" in result["agentes_requeridos"]
    assert "procedimental" in result["agentes_requeridos"]

def test_orchestrator_execute_laboral():
    agent = OrchestratorAgent()
    mock_response = '{"area_derecho": "laboral", "agentes_requeridos": ["normativo", "procedimental"], "plan_trabajo": [{"paso": 1, "agente": "normativo", "tarea": "leyes"}], "prioridad": "estándar"}'
    agent.llm.invoke = MagicMock(return_value=AIMessage(content=mock_response))
    
    task = {"type": "consultation", "consulta": "despido injustificado laboral"}
    result = agent.execute(task)
    
    assert result["status"] == "success"
    assert result["area_derecho"] == "laboral"
    assert "normativo" in result["agentes_requeridos"]
    assert "doctrinal" not in result["agentes_requeridos"]
