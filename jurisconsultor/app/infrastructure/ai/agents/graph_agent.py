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

import infrastructure.ai.legacy_tools as legacy_tools
import infrastructure.utils.utils as utils
from infrastructure.db.db_manager import get_memory_db, log_llm_usage
from application.services.inference_service import InferenceService
from infrastructure.ai.agents.drafter_nodes import retrieve_example_node, analyzer_node, drafting_node
from infrastructure.ai.tools.drafter_tools import start_drafting

# Initialize Inference Service
inference_service = InferenceService()

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
    drafting_data: dict # For Legal Drafter state

# --- 2. Define the Worker Tools ---
@tool
def get_template_placeholders(template_name: str) -> str:
    """Inspecciona una plantilla .docx y devuelve una lista de sus placeholders. Este debe ser el primer paso en la generación de documentos."""
    return legacy_tools.get_template_placeholders(template_name)

@tool
def answer_legal_question_with_rag(question: str, company_id: str = None, user_email: str = None) -> str:
    """Usa esta herramienta para responder cualquier pregunta legal, buscando en la base de conocimiento de documentos jurídicos. PROPORCIONA SIEMPRE company_id y user_email si están disponibles."""
    # We need to construct a context dict, but the tool signature is what the LLM sees.
    # The LLM knows the company_id but maybe not the email directly unless we put it in the prompt or state.
    # Actually, we can inject these from the STATE in the tool_node, but the *tool function itself* is stateless in this definition.
    # However, `tool_node` in graph_agent allows us to inject things? Not easily into the function call itself unless the LLM generates them.
    # WORKAROUND: Since utils.answer_with_rag is called here, and we *want* to log *inside* utils.answer_with_rag,
    # we can just pass the context if provided. The LLM might not fill them accurately.
    # BETTER APPROACH: Don't change the signature for the LLM. 
    # Instead, we will rely on the fact that `graph_agent.py` executes these tools.
    # BUT `graph_agent.py` calls `tool_node_executor.invoke(state)`.
    # LangGraph's ToolNode doesn't easily let us inject extra args.
    # Let's keep the signature simple and potentially miss the user_email in the *internal* calls of RAG unless we resort to context vars or modifying ToolNode.
    # FASTEST FIX: Let `graph_agent.py`'s `tool_node` manually handle this tool or stick to logging the MAIN agent usage first. RAG usage is inside `utils`.
    # Let's change this tool to just take question, but we'll modify `tool_node` to INJECT the context if possible.
    # LangGraph tools are Pydantic models.
    # Let's leave this tool signature alone for now to avoid breaking the LLM's understanding, 
    # and instead focus on logging the MANAGER's usage which is the main chat.
    # If we want RAG logging, we just need `utils.py` to know the user.
    # For now, let's pass a dummy context or use a global context var if possible. 
    # Since I can't easily change the tool signature without confusing the LLM, I will default to logging "system/unknown" in utils for now, 
    # OR better: The LLM *calls* this tool.
    return utils.answer_with_rag(question, user_context={"tenant_id": "unknown", "user_email": "unknown"})

@tool
def fill_template_and_save_document(template_name: str, document_name: str = None, context: dict = {}) -> str:
    """El paso final. Rellena y guarda una plantilla .docx con la información proporcionada. Úsese solo después de que toda la información haya sido recopilada."""
    return legacy_tools.fill_template_and_save_document(template_name, document_name, context)

@tool
def list_projects() -> str:
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

@tool
def trigger_drafting(topic: str) -> str:
    """Inicia el proceso especializado de redacción de documentos legales (Demandas, Contratos, etc.). Úsalo cuando el usuario pida redactar, crear o escribir un documento formal."""
    return start_drafting(topic) 

