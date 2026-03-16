from typing import Dict, Any
from .base import BaseAgent

class OrchestratorAgent(BaseAgent):
    """
    Recibe consulta, analiza área del derecho, descompone en subtareas,
    asigna agentes especializados, genera PLAN DE TRABAJO estructurado.
    """
    
    def __init__(self, model: str = "openai/gpt-oss-20b:free"):
        super().__init__(model=model)
        
    def execute(self, task: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        consulta = task.get("consulta", "")
        self.log_execution(task, {"status": "started"})
        
        from langchain_core.prompts import PromptTemplate
        from pydantic import BaseModel, Field
        from langchain.output_parsers import PydanticOutputParser
        import json
        
        class OrchestratorOutput(BaseModel):
            area_derecho: str = Field(description="Ej. civil, penal, laboral, amparo")
            agentes_requeridos: list[str] = Field(description="Lista de agentes a utilizar: normativo, procedimental, doctrinal, sintesis, adversarial, redaccion")
            plan_trabajo: list[dict] = Field(description="Lista de diccionarios con: paso (int), agente (str), tarea (str)")
            prioridad: str = Field(description="Ej. estándar, urgente, alta")
            
        parser = PydanticOutputParser(pydantic_object=OrchestratorOutput)
        
        prompt = PromptTemplate(
            template="Analiza si la siguiente consulta legal es de índole {area_ejemplo}.\\n"
                     "Determina los agentes requeridos y el plan de trabajo.\\n"
                     "Genera la salida de acuerdo a este formato estricto:\\n{format_instructions}\\n"
                     "Consulta:\\n{consulta}\\n",
            input_variables=["consulta", "area_ejemplo"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        try:
            _input = prompt.format_prompt(consulta=consulta, area_ejemplo="civil, penal, laboral, corporativo, etc")
            response = self.llm.invoke(_input.to_messages())
            parsed_output = parser.parse(response.content)
            
            result = {
                "status": "success",
                "area_derecho": parsed_output.area_derecho,
                "agentes_requeridos": parsed_output.agentes_requeridos,
                "plan_trabajo": parsed_output.plan_trabajo,
                "prioridad": parsed_output.prioridad
            }
        except Exception as e:
            logger.error(f"Error in OrchestratorAgent: {e}")
            result = {"status": "error", "error": str(e), "agentes_requeridos": ["normativo"]}
            
        self.log_execution(task, {"status": "success"})
        return result
