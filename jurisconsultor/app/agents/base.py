from abc import ABC, abstractmethod
from typing import Dict, Any
import os
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Clase base para todos los agentes de JurisBot vinculados a OpenRouter"""
    
    def __init__(self, model: str = "openai/gpt-oss-20b:free"):
        self.model = model
        self.agent_name = self.__class__.__name__
        self.llm = self._initialize_llm()
        
    def _initialize_llm(self):
        """Inicializa el modelo LLM a través de OpenRouter o Anthropic"""
        if "claude" in self.model.lower():
            from langchain_anthropic import ChatAnthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                logger.warning("ANTHROPIC_API_KEY no encontrada. El LLM podría fallar.")
                
            model_name = self.model.replace("anthropic/", "")
            return ChatAnthropic(
                model_name=model_name,
                temperature=0,
                anthropic_api_key=api_key
            )
        else:
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                logger.warning("OPENROUTER_API_KEY no encontrada. El LLM podría fallar.")
                
            return ChatOpenAI(
                model=self.model,
                temperature=0,
                openai_api_key=api_key,
                openai_api_base="https://openrouter.ai/api/v1"
            )
    
    @abstractmethod
    def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la tarea asignada y retorna resultado estructurado"""
        pass
    
    def log_execution(self, task: Dict, result: Dict):
        """Registra ejecución en audit trail"""
        logger.info(f"[{self.agent_name}] Task: {task.get('type')} | Status: {result.get('status')}")
