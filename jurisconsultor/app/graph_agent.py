import os
from typing import Annotated, List, TypedDict
from dotenv import load_dotenv

# Explicitly load .env from the project root directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.mongodb import MongoDBSaver
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

import tools as legacy_tools
import utils
from db_manager import get_memory_db # Import the new db getter for memory

# --- 1. Define the State ---

class AgentState(TypedDict):
    messages: Annotated[list, lambda x, y: x + y]
    access_token: str

# --- 2. Define the Worker Tools ---

@tool
def get_template_placeholders(template_name: str) -> str:
    """Inspecciona una plantilla .docx y devuelve una lista de sus placeholders. Este debe ser el primer paso en la generación de documentos."""
    return legacy_tools.get_template_placeholders(template_name)

@tool
def answer_legal_question_with_rag(question: str) -> str:
    """Usa esta herramienta para responder cualquier pregunta legal, buscando en la base de conocimiento de documentos jurídicos."""
    return utils.answer_with_rag(question)

@tool
def fill_template_and_save_document(template_name: str, project_id: str, document_name: str, context: dict) -> str:
    """El paso final. Rellena y guarda una plantilla .docx con la información proporcionada. Úsese solo después de que toda la información haya sido recopilada."""
    return legacy_tools.fill_template_and_save_document(template_name, document_name, context)

@tool
def list_projects() -> str:
    """Lista todos los proyectos disponibles para el usuario."""
    return legacy_tools.list_projects()

# --- 3. Create the Manager Agent ---

agent_tools = [
    get_template_placeholders,
    answer_legal_question_with_rag,
    fill_template_and_save_document,
    list_projects,
]

llm = ChatOllama(model="llama3", temperature=0, base_url=os.getenv("LLM_URL"))

# Custom ReAct Prompt Template in Spanish
react_prompt_template = """Eres un asistente experto que debe seguir reglas estrictas. Responde a la siguiente pregunta de la mejor manera posible. Tienes acceso a las siguientes herramientas:

{tools}

Usa el siguiente formato para responder:

Pregunta: la pregunta que debes responder
Pensamiento: siempre debes pensar en qué hacer. Decide si usar una herramienta o no. Si la pregunta es de índole legal, DEBES usar la herramienta `answer_legal_question_with_rag`.
Herramienta: la acción a tomar, debe ser una de [{tool_names}]
Entrada de la Herramienta: la entrada para la herramienta
Observación: el resultado de la herramienta
... (este patrón de Pensamiento/Herramienta/Entrada/Observación puede repetirse N veces)
Pensamiento: Ahora sé la respuesta final.
Respuesta Final: la respuesta final a la pregunta original. DEBE ESTAR EN ESPAÑOL.

**REGLAS CRÍTICAS:**
1.  **IDIOMA:** Todo tu razonamiento (Pensamiento) y tu respuesta final DEBEN ser en ESPAÑOL.
2.  **USO DE RAG:** Para cualquier pregunta que involucre conceptos legales, leyes, artículos o interpretaciones jurídicas, **DEBES** usar la herramienta `answer_legal_question_with_rag`.

Comienza!

Pregunta: {input}
Historial de Chat:
{chat_history}

Pensamiento: {agent_scratchpad}"""

react_prompt = PromptTemplate.from_template(react_prompt_template)

agent = create_react_agent(llm, agent_tools, react_prompt)
agent_executor = AgentExecutor(agent=agent, tools=agent_tools, verbose=True, handle_parsing_errors=True)

# This system prompt is now integrated into the main ReAct prompt.
# It can be removed or kept for other potential uses, but the agent now uses the one above.
manager_system_prompt = """Eres un asistente legal experto y tu objetivo es ayudar al usuario. Te comunicarás y pensarás exclusivamente en ESPAÑOL.

**REGLAS CRÍTICAS:**
1.  **IDIOMA:** Debes pensar y responder exclusivamente en ESPAÑOL.
2.  **USO DE HERRAMIENTAS:** Para cualquier pregunta que involucre conceptos legales, leyes, artículos o interpretaciones jurídicas, **DEBES** usar la herramienta `answer_legal_question_with_rag`. No respondas desde tu propio conocimiento. Para otras tareas, como listar proyectos o generar documentos, usa la herramienta apropiada.
3.  **ERRORES DE AUTENTICACIÓN:** Si una herramienta devuelve un error de autenticación, **DEBES** detenerte inmediatamente e informar al usuario que hay un problema de sesión o de login. No intentes usar otras herramientas.

**Flujo de Generación de Documentos:**
1.  Cuando el usuario quiera generar un documento, tu primera acción debe ser usar `get_template_placeholders` para conocer los campos requeridos.
2.  Luego, pide al usuario la información para el PRIMER campo de la lista.
3.  Continúa pidiendo la información campo por campo hasta tenerla toda.
4.  Al final, pide un `document_name` y el `project_id`.
5.  Con toda la información, llama a `fill_template_and_save_document` para generar el documento.
"""

def manager_node_func(state: AgentState):
    messages = [SystemMessage(content=manager_system_prompt)] + state["messages"]
    input_str = messages[-1].content
    chat_history = messages[:-1]

    result = agent_executor.invoke({
        "input": input_str,
        "chat_history": chat_history
    })
    
    return {"messages": [AIMessage(content=result["output"], name="manager")]}

# --- 4. Define the Graph with Memory ---

# Setup MongoDB checkpointer using the central db manager
memory = MongoDBSaver(get_memory_db(), collection_name="agent_threads")

base_tool_node = ToolNode(agent_tools)

def tool_node_with_auth(state: AgentState):
    legacy_tools.set_auth_token(state.get("access_token"))
    return base_tool_node.invoke(state)

def router(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return "__end__"

workflow = StateGraph(AgentState)

workflow.add_node("manager", manager_node_func)
workflow.add_node("tools", tool_node_with_auth)

workflow.set_entry_point("manager")

workflow.add_conditional_edges(
    "manager",
    router,
    {"tools": "tools", "__end__": END}
)

workflow.add_edge("tools", "manager")

# Compile the graph with the MongoDB checkpointer
graph = workflow.compile(checkpointer=memory)

print("Graph fully defined and ready.")