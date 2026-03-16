from typing import Dict, Any
from .base import BaseAgent

class DoctrinaAgent(BaseAgent):
    """
    Especialista en tesis de jurisprudencia, tesis aisladas y doctrina.
    """
    
    def __init__(self, model: str = "openai/gpt-oss-20b:free"):
        super().__init__(model=model)
        
    def execute(self, task: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        self.log_execution(task, {"status": "started"})
        
        result = {
            "status": "success",
            "tesis_jurisprudencia": [
                {
                    "numero": "1a./J. 12/2023",
                    "tipo": "jurisprudencia",
                    "instancia": "SCJN",
                    "fecha": "2023-05-10",
                    "materia": "Civil",
                    "criterio": "Las costas proceden cuando hay condena total.",
                    "aplicabilidad": "Directamente aplicable al caso"
                }
            ],
            "doctrina_relevante": ["Tratado de Derecho Civil por Rojina Villegas"],
            "criterios_contrarios": ["Tesis aislada CCVII/2020 de tribunal colegiado"],
            "tendencia_actual": "La Suprema Corte ha sido estricta en la condena en costas."
        }
        
        self.log_execution(task, {"status": "success"})
        return result
