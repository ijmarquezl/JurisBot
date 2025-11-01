import os
import re
import json
import inspect
from typing import Optional, List
from pymongo.database import Database
from datetime import datetime

from utils import get_public_db_conn, generate_embedding
from models import ConversationState, UserInDB
from app import tools

LLM_URL = os.getenv("LLM_URL")

# --- RAG-related functions (existing logic) ---
def find_relevant_documents(query_embedding, top_k=3):
    """Finds the most relevant document chunks from the database."""
    try:
        conn = get_public_db_conn()
        cur = conn.cursor()
        embedding_str = str(query_embedding.tolist())
        cur.execute(
            "SELECT content, source FROM documents ORDER BY embedding <-> %s LIMIT %s;",
            (embedding_str, top_k)
        )
        results = cur.fetchall()
        cur.close()
        conn.close()
        return results
    except Exception as e:
        print(f"An error occurred during document retrieval: {e}")
        return []

def answer_with_rag(question: str) -> str:
    """Answers a question using the RAG pipeline."""
    question_embedding = generate_embedding(question)
    relevant_docs = find_relevant_documents(question_embedding)
    if not relevant_docs:
        return "No se encontraron documentos relevantes para responder a su pregunta."
    
    context = "\n".join([f"Fuente: {source}\nContenido: {content}" for content, source in relevant_docs])
    prompt = f"Contexto: {context}\n\nPregunta: {question}\n\nRespuesta:"
    
    return call_llm(prompt)

# --- Generic LLM Call ---
def call_llm(prompt: str, json_format: bool = False) -> str:
    """Generic function to call the LLM."""
    if not LLM_URL:
        raise ValueError("LLM_URL environment variable not set.")
    try:
        payload = {"model": "llama3", "prompt": prompt, "stream": False}
        if json_format:
            payload["format"] = "json"
            
        response = requests.post(f"{LLM_URL}/api/generate", json=payload)
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while querying the LLM: {e}")
        return f"Error: No se pudo obtener una respuesta del modelo de lenguaje. {e}"

# --- Stateful Agent Logic ---

def get_tools_prompt():
    """Generates the tools prompt for the router agent."""
    tools_description = ""
    for name, func in inspect.getmembers(tools, inspect.isfunction):
        if name.startswith('_') or name == 'set_auth_token':
            continue
        tools_description += f"- Tool: {name}\n  Description: {inspect.getdoc(func)}\n"

    prompt_template = """Your job is to act as a router. Based on the user's query, you must decide which tool to use. You must respond with a JSON object indicating the tool and its arguments.\n\nAvailable tools:\n{tools_placeholder}\n- Tool: answer_with_rag\n  Description: **This is the default tool.** Use it for any legal questions, requests for information, or any general question that doesn't match another tool.\n  Args:\n      question (str): The user's original question.\n---\nIf you decide to use a tool, respond with a JSON object like this: {{\"tool\": \"tool_name\", \"args\": {{\"arg1\": \"value1\"}}}}\n"""
    return prompt_template.format(tools_placeholder=tools_description)

def _clear_state(db: Database, user_email: str):
    """Clears the conversation state for a user."""
    db.conversation_states.update_one(
        {"user_email": user_email},
        {"$set": {"workflow": None, "workflow_data": {}, "last_updated": datetime.utcnow()}},
        upsert=True
    )

