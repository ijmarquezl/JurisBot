import os
import json
from typing import Annotated, List, TypedDict

from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, create_react_agent_executor

from app import tools as legacy_tools # Import old tools to be adapted

# --- 1. Define the State ---

class AgentState(TypedDict):
    messages: Annotated[list, lambda x, y: x + y]
    # This will hold the data for the document generation workflow
    # We can add more specific keys as needed, e.g., 'template_name', 'collected_data'
    workflow_data: dict

# --- 2. Define the Worker Tools ---

# We adapt the functions from the old tools.py into this new format.
# Note: The docstrings are crucial for the agent to understand the tool.

@tool
def get_template_placeholders(template_name: str) -> str:
    """Inspects a .docx template and returns a list of its placeholders. This should be the first step in document generation."""
    return legacy_tools.get_template_placeholders(template_name)

@tool
def answer_legal_question_with_rag(question: str) -> str:
    """Use this tool to answer any legal question by searching through the knowledge base of legal documents."""
    # This will be adapted from the old rag_agent.py. For now, it's a placeholder.
    print(f"---Invoking RAG with: {question}---")
    return "Placeholder RAG answer: According to Article 123, you have rights."

@tool
def fill_template_and_save_document(template_name: str, project_id: str, document_name: str, context: dict) -> str:
    """The final step. Fills and saves a .docx template with the provided information. Only use this after all information has been collected."""
    return legacy_tools.fill_template_and_save_document(template_name, project_id, document_name, context)

@tool
def list_projects() -> str:
    """Lists all available projects for the user."""
    return legacy_tools.list_projects()

# --- 3. Create the Manager Agent ---

manager_tools = [
    get_template_placeholders,
    answer_legal_question_with_rag,
    fill_template_and_save_document,
    list_projects,
]

# Set up the LLM using ChatOllama
llm = ChatOllama(model="llama3", temperature=0)

manager_system_prompt = """You are a master agent, a legal assistant manager. Your job is to orchestrate a team of specialized tools to fulfill the user's request.

You will manage the entire process, from understanding the request to delivering the final product.
When the user wants to generate a document, you must follow this plan:
1. First, use `get_template_placeholders` to understand the template.
2. Then, you must interview the user one by one for each placeholder.
3. If you need to find legal articles based on the facts, use the `answer_legal_question_with_rag` tool.
4. Once all information is gathered, you will ask for a final document name and project ID.
5. Finally, you will call `fill_template_and_save_document` to create the document.

For simple requests, like listing projects, you can call the appropriate tool directly.
If a tool call fails, analyze the error and decide on a new course of action.
"""

manager_agent = create_react_agent_executor(llm, manager_tools, messages_modifier=manager_system_prompt)

# --- 4. Define the Graph ---

# Create the tool node
tool_node = ToolNode(manager_tools)

# Define the router logic
def router(state: AgentState) -> str:
    """Routes the conversation to the correct node."""
    last_message = state["messages"][-1]
    # If the last message is a tool call, route to the tool node
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    # Otherwise, route back to the manager
    return "manager"

workflow = StateGraph(AgentState)

# Add the manager node
workflow.add_node("manager", manager_agent)
# Add the tool execution node
workflow.add_node("tools", tool_node)

# Set the entry point
workflow.set_entry_point("manager")

# Add the conditional edges from the manager
workflow.add_conditional_edges(
    "manager",
    router,
    # If the router returns "tools", go to the tool_node. Otherwise, end.
    # We will make this more complex later to allow for continuous conversation.
    {"tools": "tools", "__end__": END}
)

# Add an edge from the tool node back to the manager
workflow.add_edge("tools", "manager")

# Compile the graph
graph = workflow.compile()

print("Graph with router and tool node defined. Ready for integration.")
