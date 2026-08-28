
import json
import logging
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from infrastructure.ai.tools.drafter_tools import search_legal_examples, read_legal_example
from infrastructure.utils.utils import answer_with_rag
import os

logger = logging.getLogger(__name__)

# Prompts
ANALYZER_PROMPT = """Eres un experto analista legal. Tu tarea es analizar el "Ejemplo de Documento" proporcionado y la "Solicitud del Usuario".
1. Identifica qué TIPO de documento es.
2. Identifica las VARIABLES CRÍTICAS que faltan en la solicitud del usuario para poder redactar un documento similar al ejemplo (ej. Nombres, Fechas, Ubicaciones, Montos).
3. Si faltan variables críticas, genera una lista de preguntas para hacérselas al usuario.
4. Si tienes todo lo necesario, indica que estás listo para redactar.

Responde ÚNICAMENTE en formato JSON:
{
  "document_type": "...",
  "missing_info": ["variable1", "variable2"],
  "questions_for_user": ["Pregunta 1", "Pregunta 2"],
  "ready_to_draft": boolean,
  "drafting_instructions": "Instrucciones especiales para el redactor..."
}
"""

DRAFTER_PROMPT = """Eres un Redactor Legal Experto (Legal Drafter). 
Tu objetivo es redactar un documento formal basándote ESTRICTAMENTE en la ESTRUCTURA del ejemplo proporcionado, pero rellenándolo con los HECHOS del usuario y los FUNDAMENTOS JURÍDICOS obtenidos del RAG.

FUENTES:
1. ESTRUCTURA: Usa el 'Ejemplo Seleccionado'. Respeta sus encabezados y estilo.
2. HECHOS: Usa la información provista por el usuario.
3. LEY: Usa los 'Fundamentos Legales' (RAG) para rellenar las secciones de derecho (Procedencia, Conceptos de Violación). NO INVENTES LEYES.

INSTRUCCIONES:
- Genera el documento completo en formato Markdown bien estructurado.
- Donde falten datos menores, usa placeholders como [DATOS].
- Tu respuesta debe ser SOLO el documento redactado.
"""

llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_NAME"),
    temperature=0,
    openai_api_key=os.getenv("GROQ_API_KEY"),
    openai_api_base=os.getenv("LLM_URL")
)

def retrieve_example_node(state):
    """
    Searches for a legal example matching the user's last message.
    """
    # Find the last HumanMessage
    last_msg = ""
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            last_msg = m.content
            break
            
    if not last_msg:
        logger.warning("Drafter: No HumanMessage found in state.")
        return {"messages": [AIMessage(content="No encontré instrucción del usuario.")]}

    logger.info(f"Drafter: Searching examples for '{last_msg[:50]}...'")
    
    # 1. Search
    search_res = search_legal_examples(last_msg)
    options = json.loads(search_res)
    
    if not options or "error" in options:
        # Return specific status so router can handle it or analyzer can see it
        return {
            "messages": [AIMessage(content="No encontré ejemplos adecuados para redactar este documento. ¿Podrías ser más específico o subir un ejemplo?")],
            "drafting_data": {"status": "error", "error": "no_examples_found"}
        }
    
    # 2. Select Best
    best_match = options[0] # Default
    
    if len(options) > 1:
        try:
            # Smart Selection with LLM
            options_text = "\n".join([f"- {opt['filename']} (Category: {opt['category']})" for opt in options])
            selection_prompt = f"""
            El usuario solicitó: "{last_msg}"
            
            He encontrado los siguientes documentos similares:
            {options_text}
            
            Tu tarea es seleccionar el MEJOR documento para servir de ejemplo base.
            Si el usuario pide algo genérico (ej. "demanda de amparo"), prefiere el documento más general (ej. "Demanda de Amparo Muestra.docx").
            Si pide algo específico, busca el más afin.
            
            Responde ÚNICAMENTE un objeto JSON:
            {{ "selected_filename": "Nombre del archivo exacto seleccionado" }}
            """
            
            messages = [
                SystemMessage(content="Eres un asistente experto en selección de documentos legales."),
                HumanMessage(content=selection_prompt)
            ]
            
            response = llm.invoke(messages)
            content = response.content.strip()
            
            # Simple cleanup for JSON
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            elif content.startswith("```"):
                content = content.replace("```", "")
                
            selection_data = json.loads(content)
            selected_name = selection_data.get("selected_filename")
            
            # Find the match object
            for opt in options:
                if opt['filename'] == selected_name:
                    best_match = opt
                    logger.info(f"Drafter: LLM selected '{selected_name}'")
                    break
                    
        except Exception as e:
            logger.error(f"Drafter: Selection LLM failed ({e}), falling back to first option.")
    
    logger.info(f"Drafter: Final Selected Example '{best_match['filename']}'")
    
    # 3. Read Content
    content_res = read_legal_example(best_match['category'], best_match['filename'])
    content_json = json.loads(content_res)
    
    if "error" in content_json:
        return {"messages": [AIMessage(content=f"Error leyendo el ejemplo: {content_json['error']}")]}
        
    example_text = content_json["content"]
    
    # Store in state (We need to update state definition in main graph to hold 'drafting_data')
    return {
        "drafting_data": {
            "example_content": example_text,
            "example_name": best_match['filename'],
            "status": "analyzing"
        }
    }

