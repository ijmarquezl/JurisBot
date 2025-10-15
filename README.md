# Jurisconsultor: Agente IA para Asesoría Legal

Jurisconsultor es un sistema de agentes inteligentes impulsado por IA diseñado para asistir a abogados y profesionales del derecho. Su objetivo es facilitar la consulta eficiente de documentos legales, la gestión de proyectos y la generación de documentos jurídicos complejos, con una arquitectura segura y escalable.

## Arquitectura (Multi-Tenant)

El proyecto utiliza una arquitectura de microservicios contenerizada con Docker, diseñada para un entorno multi-tenant que garantiza el aislamiento de datos entre diferentes compañías.

-   **`frontend`**: Servicio React que provee la interfaz de usuario. Es compartido por todos los tenants.
-   **`backend`**: API central en FastAPI. Contiene toda la lógica de negocio y orquesta a los agentes de IA. Es un servicio compartido y diseñado para ser escalable horizontalmente.
-   **`postgres-public`**: Base de datos PostgreSQL compartida que almacena vectores de documentos legales públicos para el sistema RAG.
-   **Bases de Datos por Tenant**: Cada compañía (tenant) tiene su propio conjunto de bases de datos para garantizar el aislamiento de datos privados:
    -   `postgres-private-<tenant>`: Almacena vectores de documentos privados.
    -   `mongodb-private-<tenant>`: Almacena datos de la aplicación como usuarios, proyectos y conversaciones.

## Flujo de Trabajo de Desarrollo (CI/CD Local)

Para simplificar el desarrollo, las pruebas y el despliegue en un entorno local, el proyecto incluye un script de automatización.

### Prerrequisitos

-   Docker y Docker Compose
-   Tener un archivo `.env` configurado en la raíz del proyecto (puedes basarte en `jurisconsultor/.env.example` y moverlo a la raíz).

### Despliegue Automatizado

Después de realizar cambios en el código (backend o frontend), simplemente ejecuta el siguiente comando desde la raíz del proyecto:

```bash
./deploy_test.sh
```

Este script se encargará de:
1.  Ejecutar las pruebas del backend (`pytest`).
2.  Verificar el estilo de código del frontend (`npm run lint`).
3.  Reconstruir las imágenes de Docker con los últimos cambios.
4.  Reiniciar todos los servicios en Docker Compose.

### Acceso a la Aplicación

Una vez que el script termine, la aplicación estará disponible en:

-   **Frontend:** `http://localhost:5173`
-   **Backend API:** `http://localhost:8000`

---
