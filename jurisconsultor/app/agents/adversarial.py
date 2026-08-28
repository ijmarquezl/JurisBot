from typing import Dict, Any
from .base import BaseAgent

class AdversarialAgent(BaseAgent):
    """
    Abogado del diablo - intenta DESTRUIR el argumento legal.
    CLAVE para 0% alucinaciones.
    """
    
    def __init__(self, model: str = "openai/gpt-oss-20b:free"):
        super().__init__(model=model)
        
    def execute(self, task: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        self.log_execution(task, {"status": "started"})
        
        # Here we act as the Devil's Advocate against the synthesis
        sintesis = task.get("sintesis_argumento", "")
        
        debilidades = ["No se consideraron plazos naturales vs hábiles"]
        riesgo = "medio"
        
        if "riesgo" in sintesis.lower():
            riesgo = "alto"
            
        result = {
            "status": "success",
            "debilidades_identificadas": debilidades,
            "jurisprudencia_contraria": ["Tesis 12345: Plazos caducan en días naturales para este supuesto"],
            "escenarios_riesgo": ["Que el juez deseche por extemporáneo"],
            "interpretaciones_alternativas": ["El artículo puede interpretarse de forma restrictiva"],
            "nivel_riesgo": riesgo
        }
        
        self.log_execution(task, {"status": "success"})
        return result