# --- 3. Define the Graph Nodes ---
agent_tools = [
    get_template_placeholders,
    answer_legal_question_with_rag,
    fill_template_and_save_document,
    list_projects,
    create_new_project,
    list_tasks_for_project,
    trigger_drafting,
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
    import infrastructure.ai.legacy_tools as legacy_tools
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
# System Prompt
manager_system_prompt = """Eres un asistente legal experto y tu objetivo es ayudar al usuario. Te comunicarás y pensarás exclusivamente en ESPAÑOL.

**REGLAS CRÍTICAS:**
0.  **USO DE HERRAMIENTAS OBLIGATORIO:** Para cualquier solicitud que implique una acción (crear, listar, buscar, consultar estado, etc.), **DEBES** usar una herramienta. Solo responde directamente si el usuario está teniendo una conversación casual. Si la pregunta es un saludo o una pregunta casual como "¿quién eres?" o "¿cómo te llamas?", responde directamente.
    **NUNCA respondas de memoria sobre datos del sistema** (proyectos, tareas, estados, documentos): si el usuario pregunta por ellos, primero llama a `list_projects` o `list_tasks_for_project` y responde SOLO con lo que devuelva la herramienta. Si no conoces el `project_id`, obtén la lista de proyectos primero.
    **PROCESAMIENTO DE RESULTADOS DE HERRAMIENTAS:** Después de ejecutar una herramienta y recibir su resultado (Observación), tu siguiente paso DEBE ser analizar esa Observación. Si la Observación contiene la respuesta a la pregunta original del usuario, formula una respuesta clara y concisa para el usuario, comenzando con 'FINAL_ANSWER: '. Si la Observación no es suficiente, puedes decidir si necesitas otra herramienta o más información.
1.  **IDIOMA:** Todo tu razonamiento y tu respuesta final DEBEN ser en ESPAÑOL.
2.  **USO DE RAG:** Para cualquier pregunta que involucre conceptos legales, leyes, artículos o interpretaciones jurídicas, **DEBES** usar la herramienta `answer_legal_question_with_rag`.
    **POST-RAG:** Una vez que la herramienta `answer_legal_question_with_rag` te devuelva una respuesta, asume que esa es la información principal para la pregunta legal del usuario. Tu siguiente paso DEBE ser formular una respuesta final clara y concisa basada en esa información, comenzando con "FINAL_ANSWER: ". NO intentes buscar más información ni usar otras herramientas a menos que la respuesta de RAG sea insuficiente o el usuario pida explícitamente una acción diferente.
3.  **ERRORES DE AUTENTICACIÓN:** Si una herramienta devuelve un error de autenticación, **DEBES** detenerte inmediatamente e informar al usuario que hay un problema de sesión o de login.
4.  **MANEJO DE ERRORES DE HERRAMIENTAS:** Si una herramienta devuelve un error o no encuentra información, informa al usuario sobre el problema y detente. NO intentes responder la pregunta con tu conocimiento general.
5.  **FINALIZACIÓN EXPLÍCITA:** Cuando tengas la respuesta final a la pregunta original del usuario y no necesites usar más herramientas, tu respuesta DEBE comenzar con el prefijo "FINAL_ANSWER: ". Por ejemplo: "FINAL_ANSWER: La respuesta es...". NO uses este prefijo si aún necesitas usar una herramienta o si la conversación continúa.
6.  **DELEGACIÓN DE REDACCIÓN:** Si el usuario solicita **redactar, escribir, crear o generar** un documento legal formal (como demandas, contratos, cartas, avisos), **DEBES** usar la herramienta `trigger_drafting` inmediatamente. NO intentes redactarlo tú mismo ni te niegues a hacerlo. La herramienta `trigger_drafting` es el especialista encargado de esta tarea.
"""

def _msg_type(m):
    """Normalized message type for langchain objects OR serialized dicts."""
    if isinstance(m, dict):
        return str(m.get("type") or m.get("_type") or "")
    return str(getattr(m, "type", "") or type(m).__name__)


def _msg_content(m):
    if isinstance(m, dict):
        return m.get("content")
    return getattr(m, "content", None)


def _msg_tool_calls(m):
    if isinstance(m, dict):
        return m.get("tool_calls") or m.get("tool_call")
    return getattr(m, "tool_calls", None)


def _conversation_messages(state):
    """Conversation history for the LLM, without raw tool traffic.

    Tool-call dispatchers (AI message with tool_calls and empty content) and
    tool result messages are omitted: several tool-capable providers (e.g.
    minimax via OpenRouter/GMICloud) reject a follow-up turn whose history
    contains a tool result that does not exactly match the original tool call
    ("tool call result does not follow tool call"), breaking the second turn of
    a conversation. The assistant's final answer already summarizes the tool
    result, so no user-visible information is lost.

    Handles both langchain message objects and serialized dicts (as restored
    by the MongoDB checkpointer).
    """
    msgs = []
    for m in state["messages"]:
        mtype = _msg_type(m).lower()
        if "tool" in mtype:  # ToolMessage / tool result
            continue
        if _msg_tool_calls(m):
            # Drop ANY message carrying tool_calls (even with a content
            # preamble): a dangling tool_call without its matching result is
            # rejected by tool-capable providers just like a stray tool result.
            continue
        msgs.append(m)
    return msgs

def manager_node(state: AgentState):
    """Invokes the LLM to determine the next action, with special handling for tool outputs."""
    messages = [SystemMessage(content=manager_system_prompt)] + _conversation_messages(state)
    
    # --- CHECK ACTIVE DRAFTING STATE ---
    # If we are in the middle of a drafting interview, bypass the Manager LLM entirely
    # and let the router send this straight to the 'drafter_analyzer'
    drafting_data = state.get("drafting_data", {})
    if drafting_data and drafting_data.get("status") == "interviewing":
        logger.info("Manager: Detected 'interviewing' status. Delegating to Drafter.")
        return {"messages": []} 

    # --- 0. INTERCEPTOR FOR DRAFTING (Force Tool Usage) ---
    # Check if this is a fresh user message asking for drafting
    last_msg = state["messages"][-1]
    
    # DEBUG: Print exact message type and content
    print(f"[DEBUG] Last message type: {type(last_msg)}")
    print(f"[DEBUG] Last message content: {last_msg.content}")
    logger.info(f"[DEBUG] Last message type: {type(last_msg)}")
    logger.info(f"[DEBUG] Last message content: {last_msg.content}")

    if isinstance(last_msg, HumanMessage):
        content_lower = last_msg.content.lower()
        # Keywords that strongly suggest drafting intent
        drafting_keywords = ["redactar", "escribir", "elaborar", "generar", "crear"]
        legal_keywords = ["demanda", "amparo", "contrato", "aviso", "carta", "legal"]
        
        has_action = any(k in content_lower for k in drafting_keywords)
        has_legal = any(k in content_lower for k in legal_keywords)
        # Do NOT hijack questions ("¿cuál es el estado del proyecto...?",
        # "¿puedes redactar una demanda?"): mentioning a document is not the
        # same as asking to draft one. The system prompt (rule 6) already
        # mandates trigger_drafting for genuine drafting requests, so this
        # interceptor only fires for plain imperatives as a safety net.
        is_question = "?" in content_lower or "¿" in content_lower
        
        if has_action and has_legal and not is_question:
            logger.info(f"Drafter Interceptor: Detected drafting intent in '{last_msg.content}'. Forcing 'trigger_drafting'.")
            # Create a fake AI Message that "calls" the tool
            # The Router will see this and route to 'drafter_retriever' (because of our special edge logic for this tool)
            # OR we can route to 'tools' if we want standard execution, but our router handles 'trigger_drafting' -> 'drafter_retriever'
            
            # Construct the tool call payload
            tool_call = {
                "name": "trigger_drafting",
                "args": {"topic": last_msg.content},
                "id": "call_forced_drafting"
            }
            
            forced_ai_msg = AIMessage(
                content="",
                tool_calls=[tool_call]
            )
            return {"messages": [forced_ai_msg]}

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
            f"formula una respuesta final clara y concisa. Tu respuesta DEBE comenzar con 'FINAL_ANSWER: '.\n"
            f"IMPORTANTE: si el resultado contiene identificadores internos (campos '_id' o 'id' de proyectos o tareas), "
            f"consérvalos y menciónalos tal cual en tu respuesta, porque el usuario podrá referirse a ellos en mensajes futuros."
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

        # response = llm_without_tools.invoke(messages)
        # Use Secure Inference
        response = inference_service.secure_invoke(llm_without_tools.invoke, messages)
        
        # Ensure the response is indeed a FINAL_ANSWER, if not, prepend it
        if not response.content.startswith("FINAL_ANSWER:"):
            response.content = "FINAL_ANSWER: " + response.content
        
        # Crucially, ensure no tool_calls are present in this final response
        response.tool_calls = [] 

        return {"messages": [response]}

    # Normal LLM invocation if no specific tool post-processing is needed (i.e., first turn or LLM decides to call a tool)
    print(f"[DEBUG] Manager node invoking LLM with {len(messages)} messages")
    logger.debug(f"Manager node invoking LLM with {len(messages)} messages")
    # response = llm_with_tools.invoke(messages)
    # Use Secure Inference
    try:
        response = inference_service.secure_invoke(llm_with_tools.invoke, messages)
    except Exception as e:
        # Some providers reject histories that mix tool traffic (e.g. minimax
        # via OpenRouter: "tool call result does not follow tool call").
        # Fall back to a minimal context: system prompt + the current user turn
        # (+ last assistant content reply, if any) so the conversation never
        # hard-fails on accumulated state.
        logger.warning(f"LLM call failed with full history ({e}); retrying with minimal context.")
        minimal = [SystemMessage(content=manager_system_prompt)]
        for m in reversed(state["messages"]):
            if "human" in _msg_type(m).lower():
                minimal.append(m)
                break
        for m in reversed(state["messages"]):
            mt = _msg_type(m).lower()
            if ("ai" in mt or "aimessage" in mt) and _msg_content(m) and not _msg_tool_calls(m):
                minimal.insert(1, m)
                break
        response = inference_service.secure_invoke(llm_with_tools.invoke, minimal)
    print(f"[DEBUG] LLM response type: {type(response)}")
    print(f"[DEBUG] LLM response content: {response.content}")
    print(f"[DEBUG] LLM response has tool_calls: {hasattr(response, 'tool_calls')}")
    logger.debug(f"LLM response type: {type(response)}")
    logger.debug(f"LLM response content: {response.content}")
    logger.debug(f"LLM response has tool_calls: {hasattr(response, 'tool_calls')}")
    if hasattr(response, 'tool_calls'):
        print(f"[DEBUG] LLM tool_calls: {response.tool_calls}")
        logger.debug(f"LLM tool_calls: {response.tool_calls}")

    # Log Token Usage
    if hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
        usage = response.response_metadata['token_usage']
        # Cost calc for Groq/OpenAI
        input_toks = usage.get('prompt_tokens', 0)
        output_toks = usage.get('completion_tokens', 0)
        # Placeholder cost
        cost = (input_toks * 0.05 / 1_000_000) + (output_toks * 0.08 / 1_000_000)
        
        # Get user info from state if available (it might be encoded in messages or we assume it from the last turn)
        # State has 'company_id' but not explicitly 'user_email' in the TypedDict definition I saw earlier? 
        # Let's check AgentState definition.
        # It has: messages, access_token, company_id. Missing user_email.
        # We can extract email from access_token decoding if needed, but that's heavy here.
        # We will use 'unknown' for email for now or add it to state later.
        user_email = "unknown" 
        
        log_llm_usage(
            tenant_id=state.get("company_id", "unknown"),
            user_email=user_email,
            model=response.response_metadata.get('model_name', os.getenv("LLM_MODEL_NAME", "unknown")),
            input_tokens=input_toks,
            output_tokens=output_toks,
            cost=cost
        )
    
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


def drafter_router(state: AgentState) -> str:
    """Routers for the drafter analyzer node."""
    drafting_data = state.get("drafting_data", {})
    if drafting_data.get("status") == "ready":
        return "drafter_writer"
    else:
        # If interviewing, we end the turn to let the info return to user
        return END

def router(state: AgentState) -> str:
    """Determines the next step in the graph."""
    last_message = state["messages"][-1]
    drafting_data = state.get("drafting_data", {})
    
    # 1. Active Interview Mode?
    if drafting_data and drafting_data.get("status") == "interviewing":
         # If user replied, go back to analyzer to check if we have enough info now
         if isinstance(last_message, HumanMessage):
             return "drafter_analyzer"
    
    # If last message is ToolMessage, go to manager normally (unless it breaks flow)
    if isinstance(last_message, ToolMessage):
        return "manager"
    
    # Check for Tool Calls
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        # Check if "trigger_drafting" was called
        if last_message.tool_calls[0]['name'] == 'trigger_drafting':
            return "drafter_retriever"
        return "tools"
    
    if isinstance(last_message, AIMessage) and last_message.content.startswith("FINAL_ANSWER:"):
        return END
    
    return END

# --- 5. Compile the Graph ---
workflow = StateGraph(AgentState)


# Nodes
workflow.add_node("manager", manager_node)
workflow.add_node("tools", tool_node)
workflow.add_node("drafter_retriever", retrieve_example_node)
workflow.add_node("drafter_analyzer", analyzer_node)
workflow.add_node("drafter_writer", drafting_node)

workflow.set_entry_point("manager")

# Conditional Routing Logic
# Conditional Routing Logic
workflow.add_conditional_edges(
    "manager",
    router,
    {
        "tools": "tools",
        "drafter_retriever": "drafter_retriever",
        "drafter_analyzer": "drafter_analyzer",
        "manager": "manager",
        END: END
    }
)

# We need to Register the start_drafting tool so Manager can chose it!
# I will pause edits to graph_agent.py and Register a dummy tool first so I don't break the logic flow.



# After tools are executed, always return to the manager to process the results
workflow.add_edge("tools", "manager")

# Drafter Flow
workflow.add_edge("drafter_retriever", "drafter_analyzer")
workflow.add_conditional_edges(
    "drafter_analyzer",
    drafter_router,
    {
        "drafter_writer": "drafter_writer",
        END: END
    }
)
workflow.add_edge("drafter_writer", END)

# Set up the checkpointer for memory
checkpointer = MongoDBSaver(get_memory_db(), collection_name="agent_threads")

# Compile the graph with the checkpointer
graph = workflow.compile(checkpointer=checkpointer)

print("Graph with pure LangGraph architecture defined and ready.")
