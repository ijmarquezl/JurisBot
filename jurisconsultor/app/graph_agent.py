import os
from typing import Annotated, List, TypedDict
from dotenv import load_dotenv

# Explicitly load .env from the parent directory (jurisconsultor/)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.mongodb import MongoDBSaver
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub

from app import tools as legacy_tools
from app import utils
from app.db_manager import get_memory_db # Import the new db getter for memory

# --- 1. Define the State ---

class AgentState(TypedDict):
    messages: Annotated[list, lambda x, y: x + y]
    access_token: str

# --- 2. Define the Worker Tools ---

@tool
def get_template_placeholders(template_name: str) -> str:
    """Inspects a .docx template and returns a list of its placeholders. This should be the first step in document generation."""
    return legacy_tools.get_template_placeholders(template_name)

@tool
def answer_legal_question_with_rag(question: str) -> str:
    """Use this tool to answer any legal question by searching through the knowledge base of legal documents."""
    return utils.answer_with_rag(question)

@tool
def fill_template_and_save_document(template_name: str, project_id: str, document_name: str, context: dict) -> str:
    """The final step. Fills and saves a .docx template with the provided information. Only use this after all information has been collected."""
    return legacy_tools.fill_template_and_save_document(template_name, document_name, context)

@tool
def list_projects() -> str:
    """Lists all available projects for the user."""
    return legacy_tools.list_projects()

# --- 3. Create the Manager Agent ---

agent_tools = [
    get_template_placeholders,
    answer_legal_question_with_rag,
    fill_template_and_save_document,
    list_projects,
]

llm = ChatOllama(model="llama3", temperature=0, base_url=os.getenv("LLM_URL"))

react_prompt = hub.pull("hwchase17/react-chat")

agent = create_react_agent(llm, agent_tools, react_prompt)
agent_executor = AgentExecutor(agent=agent, tools=agent_tools, verbose=True, handle_parsing_errors=True)

manager_system_prompt = """You are a helpful and expert legal assistant manager. Your goal is to assist the user in their tasks, primarily focusing on document generation.

**CRITICAL RULE: If a tool returns an authentication error, you MUST stop immediately and inform the user that there is a login or session problem. Do not try other tools.**

**Document Generation Workflow:**
1. When the user expresses intent to generate a document from a template, your first and only action should be to use the `get_template_placeholders` tool to understand the template's required fields.
2. After getting the list of fields, you MUST ask the user for the information for the FIRST field in the list.
3. Continue this process, asking for one piece of information at a time, until all fields are collected.
4. Once all information is gathered, ask for a final `document_name` and the `project_id`.
5. Finally, call `fill_template_and_save_document` with all the collected context to generate the document.

For any other request, like listing projects, use the appropriate tool.
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