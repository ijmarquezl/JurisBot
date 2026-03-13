# Legal Drafter Agent Implementation Plan

## Goal
Dotar al sistema JurisBot de una capacidad de "Pensamiento Estructural" para redactar documentos legales profundos, basándose en ejemplos ("Few-Shot") proporcionados por el usuario.

**Diferenciación de Fuentes:**
*   **Usuario:** Provee los hechos del caso, nombres, fechas, montos (Datos fácticos).
*   **RAG (Base de Conocimiento):** Provee fundamentos legales, tesis, jurisprudencia y artículos aplicables (Datos jurídicos).
*   **Ejemplos (Templates):** Proveen la estructura, formato y estilo de redacción.

## Core Component: `DrafterAgent` (Sub-Graph)

### Workflow
1.  **Router Detection:** If user intent == "DRAFT" (Redactar, Crear documento), route to `DrafterNode`.
2.  **Example Retrieval (`TemplateRetriever`):**
    *   Input: User Request (e.g., "Demanda de Amparo").
    *   Action: Search `jurisconsultor/ejemplos_legales` for the matching category/file.
    *   Output: Content of the best matching example.
3.  **Skeleton & Variable Analysis:**
    *   Input: Example Content + User Request.
    *   Action: Analyze the example to identify the structure AND the necessary variables (e.g., `[NOMBRE_QUEJOSO]`, `[ACTO_RECLAMADO]`).
4.  **Interactive Interview (New Step):**
    *   Action: Compare required variables with current conversation context.
    *   **Decision:** If critical facts are missing, **ASK THE USER**.
    *   Loop: Continue conversation until sufficient facts are gathered.
5.  **Legal Research (RAG):**
    *   Action: Once facts are clear, perform RAG queries to find the *legal backing* (e.g., "Fundamentos ley amparo silencio administrativo").
6.  **Draft Generation:**
    *   Input: `Structure` + `User_Facts` + `RAG_Law`.
    *   Prompt: "Draft the document using the Example's structure. Fill variables with User Facts. Build legal arguments ('Procedencia', 'Conceptos de Violación') using RAG data."

## Technical Changes

### 1. New Tools
*   `search_legal_examples(query: str)`: Searches `ejemplos_legales`.
*   `read_legal_example(filepath: str)`: Reads `.docx` content.

### 2. Graph Update (`graph_agent.py`)
*   **New Node:** `drafter_node` (Manages the drafting logic).
*   **State Update:** Add `drafting_context` to `AgentState` to track variables gathered so far.

### 3. Prompt Engineering
*   **Skeleton Analyzer:** "Identify variables in this text that need user input."
*   **Interviewer:** "Ask the user for missing variables X, Y, Z naturally."
*   **Final Drafter:** "Combine Structure, Facts, and Law."

## Verification
*   Test: Ask for a document with missing info. Verify Agent asks for it.
*   Test: Provide limits/dates. Verify Agent incorporates them.
*   Test: Verify Legal Arguments come from RAG.
