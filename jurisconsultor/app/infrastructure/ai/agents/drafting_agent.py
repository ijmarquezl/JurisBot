from infrastructure.utils.utils import call_llm

def draft_legal_document(topic: str, context: str, document_type: str = "Escrito Legal") -> str:
    """
    Uses the LLM to draft a structured legal document in Markdown format.
    
    Args:
        topic (str): The main facts, claims or topic of the document.
        context (str): The legal basis and retrieved context about the laws/jurisprudence.
        document_type (str): The kind of document to draft (e.g. Amparo, Contrato, Demanda).
        
    Returns:
        str: The drafted document in pure Markdown.
    """
    
    llm = get_llm()
    
    system_prompt = f"""Estarás actuando como un abogado litigante experto redactando un {document_type} altamente profesional y bien fundamentado.
    
REGLAS IMPORTANTES:
1. No uses ningún preámbulo ni despedida. Escribe DIRECTAMENTE el contenido del documento legal.
2. Utiliza estrictamente formato Markdown (títulos con #, subtítulos con ##, listas con -, negritas con **).
3. Fundamenta tu redacción en los preceptos legales proporcionados en el Contexto Jurídico.
4. Escribe con un tono formal, claro y conciso, estructurando el documento con apartados estándar como: Proemio, Hechos, Derecho/Fundamentos, y Puntos Petitorios (o cláusulas si es un contrato).
5. Cuida la gramática y ortografía en todo momento.

CONTEXTO JURÍDICO APLICABLE:
{context}
    """
    
    human_prompt = f"""
Por favor redacta el {document_type} basándote en los siguientes hechos/pretensiones:

{topic}
    """
    
    combined_prompt = system_prompt + "\n\n" + human_prompt
    
    response_content = call_llm(combined_prompt)
    return response_content
