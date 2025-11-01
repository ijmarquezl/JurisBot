# Jurisconsultor: Agente IA para Asesoría Legal

Jurisconsultor es un sistema de agentes inteligentes impulsado por IA diseñado para asistir a abogados y profesionales del derecho. Su objetivo es facilitar la consulta eficiente de documentos legales, la gestión de proyectos y la generación de documentos jurídicos complejos, con una arquitectura segura y escalable.

## Arquitectura (Multi-Tenant con Reverse Proxy)

El proyecto utiliza una arquitectura de microservicios contenerizada con Docker Compose, diseñada para un entorno multi-tenant que garantiza el aislamiento de datos entre diferentes compañías.

-   **`proxy` (Nginx)**: Nuevo servicio de reverse proxy. Es el único punto de entrada público a la aplicación (puerto 80). Enruta el tráfico al `frontend` o al `backend` internamente, proporcionando una capa de seguridad y abstracción.
-   **`frontend`**: Aplicación React que provee la interfaz de usuario. Es un servicio interno, accesible solo a través del `proxy`.
-   **`backend`**: API central en FastAPI. Contiene toda la lógica de negocio y orquesta a los agentes de IA. Es un servicio interno, accesible solo a través del `proxy`.
-   **`postgres_public`**: Base de datos PostgreSQL que almacena vectores de documentos legales públicos para el sistema RAG. Incluye la extensión `pgvector`.
-   **`mongodb_tenant_a`**: Base de datos MongoDB de ejemplo para el tenant 'A', que almacena usuarios, proyectos y conversaciones.
-   **`postgres_tenant_a`**: Base de datos PostgreSQL de ejemplo para el tenant 'A', que almacena vectores de documentos privados.
-   **Bases de Datos por Tenant (Dinámicas)**: El script `onboard_tenant.sh` permite crear dinámicamente nuevos servicios de bases de datos (PostgreSQL y MongoDB) para cada nueva compañía, asegurando el aislamiento de datos privados.

## Configuración de Entorno (`.env`)

El proyecto utiliza archivos `.env` para gestionar variables de entorno sensibles y configuraciones específicas de cada entorno.

-   **`.env` (raíz del proyecto)**: Contiene variables de entorno globales y credenciales para las bases de datos de ejemplo (`tenant_a`) y las que se generen dinámicamente. **No debe ser versionado.**
-   **`jurisconsultor/.env.example`**: Ejemplo de configuración para el backend.
-   **`jurisconsultor/frontend/.env`**: Contiene la URL del backend para el frontend. **No debe ser versionado.**
-   **`jurisconsultor/frontend/.env.example`**: Ejemplo de configuración para el frontend.

## Flujo de Trabajo y Despliegue

### Prerrequisitos

-   Docker y Docker Compose.
-   Asegúrate de que tu archivo `.env` en la raíz del proyecto esté configurado. Puedes copiar `jurisconsultor/.env.example` y adaptarlo.

### Gestión de Tenants y Primer Inicio

El script `onboard_tenant.sh` automatiza la creación de nuevos tenants (compañías), incluyendo sus bases de datos y un usuario administrador inicial.

**Para crear tu primera compañía y usuario administrador:**

```bash
./onboard_tenant.sh "Nombre de tu Empresa" admin@tuempresa.com TuContraseñaSegura
```
**Ejemplo:**
```bash
./onboard_tenant.sh "Mi Primera Empresa" admin@miempresa.com P@ssw0rdSegur@123
```

Este script realizará las siguientes acciones:
1.  Generará credenciales seguras para las bases de datos del nuevo tenant.
2.  Actualizará el archivo `.env` en la raíz del proyecto con estas nuevas credenciales.
3.  Añadirá las definiciones de los servicios de base de datos del nuevo tenant a `docker-compose.override.yml`.
4.  Levantará o reiniciará todos los servicios de Docker Compose, incluyendo las nuevas bases de datos.
5.  Creará el usuario administrador especificado en la base de datos del nuevo tenant.

### Reconstrucción y Reinicio General

Después de realizar cambios en el código (backend, frontend, proxy) o en la configuración de Docker Compose, ejecuta:

```bash
docker compose up -d --build
```
Esto reconstruirá las imágenes necesarias y reiniciará los servicios.

### Acceso a la Aplicación

Una vez que los servicios estén en funcionamiento, la aplicación será accesible a través del reverse proxy en el puerto 80. Si tu servidor tiene la IP `10.29.93.10`, la URL será:

**http://10.29.93.10**

Podrás iniciar sesión con las credenciales del usuario administrador que creaste con `onboard_tenant.sh`.

## Procesamiento de Documentos Públicos (RAG)

Para que el sistema RAG funcione con documentos públicos:

1.  **Coloca tus documentos PDF:** Copia todos los archivos PDF que deseas procesar en la carpeta **`jurisconsultor/documentos_legales`** en tu máquina host.
2.  **Ejecuta el script de migración de la base de datos:** Esto asegura que la tabla `documents` y `document_ownership` existan en PostgreSQL.
    ```bash
    docker exec jurisbot-backend-1 python db_migration.py public
    ```
3.  **Ejecuta el script de procesamiento:** Esto leerá los PDFs, generará embeddings y los almacenará en la base de datos.
    ```bash
    docker exec jurisbot-backend-1 python legal_scraper.py /docs public
    ```

---