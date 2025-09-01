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

** V 0.0.4 **
- Identificar el proceso para construir un contenedor que pueda ser accedido de forma remota sin fallos (no localhost).
- Probar en un servidor docker.
- Publicar el servidor docker a Internet para pruebas remotas de especialistas.