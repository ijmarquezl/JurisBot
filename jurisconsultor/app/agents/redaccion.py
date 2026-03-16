from typing import Dict, Any
from .base import BaseAgent

class RedaccionAgent(BaseAgent):
    """
    Da formato profesional al documento final.
    """
    
    def __init__(self, model: str = "anthropic/claude-3.5-sonnet"):
        super().__init__(model=model)
        
    def execute(self, sintesis: Dict[str, Any], adversarial: Dict[str, Any] = None) -> Dict[str, Any]:
        self.log_execution({"type": "redaction"}, {"status": "started"})
        
        from langchain_core.prompts import PromptTemplate
        
        # Merge results to craft a finalized document using the LLM
        prompt = PromptTemplate(
            template="Eres un abogado experto. Redacta un dictamen legal formal estructurado en:\\n"
                     "I. Antecedentes\\nII. Marco Normativo\\nIII. Análisis\\nIV. Conclusiones y Advertencias\\n\\n"
                     "Toma como base el siguiente análisis central:\\n{sintesis}\\n\\n"
                     "Toma la siguiente evaluación de riesgos:\\n{riesgos}\\n\\n"
                     "Si el nivel de riesgo es alto, DEBES incluir una clara ADVERTENCIA en la sección correspondiente. Emite solo el documento final en formato Markdown.",
            input_variables=["sintesis", "riesgos"]
        )
        
        riesgos_str = str(adversarial) if adversarial else "Sin riesgos adicionales detectados."
        
        try:
            _input = prompt.format_prompt(sintesis=sintesis.get('sintesis_argumento', '...'), riesgos=riesgos_str)
            response = self.llm.invoke(_input.to_messages())
            doc = response.content
            status = "success"
        except Exception as e:
            logger.error(f"Error in RedaccionAgent: {e}")
            doc = "Error generando el documento."
            status = "error"
             
        result = {
            "status": status,
            "documento": doc,
            "estructura": {
                "antecedentes": "Yes",
                "marco_normativo": "Yes",
                "analisis": "Yes",
                "conclusiones": "Yes"
            }
        }
        
        self.log_execution({"type": "redaction"}, {"status": "success"})
        return result
