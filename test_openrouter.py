import os
from dotenv import load_dotenv

load_dotenv()

from jurisconsultor.app.agents.orchestrator import OrchestratorAgent
from jurisconsultor.app.agents.redaccion import RedaccionAgent

def test_openrouter():
    print("Testing OrchestratorAgent with OpenRouter (openai/gpt-oss-20b:free)...")
    orch_agent = OrchestratorAgent()
    result = orch_agent.execute({"consulta": "Quiero demandar a un trabajador que robó material de mi bodega."})
    print(f"Orchestrator Result: {result}\\n")
    
    print("Testing RedaccionAgent with OpenRouter (anthropic/claude-3.5-sonnet)...")
    red_agent = RedaccionAgent()
    result2 = red_agent.execute({"sintesis_argumento": "El trabajador robó material de la bodega y hay evidencia en video."}, {"nivel_riesgo": "alto", "escenarios_riesgo": ["Demanda por despido injustificado si no se levanta el acta correspondiente."]})
    print(f"Redaccion Result: {result2}\\n")

if __name__ == "__main__":
    test_openrouter()
