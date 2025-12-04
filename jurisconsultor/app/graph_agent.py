import os
import json
import re
from typing import Annotated, List, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.mongodb import MongoDBSaver
import logging

logger = logging.getLogger(__name__)

import tools as legacy_tools
import utils
from db_manager import get_memory_db

# Load environment variables from the root .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
else:
    print(f"Warning: .env file not found at {dotenv_path}")

# --- 1. Define the State ---
class AgentState(TypedDict):
    messages: Annotated[list, lambda x, y: x + y]
    access_token: str
    company_id: str

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
def list_projects(dummy_input: str = "Este es un input dummy") -> str:
    """Lista todos los proyectos disponibles para el usuario."""
    return legacy_tools.list_projects()

@tool
def create_new_project(project_name: str, project_description: str = None) -> str:
    """Crea un nuevo proyecto. Úsese cuando el usuario pida explícitamente crear un proyecto. Devuelve el ID del proyecto creado."""
    return legacy_tools.create_project(project_name, project_description)

@tool
def list_tasks_for_project(project_id: str) -> str:
    """Lista todas las tareas para un proyecto dado. Úsese cuando el usuario pida ver las tareas o el estado de un proyecto."""
    return legacy_tools.list_tasks_for_project(project_id)

# --- 3. Define the Graph Nodes ---
agent_tools = [
    get_template_placeholders,
    answer_legal_question_with_rag,
    fill_template_and_save_document,
    list_projects,
    create_new_project,
    list_tasks_for_project,
]
logger.debug(f"Agent tools initialized: {[t.name for t in agent_tools]}")

# Create a dictionary of tools by name for easy lookup
tools_by_name = {t.name: t for t in agent_tools}

def parse_and_execute_function_from_text(content: str, state: AgentState) -> str:
    """
    Parses function calls from text format like <function>list_projects({"dummy_input": "..."})</function>
    and executes them, returning the result.
    """
    # Extract function name and arguments using regex
    match = re.search(r'<function>(\w+)\((.*?)\)</function>', content, re.DOTALL)
    if not match:
        return None
    
    func_name = match.group(1)
    args_str = match.group(2)
    
    logger.debug(f"Parsed function call: {func_name} with args: {args_str}")
    
    # Get the tool
    if func_name not in tools_by_name:
        logger.error(f"Function {func_name} not found in tools")
        return json.dumps({"error": f"Function {func_name} not found"})
    
    tool = tools_by_name[func_name]
    
    # Set authentication context for legacy tools
    import tools as legacy_tools
    legacy_tools.set_auth_token(state.get("access_token"))
    legacy_tools.set_tenant_id(state.get("company_id"))
    
    try:
        # Parse arguments
        args_dict = json.loads(args_str) if args_str.strip() else {}
        
        # Execute the tool
        result = tool.invoke(args_dict)
        logger.debug(f"Tool {func_name} returned: {result}")
        return result
    except Exception as e:
        logger.error(f"Error executing tool {func_name}: {e}", exc_info=True)
        return json.dumps({"error": f"Error executing {func_name}: {str(e)}"})

# LLM with tools
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_NAME"),
    temperature=0,
    openai_api_key=os.getenv("GROQ_API_KEY"),
    openai_api_base=os.getenv("LLM_URL")
)
llm_with_tools = llm.bind_tools(agent_tools)

