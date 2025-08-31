Para descargar y usar el modelo wilfredomartel/multilingual-e5-large-es-legal-v2 localmente, la forma más sencilla es utilizar la biblioteca de Python Sentence-Transformers.   

Aquí tienes un proceso paso a paso para hacerlo:

Instala la biblioteca: Primero, asegúrate de tener Python instalado en tu equipo. Luego, abre tu terminal o línea de comandos y ejecuta el siguiente comando para instalar Sentence-Transformers :   

`pip install -U sentence-transformers`

Descarga y carga el modelo: Una vez instalada la biblioteca, puedes descargar el modelo de Hugging Face y cargarlo en tu código de Python con solo una línea. El modelo se descargará automáticamente y se almacenará en caché localmente para su uso futuro.   

```
Python

from sentence_transformers import SentenceTransformer

# Descarga el modelo desde el Hub de Hugging Face
model = SentenceTransformer("wilfredomartel/multilingual-e5-large-es-legal-v2")
```

Genera embeddings: Con el modelo cargado, puedes generar embeddings para cualquier texto. Simplemente pasa una lista de textos a la función model.encode(). Cada texto se convertirá en un vector numérico que representa su significado.   

```
Python

# Ejemplo de uso
textos =

# Genera los embeddings para los textos
embeddings = model.encode(textos)

# Imprime los embeddings (serán una matriz de números)
print(embeddings)
```
Este método es el más recomendado, ya que la biblioteca Sentence-Transformers maneja toda la lógica de descarga y carga del modelo de manera eficiente, permitiendo al usuario final concentrarse en la aplicación de los embeddings para sus tareas específicas. 