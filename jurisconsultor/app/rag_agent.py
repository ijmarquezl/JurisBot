import os
from typing import Optional
from pymongo.database import Database # Keep for potential future use or if other parts depend on it
from langchain_core.messages import HumanMessage, AIMessage
from models import UserInDB # Assuming UserInDB is needed for context
from graph_agent import graph # Import the LangGraph graph

def run_agent(user_query: str, current_user: UserInDB, access_token: str) -> str:
    """
    Runs the LangGraph agent with the user's query and context.
    """
    if not current_user.company_id:
        return "Error: No se pudo determinar el ID de la compañía del usuario."

    # Configure the graph with the user's thread ID for state persistence
    config = {"configurable": {"thread_id": current_user.email}}
    
    # Prepare the initial state for the graph
    inputs = {
        "messages": [HumanMessage(content=user_query)],
        "access_token": access_token,
        "company_id": str(current_user.company_id)
    }
    
    final_answer_content = "Lo siento, no pude procesar tu solicitud."

    try:
        # Invoke the graph. The graph handles the entire conversation flow.
        # We use invoke here to get the final state after all steps are completed.
        final_state = graph.invoke(inputs, config=config)
        
        # Extract the last message from the manager node, which should be the final answer
        if final_state and final_state.get("messages"):
            last_message = final_state["messages"][-1]
            if isinstance(last_message, AIMessage):
                final_answer_content = last_message.content
            elif isinstance(last_message, HumanMessage): # In case the last message is from the user, which shouldn't happen in a final state
                final_answer_content = "El agente ha procesado tu solicitud, pero no ha generado una respuesta final."
            else:
                final_answer_content = str(last_message) # Fallback for other message types
        
    except Exception as e:
        print(f"An error occurred during agent invocation: {e}")
        final_answer_content = f"Lo siento, ocurrió un error inesperado al procesar tu solicitud: {e}"
        
    return final_answer_content