def analyzer_node(state):
    """
    Analyzes facts vs example requirements.
    """
    drafting_data = state.get("drafting_data", {})
    if not drafting_data or drafting_data.get("status") == "error":
        # Friendly message instead of leaking the raw error code
        # ("no_examples_found") to the end user.
        return {"messages": [AIMessage(content="No encontré ejemplos adecuados para redactar este documento. ¿Podrías ser más específico o subir un ejemplo?")]}

    example_content = drafting_data.get("example_content")
    
    if not example_content:
        # State corrupted/lost. Reset to allow restart.
        return {
            "messages": [AIMessage(content="Lo siento, he perdido el contexto del documento (contenido de ejemplo) debido a un error previo. Por favor, comienza de nuevo diciéndome qué documento quieres redactar.")],
            "drafting_data": {} # Reset state
        }
    # User Request Context (Everything up to now)
    # Collect ALL HumanMessages to ensure we don't forget previous facts (Fixes looping bug)
    user_request = ""
    for m in state["messages"]:
        if isinstance(m, HumanMessage):
             user_request += f"User: {m.content}\n"
            
    prompt = f"""
    EJEMPLO DE DOCUMENTO:
    {example_content[:4000]} ... (truncado)
    
    SOLICITUD DEL USUARIO:
    {user_request}
    """
    
    messages = [
        SystemMessage(content=ANALYZER_PROMPT),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    logger.info(f"Drafter: Analyzer Raw Response: {response.content}")
    
    try:
        content = response.content.strip()
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "")
        elif content.startswith("```"):
             content = content.replace("```", "")
             
        analysis = json.loads(content)
        
        # Determine next step
        if analysis.get("ready_to_draft"):
            # Preserve existing data
            updated_drafting_data = drafting_data.copy()
            updated_drafting_data.update({
                 "status": "ready",
                 "analysis": analysis
            })
            return {
                "drafting_data": updated_drafting_data
            }
        else:
            # Ask questions
            questions = "\n".join([f"- {q}" for q in analysis["questions_for_user"]])
            
            # Preserve existing data
            updated_drafting_data = drafting_data.copy()
            updated_drafting_data.update({
                 "status": "interviewing",
                 "analysis": analysis
            })
            
            return {
                "messages": [AIMessage(content=f"Para redactar el documento '{analysis['document_type']}' basándome en el ejemplo, necesito la siguiente información:\n{questions}")],
                "drafting_data": updated_drafting_data
            }
    except Exception as e:
        logger.error(f"Analysis Error: {e}")
        return {"messages": [AIMessage(content="Tuve problemas analizando los requisitos del documento.")]}

def drafting_node(state):
    """
    Generates the final draft using RAG + Structure.
    """
    drafting_data = state.get("drafting_data")
    example_content = drafting_data.get("example_content")
    analysis = drafting_data.get("analysis")
    
    # 1. RAG Research for Legal Backing
    # We synthesize a query based on the document type
    rag_query = f"Fundamentos legales y jurisprudencia para redacción de {analysis.get('document_type', 'documento legal')} en México"
    logger.info(f"Drafter: Researching '{rag_query}'")
    
    # We use the existing 'utils.answer_with_rag' function directly
    # Ideally we'd call the tool but we are inside a node.
    rag_context = answer_with_rag(rag_query, user_context={"tenant_id": state.get("company_id")})
    
    # 2. Generate Draft
    facts = ""
    for m in state["messages"]:
        if isinstance(m, HumanMessage):
            facts += f"User: {m.content}\n"
            
    prompt = f"""
    ESTRUCTURA (EJEMPLO):
    {example_content[:6000]}
    
    FUNDAMENTOS LEGALES (RAG):
    {rag_context}
    
    HECHOS DEL USUARIO:
    {facts}
    """
    
    messages = [
        SystemMessage(content=DRAFTER_PROMPT),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    
    return {
        "messages": [AIMessage(content=f"Aquí tienes el borrador:\n\n{response.content}")]
    }

