** V 0.0.1 **
- Integrar un chatbot que pueda responder preguntas sobre los proyectos y tareas.
- Agregar información específica de leyes públicas mexicanas y que pueda responder preguntas sobre ellas.
- Separar en un backend y un frontend, utilizando vite para el frontend y fastapi para el backend.
- Utilizar MongoDB para almacenar información de usuarios, proyectos y tareas, y PostgreSQL como repositorio de vectores para el RAG.
- Hacer un login para que los usuarios puedan acceder a su información.

** V 0.0.2 **
- Definir una estructura de usuarios por empresas y perfiles de acceso.
- Definir una separacion entre los vectores de los usuarios para separar por empresas y evitar contaminación de información privada.
- Robustecer el manejo de excepciones y el registro de logs.

** V 0.0.3 **
- Construir un dashboard de usuario para manejo de proyectos, tareas y documentos.
- Construir un tablero de control para un usuario administrador del sistema, que pueda dar de alta, baja y cambiar usuarios.
- Construir un tablero de control para lider de proyecto que pueda agregar o retirar miembros de equipo, asi como asignar y reasignar proyectos y tareas a los miembros del equipo.
- Implementar en la pestaña de documentos la capacidad de referenciar enlaces a documentos creados por el sistema, como demandas, amparos y solicitudes dependiendo de una plantilla que se puede utilizar para generarlos.
- Implementar en la pestaña de documentos la funcionalidad de poner sólo enlaces a los documentos refernciados como ligas html que apunten al sistema de archivos local (con rutas relativas para poderlas migrar posteriormente), y que el usuario pueda abrirlos dando click (fuera del sistema).

** V 0.0.4 **
- Construir un backoffice para que un usuario superadminstrador pueda tener acceso a todos los elementos del sistema sin importar la compañía o equipo, y que tenga permisos para realizar todas las acciones.
- Dotar al sistema de la funcionalidad de calendarizar y dar seguimiento a tareas para que la gestión de proyecto sea más completa.
- Crear un mecanismo de rotación de logs para que no se queden sin espacio.
- Crear un mecanismo para consulta remota de logs para automatizaciones.

** V 0.0.5 **
- Re-arquitectura a un modelo Multi-Tenant para dar servicio a múltiples compañías con aislamiento de datos estricto.
- Se adopta un patrón "Database-per-Tenant", donde cada compañía tiene su propio conjunto de bases de datos privadas.
- La nueva arquitectura de servicios en Docker es:
  - `frontend`: Servicio compartido de React.
  - `backend`: API compartida de FastAPI, diseñada para ser escalable.
  - `postgres-public`: Base de datos compartida para vectores de documentos públicos.
  - `*-tenant-<nombre>`: Conjunto de bases de datos (PostgreSQL y MongoDB) provisionadas por cada compañía.
- Se implementa un script de CI/CD local (`deploy_test.sh`) para automatizar pruebas y despliegues al entorno de desarrollo.
- Se externalizan todos los secretos y configuraciones a un archivo `.env`.
- Se introduce un framework de pruebas (`pytest`) en el backend.

** V 0.0.6 **
- Agregar nuevas funcionalidades al backoffice para que un usuario superadminstrador pueda tener acceso a todos los elementos del sistema sin importar la compañía o equipo, y que tenga permisos para realizar todas las acciones.