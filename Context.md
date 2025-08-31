Quiero tu ayuda para construir una aplicación web llamada "JurisBot".

**Propósito:** Es un agente de IA que puede ayudar a los abogados a gestionar sus tareas y proyectos de manera eficiente.

**Público objetivo:** Abogados y pasantes de derecho que requieren acceso a informacion legal y que desean eficientar sus tareas.

**Funcionalidades clave:**
** Funcionalidades de Backend **
1. ** Autenticación:** Un usuario puede iniciar sesión con su nombre de usuario y contraseña.
2. ** Creación de proyectos:** Un abogado administrador puede crear un proyecto, darle un nombre y añadir a los miembros del equipo.
3. ** Creación y gestión de tareas:** Un abogado lider sera el encargado de crear tareas y asignarlas a abogados y pasantes dentro de su equipo.
4. ** Asignación de tareas:** Un abogado puede asignar una tarea a otro miembro del equipo.
5. ** Comentarios en tareas:** Los miembros del equipo pueden dejar comentarios en cada tarea para mantener la comunicación.
6. ** Panel de control (Dashboard):** Cada miembro del equipo debe tener una vista general de todas sus tareas pendientes, las que están en progreso y las completadas.
7. ** Notificaciones:** Se envían notificaciones por correo electrónico cuando se te asigna una nueva tarea o alguien comenta en una de tus tareas.
8. ** Archivos:** Cada usuario tendrá acceso a los archivos de sus tareas y proyectos, así como a la información pertinente de leyes, demandas, amparos, etc.
9. ** Acervo:** Habrá un proceso independiente corriendo en background para encontrar, descargar y vectorizar documentos de leyes públicas y documentos privados.  Los repositorios de acervo estarán almacenados en MongoDB.
10. ** Documentos privados:** Los documentos privados estarán almacenados en MongoDB.
11. ** Agente:** Habrá un agente de IA que podrá ayudar a los abogados a gestionar sus tareas y proyectos de manera eficiente, que conversará con ellos para responder a sus preguntas sobre legislación y documentos.
12. ** Vectores:** La base de datos de vectores será una PostgreSQL.
13. ** Embeddings:** El Modelo de embedding se encontrará localmente.


** Funcionalidades de Frontend **
1. ** Login:** Un usuario puede iniciar sesión con su nombre de usuario y contraseña.
2. ** Busqueda:** Un usuario puede buscar proyectos y tareas por nombre, por tipo de asunto, por fecha, por entidad federativa y por estatus.  También puede buscar en los archivos de leyes públicas y documentos privados para encontrar documentos referencia para sus tareas.
3. ** Dominio de tareas:** Cada usuario tendrá acceso a sus propias tareas y proyectos, así como a los de su equipo.
4. ** Panel de control:** Cada usuario tendrá acceso a su panel de control, donde podrá ver sus tareas y proyectos.
5. ** Notificaciones:** Se envían notificaciones por correo electrónico cuando se te asigna una nueva tarea o alguien comenta en una de tus tareas.
6. ** Archivos:** Cada usuario tendrá acceso a los archivos de sus tareas y proyectos, así como a la información pertinente de leyes, demandas, amparos, etc.

**Aspectos técnicos:**
- La gestión del proyecto se realizará con uv.
- Quiero que sea una aplicación web.
- Estoy abierto a sugerencias de tecnologías, pero me gustaría algo robusto y escalable. Podríamos considerar React para el frontend y Python + FastAPI para el backend.
- Necesitará una base de datos MongoDB para almacenar usuarios, proyectos y tareas.
- La base de datos MongoDB se encuentra en la dirección: 10.29.93.24:2717
- El Modelo general se encuentra en la dirección: http://10.29.93.56:11434, y es el "llama3"
- El Modelo de embedding se llama 'wilfredomartel/multilingual-e5-large-es-legal-v2', y para utilizarlo utiliza como referencia el archivo Embedding_Model.md