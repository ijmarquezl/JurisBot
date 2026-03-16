import pytest
from jurisconsultor.app.agents.document_manager import DocumentManagerAgent

def test_document_manager_initialization():
    agent = DocumentManagerAgent()
    assert agent.model == "openai/gpt-oss-20b:free"
    assert agent.agent_name == "DocumentManagerAgent"
    assert "dof" in agent.scrapers

def test_document_manager_scrape_valid():
    agent = DocumentManagerAgent()
    task = {"operation": "scrape_source", "source": "dof"}
    result = agent.execute(task)
    
    assert result["status"] == "success"
    assert result["documents_found"] == 1
    assert result["documents_processed"] == 1

def test_document_manager_scrape_invalid():
    agent = DocumentManagerAgent()
    task = {"operation": "scrape_source", "source": "fuente_falsa"}
    result = agent.execute(task)
    
    assert result["status"] == "error"
    assert "not supported" in result["error"]