def _handle_document_generation(state: ConversationState, user_query: str, db: Database) -> str:
    """Handles the logic for the document generation workflow."""
    workflow_data = state.workflow_data
    placeholders = workflow_data.get("placeholders_to_fill", [])
    collected_data = workflow_data.get("collected_data", {})

    # If this is not the first step, collect the user's answer from the previous turn
    if workflow_data.get("last_question"):
        last_question_key = workflow_data["last_question"]
        collected_data[last_question_key] = user_query
        if last_question_key in placeholders:
            placeholders.remove(last_question_key)
    
    # Persist the collected data immediately
    workflow_data["collected_data"] = collected_data
    workflow_data["placeholders_to_fill"] = placeholders

    # Check for special rule: RAG for legal articles
    if any(p in collected_data for p in ['hechos', 'declaracion']) and any(p in placeholders for p in ['articulos_aplicables', 'articulos_normativos']):
        legal_placeholders = [p for p in placeholders if p in ['articulos_aplicables', 'articulos_normativos']]
        if legal_placeholders:
            facts = collected_data.get('hechos', '')
            rag_query = f"Based on the following facts: {facts}, what legal articles and laws are applicable?"
            rag_result = answer_with_rag(rag_query)
            for placeholder in legal_placeholders:
                collected_data[placeholder] = rag_result
                placeholders.remove(placeholder)
            workflow_data["collected_data"] = collected_data
            workflow_data["placeholders_to_fill"] = placeholders

    # If all data is collected, ask for final details
    if not placeholders:
        if "document_name" not in collected_data:
            workflow_data["last_question"] = "document_name"
            db.conversation_states.update_one({"_id": state.id}, {"$set": {"workflow_data": workflow_data, "last_updated": datetime.utcnow()}})
            return "Tengo toda la información para la plantilla. ¿Qué nombre le damos al nuevo documento?"
        
        if "project_id" not in collected_data:
            workflow_data["last_question"] = "project_id"
            db.conversation_states.update_one({"_id": state.id}, {"$set": {"workflow_data": workflow_data, "last_updated": datetime.utcnow()}})
            return f'Excelente. El documento se llamará "{collected_data["document_name"]}". Ahora, por favor, proporciona el ID del proyecto al que pertenecerá. Puedes usar la herramienta `list_projects` si no lo conoces.'

        # All data collected, execute final tool
        try:
            result = tools.fill_template_and_save_document(
                template_name=workflow_data["template_name"],
                project_id=collected_data["project_id"],
                document_name=collected_data["document_name"],
                context=collected_data
            )
            _clear_state(db, state.user_email)
            return f'¡Documento generado con éxito! Puedes encontrarlo en: {json.loads(result).get("file_path", "")}'
        except Exception as e:
            _clear_state(db, state.user_email)
            return f"Ocurrió un error al generar el documento: {e}"

    # Ask for the next piece of information
    next_placeholder = placeholders[0]
    workflow_data["last_question"] = next_placeholder
    db.conversation_states.update_one({"_id": state.id}, {"$set": {"workflow_data": workflow_data, "last_updated": datetime.utcnow()}})
    return f'Entendido. Ahora, por favor, proporciona la información para: **{next_placeholder}**'

def run_agent(user_query: str, db: Database, current_user: UserInDB) -> str:
    """The main, stateful function to run the conversational agent."""
    tools.set_auth_token("dummy_token_for_now") # Auth token needs to be handled properly

    # 1. Get user's conversation state
    state_data = db.conversation_states.find_one({"user_email": current_user.email})
    if not state_data:
        state_data = {"user_email": current_user.email}
        db.conversation_states.insert_one(state_data)
    state = ConversationState(**state_data)

    # 2. Check for hard-coded triggers to start a workflow
    if not state.workflow:
        if "generar documento" in user_query.lower() and "plantilla" in user_query.lower():
            # Extract template name from query
            match = re.search(r'['"“](.*?.docx)['"”]', user_query)
            if not match:
                return "Por favor, especifica el nombre de la plantilla entre comillas para que pueda encontrarla. Ejemplo: ...usando la plantilla \"MI_PLANTILLA.docx\""
            template_name = match.group(1)
            
            # Call the initial tool directly
            placeholders_str = tools.get_template_placeholders(template_name)
            placeholders = json.loads(placeholders_str)

            if "error" in placeholders:
                return f"No pude iniciar el proceso de generación. La herramienta devolvió un error: {placeholders['error']}"

            # Initialize the state machine
            state.workflow = "document_generation"
            state.workflow_data = {
                "template_name": template_name,
                "placeholders_to_fill": placeholders,
                "collected_data": {},
                "last_question": None
            }
            db.conversation_states.update_one({"_id": state.id}, {"$set": state.dict(by_alias=True)})
            # Fall through to the handler to ask the first question
        
    # 3. If a workflow is active, handle it
    if state.workflow == "document_generation":
        return _handle_document_generation(state, user_query, db)

    # 4. If no workflow, act as a router for simple, one-shot tools
    tools_prompt = get_tools_prompt()
    decision_prompt = f"{tools_prompt}\n\nUser Query: \"{user_query}\"\n\nJSON response:"
    llm_decision_str = call_llm(decision_prompt, json_format=True)
    print(f"LLM Decision: {llm_decision_str}")

    try:
        decision = json.loads(llm_decision_str.strip())
        tool_name = decision.get("tool")
        args = decision.get("args", {})

        if tool_name == "answer_with_rag":
            return answer_with_rag(**args)
        
        elif hasattr(tools, tool_name):
            tool_function = getattr(tools, tool_name)
            tool_result_str = tool_function(**args)
            
            # Formulate a natural language response based on the tool's result
            response_formulation_prompt = f"The user asked: \"{user_query}\". The result from the tool \"{tool_name}\" is: {tool_result_str}. Based on this, formulate a friendly and clear response in Spanish."
            return call_llm(response_formulation_prompt)

        else:
            return answer_with_rag(user_query) # Default to RAG if tool is invalid

    except (json.JSONDecodeError, Exception) as e:
        print(f"Error parsing LLM decision or calling tool: {e}")
        return answer_with_rag(user_query) # Default to RAG on error