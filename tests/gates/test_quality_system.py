import pytest
from jurisconsultor.app.gates.quality_system import QualityGateSystem

def test_gate1_valid_sources():
    system = QualityGateSystem()
    doc = {
        "citas": [
            {"es_primaria": True, "url": "https://gov.mx", "vigente": True}
        ]
    }
    res = system._gate1_fuentes(doc)
    assert res["passed"] == True

def test_gate1_invalid_sources():
    system = QualityGateSystem()
    doc = {
        "citas": [
            {"es_primaria": False, "url": "", "vigente": True}
        ]
    }
    res = system._gate1_fuentes(doc)
    assert res["passed"] == False
    
def test_validate_all_gates():
    system = QualityGateSystem()
    doc = {
        "citas": [{"es_primaria": True, "url": "http://ok", "vigente": True}],
        "coherencia_valida": True,
        "formato": "Estructura I-V",
        "aprobacion_humana": True
    }
    res = system.validate(doc, original_query="Test query")
    assert res["can_proceed"] == True
    assert res["gates_passed"] == 5
    
def test_validate_fail_gate():
    system = QualityGateSystem()
    doc = {
        "citas": [{"es_primaria": True, "url": "http://ok", "vigente": True}],
        "coherencia_valida": False, # Will fail gate 2
        "formato": "Estructura I-V",
        "aprobacion_humana": True
    }
    res = system.validate(doc, original_query="Test query")
    assert res["can_proceed"] == False
    assert res["gates_passed"] == 4
    assert len(res["gates_failed"]) == 1
    assert res["gates_failed"][0]["gate"] == 2