# System Prompt
manager_system_prompt = """Eres un asistente legal experto y tu objetivo es ayudar al usuario. Te comunicarás y pensarás exclusivamente en ESPAÑOL.

**REGLAS CRÍTICAS:**
0.  **USO DE HERRAMIENTAS OBLIGATORIO:** Para cualquier solicitud que implique una acción (crear, listar, buscar, etc.), **DEBES** usar una herramienta. Solo responde directamente si el usuario está teniendo una conversación casual. Si la pregunta es un saludo o una pregunta casual como "¿quién eres?" o "¿cómo te llamas?", responde directamente.
    **PROCESAMIENTO DE RESULTADOS DE HERRAMIENTAS:** Después de ejecutar una herramienta y recibir su resultado (Observación), tu siguiente paso DEBE ser analizar esa Observación. Si la Observación contiene la respuesta a la pregunta original del usuario, formula una respuesta clara y concisa para el usuario, comenzando con 'FINAL_ANSWER: '. Si la Observación no es suficiente, puedes decidir si necesitas otra herramienta o más información.
1.  **IDIOMA:** Todo tu razonamiento y tu respuesta final DEBEN ser en ESPAÑOL.
2.  **USO DE RAG:** Para cualquier pregunta que involucre conceptos legales, leyes, artículos o interpretaciones jurídicas, **DEBES** usar la herramienta `answer_legal_question_with_rag`.
    **POST-RAG:** Una vez que la herramienta `answer_legal_question_with_rag` te devuelva una respuesta, asume que esa es la información principal para la pregunta legal del usuario. Tu siguiente paso DEBE ser formular una respuesta final clara y concisa basada en esa información, comenzando con "FINAL_ANSWER: ". NO intentes buscar más información ni usar otras herramientas a menos que la respuesta de RAG sea insuficiente o el usuario pida explícitamente una acción diferente.
3.  **ERRORES DE AUTENTICACIÓN:** Si una herramienta devuelve un error de autenticación, **DEBES** detenerte inmediatamente e informar al usuario que hay un problema de sesión o de login.
4.  **MANEJO DE ERRORES DE HERRAMIENTAS:** Si una herramienta devuelve un error o no encuentra información, informa al usuario sobre el problema y detente. NO intentes responder la pregunta con tu conocimiento general.
5.  **FINALIZACIÓN EXPLÍCITA:** Cuando tengas la respuesta final a la pregunta original del usuario y no necesites usar más herramientas, tu respuesta DEBE comenzar con el prefijo "FINAL_ANSWER: ". Por ejemplo: "FINAL_ANSWER: La respuesta es...". NO uses este prefijo si aún necesitas usar una herramienta o si la conversación continúa.
"""

def manager_node(state: AgentState):
    """Invokes the LLM to determine the next action, with special handling for tool outputs."""
    messages = [SystemMessage(content=manager_system_prompt)] + state["messages"]

    # Check if the last message is a ToolMessage (meaning a tool was just executed)
    if isinstance(state["messages"][-1], ToolMessage):
        last_tool_message = state["messages"][-1]
        
        # Find the original HumanMessage that triggered the tool execution
        original_human_message_content = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                original_human_message_content = msg.content
                break
        
        # Construct a prompt that forces the LLM to summarize the tool output and finalize
        forced_final_prompt_message = HumanMessage(content=(
            f"La herramienta ejecutada ha devuelto el siguiente resultado: "
            f"{last_tool_message.content}\n\n"
            f"Basándote en este resultado y en la pregunta original del usuario ('{original_human_message_content}'), "
            f"formula una respuesta final clara y concisa. Tu respuesta DEBE comenzar con 'FINAL_ANSWER: '."
        ))
        
        # Append this forced prompt to the messages for the LLM
        messages.append(forced_final_prompt_message)
        
        # Create a temporary LLM instance without tools bound for this specific step
        llm_without_tools = ChatOpenAI(
            model=os.getenv("LLM_MODEL_NAME"),
            temperature=0,
            openai_api_key=os.getenv("GROQ_API_KEY"),
            openai_api_base=os.getenv("LLM_URL")
        )

        response = llm_without_tools.invoke(messages)
        
        # Ensure the response is indeed a FINAL_ANSWER, if not, prepend it
        if not response.content.startswith("FINAL_ANSWER:"):
            response.content = "FINAL_ANSWER: " + response.content
        
        # Crucially, ensure no tool_calls are present in this final response
        response.tool_calls = [] 

        return {"messages": [response]}

    # Normal LLM invocation if no specific tool post-processing is needed (i.e., first turn or LLM decides to call a tool)
    print(f"[DEBUG] Manager node invoking LLM with {len(messages)} messages")
    logger.debug(f"Manager node invoking LLM with {len(messages)} messages")
    response = llm_with_tools.invoke(messages)
    print(f"[DEBUG] LLM response type: {type(response)}")
    print(f"[DEBUG] LLM response content: {response.content}")
    print(f"[DEBUG] LLM response has tool_calls: {hasattr(response, 'tool_calls')}")
    logger.debug(f"LLM response type: {type(response)}")
    logger.debug(f"LLM response content: {response.content}")
    logger.debug(f"LLM response has tool_calls: {hasattr(response, 'tool_calls')}")
    if hasattr(response, 'tool_calls'):
        print(f"[DEBUG] LLM tool_calls: {response.tool_calls}")
        logger.debug(f"LLM tool_calls: {response.tool_calls}")
    
    # WORKAROUND: If Groq returned a function call as text instead of tool_calls, parse and execute it
    if '<function>' in response.content and (not hasattr(response, 'tool_calls') or not response.tool_calls):
        logger.info("Detected <function> tag in content without proper tool_calls, parsing and executing manually")
        result = parse_and_execute_function_from_text(response.content, state)
        if result:
            # Create a ToolMessage with the result
            tool_message = ToolMessage(content=result, tool_call_id="manual_parse")
            # Return both the AI message and the tool message
            return {"messages": [response, tool_message]}
    
    return {"messages": [response]}

