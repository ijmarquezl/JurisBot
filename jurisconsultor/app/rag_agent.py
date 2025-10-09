import os
import requests
import json
import inspect
from typing import Optional, List
from app.utils import get_public_db_conn, generate_embedding
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
            
        response = requests.post(
            f"{LLM_URL}/api/generate",
            json=payload
        )
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while querying the LLM: {e}")
        return f"Error: No se pudo obtener una respuesta del modelo de lenguaje. {e}"

# --- New Agent Logic ---

def get_tools_prompt():
    """Generates the tools prompt from the functions in the tools module."""
    
    tools_description = ""
    for name, func in inspect.getmembers(tools, inspect.isfunction):
        if name.startswith('_') or name == 'set_auth_token':
            continue
        tools_description += f"- Tool: {name}\n  Description: {inspect.getdoc(func)}\n"

    prompt_template = """You have access to the following tools. You must respond with a JSON object indicating which tool to use.
The JSON object must have a "tool" key and an "args" key.

Important: When using a tool that requires an ID (like 'project_id'), you must use the exact ID as it appears in the conversation history or a previous tool's output. Do not use the name of the object.

---
Available tools:
{tools_placeholder}
- Tool: continue_conversation
  Description: Use this tool ONLY when you are in the middle of a multi-step process (like Document Generation) and you need to ask the user for more information or confirm what you have collected so far. DO NOT use this for general conversation.
  Args:
      question_to_user (str): The specific question you want to ask the user.

- Tool: answer_with_rag
  Description: **This is the primary and most important tool.** Use it for any legal questions, requests for information about laws, articles, or legal concepts, or any general question. Only use other tools if the user explicitly asks to perform an action like "create a project" or "list tasks".
  Args:
      question (str): The user's original question.
---

**Document Generation Workflow:**
This is a special multi-step process. Follow these steps exactly.
1. The user asks to generate a document from a template.
2. Use `get_template_placeholders` to find the needed fields.
3. The tool returns a list of fields. Your first response to the user should be to start the process, asking for the very first placeholder in the list. Use the `continue_conversation` tool for this. For example: "Claro, empecemos a llenar la plantilla. Primero, ¿cuál es el nombre completo del demandante?"
4. The user will provide an answer. Confirm you received it and then ask for the NEXT placeholder in the list. Continue this one-by-one question and answer process using `continue_conversation` until most placeholders are filled.
5. **SPECIAL RULE for legal articles:** If you encounter placeholders like `articulos_aplicables`, `articulos_normativos`, or `jurisprudencia_aplicable`, DO NOT ask the user for this. Instead, once you have collected the `hechos` (facts) of the case, use the `answer_with_rag` tool. The question for the RAG tool should be: "Based on the following facts: [insert the collected facts here], what legal articles and laws are applicable?". Use the output of the RAG tool to fill these placeholders internally.
6. Once all placeholders are filled (including the ones you filled yourself using the RAG tool), use `continue_conversation` one last time to ask the user for the desired `document_name` for the new file and which `project_id` it belongs to.
7. Finally, with all information gathered, call `fill_template_and_save_document` to create the document.

Here are examples of multi-step thought processes:

**Example 1: The user wants to perform an action.**
User Query: "Add a task to the 'Dog Bite Case' project to 'Call the witness'."

1.  First, I need to find the ID for the project named 'Dog Bite Case'. I will use the `list_projects` tool.
    JSON response: {{"tool": "list_projects", "args": {{}}}}

2.  The tool will return a result like this: `[...{{"id": "68b444f3...", "name": "Dog Bite Case", ...}}]`. Now I have the project_id.

3.  Now I can call the `create_task` tool with the correct `project_id`.
    JSON response: {{"tool": "create_task", "args": {{"project_id": "68b444f3...", "title": "Call the witness"}}}}

**Example 2: The user asks a legal question.**
User Query: "What does article 15 of the federal labor law say?"

1.  This is a legal question, so I must use the `answer_with_rag` tool.
    JSON response: {{"tool": "answer_with_rag", "args": {{"question": "What does article 15 of the federal labor law say?"}}}}
---

If you decide to use a tool, respond with a JSON object like this:
{{"tool": "tool_name", "args": {{"arg1": "value1", "arg2": "value2"}}}}

If the user's query is a legal or general question, use the RAG tool like this:
{{"tool": "answer_with_rag", "args": {{"question": "the user question"}}}}
"""
    return prompt_template.format(tools_placeholder=tools_description)

def run_agent(user_query: str, auth_token: str, history: Optional[List[str]] = None) -> str:
    """The main function to run the conversational agent."""
    tools.set_auth_token(auth_token)

    # 1. Construct the prompt for the LLM to choose a tool
    tools_prompt = get_tools_prompt()
    history_str = ""
    if history:
        history_str = "\n".join(history) + "\n"
    decision_prompt = f"{tools_prompt}\n\nConversation History:\n{history_str}User Query: \"{user_query}\"\n\nJSON response:"

    # 2. Call the LLM to get its decision
    llm_decision_str = call_llm(decision_prompt, json_format=True)
    print(f"LLM Decision: {llm_decision_str}")

    # 3. Parse the decision and select the tool
    try:
        start_index = llm_decision_str.find('{')
        end_index = llm_decision_str.rfind('}')
        if start_index != -1 and end_index != -1:
            json_str = llm_decision_str[start_index:end_index+1]
            decision = json.loads(json_str)
        else:
            return answer_with_rag(user_query)

        tool_name = decision.get("tool")
        args = decision.get("args", {})

        # 4. Execute the selected tool
        if tool_name == "answer_with_rag":
            return answer_with_rag(**args)
        
        elif tool_name == "continue_conversation":
            # This is a pseudo-tool. Just return the question to the user.
            return args.get("question_to_user", "I'm not sure what to ask next. Can you please clarify?")

        elif hasattr(tools, tool_name):
            tool_function = getattr(tools, tool_name)
            tool_result = tool_function(**args)
        else:
            tool_result = "Error: The model chose a tool that does not exist."

        # 5. Formulate a natural language response based on the tool's result
        response_formulation_prompt = f"""
        The user asked: \"{user_query}\"
        You decided to use the tool: \"{tool_name}\"
        The result from the tool is:
        ---
        {tool_result}
        ---
        Based on this result, please formulate a friendly and clear response to the user in Spanish.
        If the result is an error, inform the user about the error in a helpful way.
        If the result is a list of items, format them nicely for the user.
        """
        
        final_response = call_llm(response_formulation_prompt)
        return final_response

    except (json.JSONDecodeError, AttributeError, TypeError) as e:
        print(f"Error parsing LLM decision or calling tool: {e}")
        return answer_with_rag(user_query)