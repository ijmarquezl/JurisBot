from typing import Dict, Any
from .base import BaseAgent
import logging
import sys
import os

# Ensure the app folder is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.utils.template_manager import TemplateManager

logger = logging.getLogger(__name__)

class RedaccionAgent(BaseAgent):
    """
    Da formato profesional al documento final.
    """
    
    def __init__(self, model: str = "anthropic/claude-3.5-sonnet"):
        super().__init__(model=model)
        self.template_manager = TemplateManager()
        
    def execute(self, sintesis: Dict[str, Any], adversarial: Dict[str, Any] = None, tipo_documento: str = None) -> Dict[str, Any]:
        self.log_execution({"type": "redaction"}, {"status": "started"})
        
        from langchain_core.prompts import PromptTemplate
        
        template_text = None
        if tipo_documento:
            template_text = self.template_manager.get_template_text(tipo_documento)
        
        if template_text:
            template_instruction = (
                f"Eres un abogado experto redactando un documento formal del tipo: {tipo_documento}.\n\n"
                "A continuación se te provee una PLANTILLA DE MUESTRA EXACTA que debes usar como base y guía (su estructura, lenguaje y formato).\n"
                "Adopta el mismo formato y estilo formal. Extrae la información de los antecedentes proporcionados e insértalos en las posiciones \n"
                "adecuadas según la plantilla. \n"
                "MUY IMPORTANTE: Cuando falten datos específicos (como fechas exactas, nombres completos o domicilios) \n"
                "NO los inventes; déjalos entre corchetes [ASÍ] para que el usuario los llene posteriormente.\n\n"
                f"=== PLANTILLA DE REFERENCIA ===\n{template_text}\n==============================\n\n"
                "Toma como base el siguiente análisis central (hechos y pretensiones):\n{sintesis}\n\n"
                "Toma la siguiente evaluación de riesgos (si los hay, inclúyelos astutamente o emite prevenciones):\n{riesgos}\n\n"
                "Emite solo el documento final redactado en formato Markdown, sin explicaciones ni saludos."
            )
        else:
            template_instruction = (
                "Eres un abogado experto. Redacta un dictamen legal formal estructurado en:\n"
                "I. Antecedentes\nII. Marco Normativo\nIII. Análisis\nIV. Conclusiones y Advertencias\n\n"
                "Toma como base el siguiente análisis central:\n{sintesis}\n\n"
                "Toma la siguiente evaluación de riesgos:\n{riesgos}\n\n"
                "Si el nivel de riesgo es alto, DEBES incluir una clara ADVERTENCIA en la sección correspondiente. "
                "Emite solo el documento final en formato Markdown."
            )

        prompt = PromptTemplate(
            template=template_instruction,
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
            "tipo_documento_utilizado": tipo_documento if template_text else "genérico/dictamen"
        }
        
        self.log_execution({"type": "redaction"}, {"status": "success"})
        return result
