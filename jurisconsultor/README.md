# Jurisconsultor: Agente IA para Asesoría Legal

Jurisconsultor es un agente inteligente impulsado por IA diseñado para asistir a abogados y profesionales del derecho en México. Su objetivo es facilitar la consulta eficiente de documentos legales, la gestión de proyectos y tareas, y la interacción con un asistente conversacional especializado.

## Características Principales (v0.0.3 - Pre-Alpha)

-   **Agente Conversacional (RAG):**
    -   Un agente de IA capaz de responder preguntas sobre legislación mexicana y documentos internos.
    -   Utiliza Retrieval-Augmented Generation (RAG) para proporcionar respuestas basadas en una base de conocimientos legal.
    -   Puede interactuar con la API para realizar acciones como crear proyectos o tareas.
-   **Dashboard de Usuario:**
    -   Interfaz centralizada para la gestión de proyectos, tareas y documentos.
    -   **Gestión de Proyectos:**
        -   Visualización de proyectos activos y archivados.
        -   Creación de nuevos proyectos.
        -   Borrado de proyectos (solo para líderes/administradores).
        -   Archivado y desarchivado de proyectos (solo para líderes/administradores).
    -   **Gestión de Tareas:**
        -   Visualización de tareas asociadas a un proyecto seleccionado.
        -   Creación de nuevas tareas.
        -   Actualización del estado de las tareas (Por Hacer, En Progreso, Hecho).
    -   **Gestión de Documentos:**
        -   Visualización de documentos legales públicos (leyes mexicanas).
        -   Visualización de documentos privados asociados a la compañía del usuario.
-   **Autenticación y Autorización:**
    -   Sistema de login para usuarios.
    -   Roles de usuario (administrador, líder de proyecto, miembro) con permisos diferenciados.
-   **API Backend Robusta:**
    -   Desarrollado con FastAPI, MongoDB (usuarios, proyectos, tareas) y PostgreSQL (documentos, embeddings).
    -   Manejo resiliente de inconsistencias de datos y validación estricta con Pydantic.
-   **Frontend Interactivo:**
    -   Desarrollado con React y Material-UI para una experiencia de usuario moderna.

## Arquitectura

-   **Backend:** Python (FastAPI)
-   **Bases de Datos:** MongoDB (NoSQL), PostgreSQL (Relacional con extensión `pgvector`)
-   **Frontend:** React (Vite, Material-UI)
-   **Modelos de Lenguaje:** Integración con LLMs para el agente conversacional.

## Configuración y Ejecución Local

### Prerrequisitos

-   Python 3.11+
-   Node.js (para el frontend)
-   MongoDB (servidor local o Docker)
-   PostgreSQL (servidor local o Docker)

### Pasos de Configuración

1.  **Clonar el Repositorio:**
    ```bash
    git clone [URL_DEL_REPOSITORIO]
    cd JurisBot
    ```

2.  **Configurar el Backend (Python):**
    a.  **Crear y Activar Entorno Virtual:**
        ```bash
        python -m venv .venv
        source .venv/bin/activate
        ```
    b.  **Instalar Dependencias:**
        ```bash
        pip install -r jurisconsultor/requirements.txt
        ```
    c.  **Configurar Variables de Entorno:**
        Crea un archivo `.env` en el directorio `jurisconsultor/` basado en `jurisconsultor/.env.example`. Asegúrate de configurar:
        -   `MONGO_URI`
        -   `PUBLIC_POSTGRES_URI` (para la base de datos pública)
        -   `PRIVATE_POSTGRES_URI` (para la base de datos privada)
        -   `LLM_URL` (URL de tu modelo de lenguaje local, ej. `http://localhost:11434`)
        -   `EMBEDDING_MODEL_NAME`
        -   `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`

    d.  **Ejecutar Migraciones de Base de Datos:**
        *   Para la base de datos **pública**:
            ```bash
            python jurisconsultor/db_migration.py public
            ```
        *   Para la base de datos **privada**:
            ```bash
            python jurisconsultor/db_migration.py private
            ```

    e.  **Procesar Documentos (Scraper):**
        Carga tus documentos legales en la base de datos. Asegúrate de tener tus archivos PDF en una carpeta (ej. `jurisconsultor/documentos_legales/`).
        *   **Para documentos públicos:**
            ```bash
            python jurisconsultor/app/legal_scraper.py jurisconsultor/documentos_legales/publicos public
            ```
        *   **Para documentos privados** (reemplaza `<tu_company_id>` con el ID de tu compañía):
            ```bash
            python jurisconsultor/app/legal_scraper.py jurisconsultor/documentos_legales/privados private --company-id <tu_company_id>
            ```

3.  **Configurar el Frontend (React):**
    a.  **Navegar al Directorio:**
        ```bash
        cd jurisconsultor/frontend
        ```
    b.  **Instalar Dependencias:**
        ```bash
        npm install
        ```
    c.  **Volver al Directorio Raíz del Backend:**
        ```bash
        cd ../..
        ```

4.  **Ejecutar la Aplicación:**
    Abre dos terminales separadas:
    a.  **Terminal 1 (Backend):**
        ```bash
        source .venv/bin/activate # Si no está activado
        uvicorn jurisconsultor/app/main:app --reload
        ```
    b.  **Terminal 2 (Frontend):
        ```bash
        cd jurisconsultor/frontend
        npm run dev
        ```

5.  **Acceder a la Aplicación:**
    Abre tu navegador y ve a `http://localhost:5173`.

## Próximos Pasos (Roadmap v0.0.4+)

-   **Contenerización:** Preparación para despliegues en Docker y entornos de producción.
-   **Orquestación:** Gestión de múltiples bases de datos privadas por compañía.
-   **Despliegue Remoto:** Publicación en servidores para pruebas de especialistas.

---