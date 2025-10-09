# Jurisconsultor: Agente IA para Asesoría Legal

Jurisconsultor es un sistema de agentes inteligentes impulsado por IA diseñado para asistir a abogados y profesionales del derecho en México. Su objetivo es facilitar la consulta eficiente de documentos legales, la gestión de proyectos y la generación de documentos jurídicos complejos.

## Características Principales (v0.1.0 - Alpha)

-   **Equipo de Agentes Jerárquico (LangGraph):**
    -   El núcleo del sistema es un equipo de agentes de IA orquestado por LangGraph, basado en un patrón de "Manager/Workers".
    -   Un **Agente Gerente** planifica y descompone tareas complejas, delegando trabajo a agentes especializados.
    -   **Agente RAG:** Un especialista que responde preguntas sobre legislación buscando en una base de conocimientos vectorizada.
    -   **Agente de Documentos:** Un especialista que gestiona la creación de documentos a partir de plantillas.

-   **Generación de Documentos Asistida por IA:**
    -   Un flujo de conversación multi-paso para la creación de documentos (ej. demandas) a partir de plantillas `.docx`.
    -   El agente entrevista al usuario campo por campo para recopilar la información necesaria.
    -   **Asistencia Proactiva:** El agente utiliza el sistema RAG para sugerir automáticamente artículos y leyes aplicables basándose en los hechos del caso descritos por el usuario.
    -   El sistema genera un nuevo archivo `.docx` con la información recopilada.

-   **Dashboard de Usuario:**
    -   Interfaz centralizada para la gestión de proyectos, tareas y los nuevos documentos generados.
    -   Visualización de documentos con su nombre, propietario y proyecto asociado.

-   **Autenticación y Autorización:**
    -   Sistema de login y roles de usuario (administrador, líder, miembro) con permisos diferenciados.

## Arquitectura

-   **Backend:** Python (FastAPI)
-   **Orquestación de Agentes:** LangGraph
-   **Bases de Datos:** MongoDB (datos de la aplicación y estado de conversaciones), PostgreSQL (documentos para RAG)
-   **Frontend:** React (Vite, Material-UI)
-   **Modelos de Lenguaje:** Integración con LLMs locales a través de Ollama (`langchain-ollama`).

## Configuración y Ejecución Local

### Prerrequisitos

-   Python 3.11+
-   Node.js
-   MongoDB
-   PostgreSQL

### Pasos de Configuración

1.  **Clonar el Repositorio.**

2.  **Configurar el Backend (Python):**
    a.  Crear y activar un entorno virtual.
    b.  Instalar dependencias. El archivo `requirements.txt` ahora incluye `langgraph`, `langchain`, `langchain-ollama` y `python-docx`.
        ```bash
        pip install -r jurisconsultor/requirements.txt
        ```
    c.  Configurar el archivo `.env` en `jurisconsultor/` (basado en `.env.example`).
    d.  **Crear Carpeta de Plantillas:** En la raíz del proyecto (`JurisBot/`), crea una carpeta llamada `formatos/` y coloca tus plantillas `.docx` dentro.

3.  **Configurar el Frontend (React):**
    a.  Navegar a `jurisconsultor/frontend` e instalar dependencias con `npm install`.

4.  **Ejecutar la Aplicación:**
    a.  **Backend:** `uvicorn jurisconsultor.app.main:app --reload`
    b.  **Frontend:** `npm run dev` (desde `jurisconsultor/frontend`)

5.  **Acceder a la Aplicación:**
    Abre tu navegador y ve a `http://localhost:5173`.

---
