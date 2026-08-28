import pytest
from unittest.mock import patch
from jurisconsultor.app.workflows import legal_workflow

PLAN = {
    "status": "success",
    "area_derecho": "civil",
    "agentes_requeridos": ["normativo", "procedimental"],
    "tipo_documento": "dictamen",
    "prioridad": "estándar",
}

def test_legal_workflow_execution():
    """
    Runs the full multi-agent workflow with the agent classes mocked so the
    test is hermetic: no LLM calls, no network, no API keys required.
    The real QualityGateSystem still validates the assembled document.
    """
    with patch("jurisconsultor.app.workflows.legal_workflow.OrchestratorAgent") as OrchCls, \
         patch("jurisconsultor.app.workflows.legal_workflow.NormativoAgent") as NormCls, \
         patch("jurisconsultor.app.workflows.legal_workflow.ProcedimentalAgent") as ProcCls, \
         patch("jurisconsultor.app.workflows.legal_workflow.SintesisAgent") as SintCls, \
         patch("jurisconsultor.app.workflows.legal_workflow.AdversarialAgent") as AdvCls, \
         patch("jurisconsultor.app.workflows.legal_workflow.RedaccionAgent") as RedCls:

        OrchCls.return_value.execute.return_value = PLAN
        NormCls.return_value.execute.return_value = {"status": "success", "fundamentos": ["Art. X"]}
        ProcCls.return_value.execute.return_value = {"status": "success", "procedimiento": ["paso 1"]}
        SintCls.return_value.execute.return_value = {"sintesis_argumento": "Argumento de prueba.", "status": "success"}
        AdvCls.return_value.execute.return_value = {"nivel_riesgo": "bajo", "escenarios_riesgo": []}
        RedCls.return_value.execute.return_value = {"documento": "# Dictamen Legal\nI. Antecedentes", "status": "success"}

        result = legal_workflow.process_legal_consultation("consulta simple", "t_1")

    assert result["status"] == "success"
    assert "document" in result
    assert "audit_trail" in result

    audit = result["audit_trail"]
    assert "plan" in audit
    assert "agent_results" in audit
    assert len(audit["agent_results"]) > 0
    assert audit["gates"]["approved"] is True
