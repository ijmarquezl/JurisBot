import pytest
from jurisconsultor.app.agents.procedimental import ProcedimentalAgent

def test_procedimental_initialization():
    agent = ProcedimentalAgent()
    assert agent.model == "openai/gpt-oss-20b:free"
    assert agent.agent_name == "ProcedimentalAgent"

def test_procedimental_execute():
    agent = ProcedimentalAgent()
    task = {"type": "procedural_definition", "query": "proceso de asimilados a salarios"}
    result = agent.execute(task)
    
    assert result["status"] == "success"
    assert "via_procesal" in result
    assert "pasos_procesales" in result
    assert len(result["pasos_procesales"]) > 0