def tool_node(state: AgentState):
    """
    Executes tools and returns the output. It also handles setting authentication
    before executing any tool.
    """
    logger.debug(f"Entering tool_node with state: {state}")
    # Set authentication context for legacy tools
    legacy_tools.set_auth_token(state.get("access_token"))
    legacy_tools.set_tenant_id(state.get("company_id"))

    # The `ToolNode` will correctly route the tool calls from the last AIMessage
    tool_node_executor = ToolNode(agent_tools)
    
    # Log the tool calls that are about to be executed
    last_ai_message = state["messages"][-1]
    if hasattr(last_ai_message, 'tool_calls') and last_ai_message.tool_calls:
        logger.debug(f"Tool calls to execute: {last_ai_message.tool_calls}")
    else:
        logger.warning("tool_node entered but no tool_calls found in last AI message.")

    output = tool_node_executor.invoke(state)
    logger.debug(f"Exiting tool_node. Type of output: {type(output)}, Output: {output}")
    
    # If the output is a ToolMessage, log its content specifically
    if isinstance(output, dict) and 'messages' in output and isinstance(output['messages'][-1], ToolMessage):
        logger.debug(f"ToolMessage content: {output['messages'][-1].content}")

    return output

# --- 4. Define the Graph Logic ---
def router(state: AgentState) -> str:
    """Determines the next step in the graph."""
    last_message = state["messages"][-1]
    
    # If the last message is a ToolMessage, it means a tool was executed (either normally or via workaround)
    # Route back to manager to process the tool output
    if isinstance(last_message, ToolMessage):
        logger.debug("Last message is ToolMessage, routing back to manager")
        return "manager"
    
    # Check if the LLM made tool calls using the standard format
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        # If the LLM made tool calls, route to the tool node
        return "tools"
    
    # Check if this is a final answer
    if isinstance(last_message, AIMessage) and last_message.content.startswith("FINAL_ANSWER:"):
        # If the LLM provided a final answer, end the conversation
        return END
    
    # Otherwise, the conversation is finished
    return END

# --- 5. Compile the Graph ---
workflow = StateGraph(AgentState)

workflow.add_node("manager", manager_node)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("manager")

workflow.add_conditional_edges(
    "manager",
    router,
    # The router will decide whether to call tools, loop back to manager, or end
    {
        "tools": "tools",
        "manager": "manager",
        END: END
    }
)

# After tools are executed, always return to the manager to process the results
workflow.add_edge("tools", "manager")

# Set up the checkpointer for memory
checkpointer = MongoDBSaver(get_memory_db(), collection_name="agent_threads")

# Compile the graph with the checkpointer
graph = workflow.compile(checkpointer=checkpointer)

print("Graph with pure LangGraph architecture defined and ready.")
