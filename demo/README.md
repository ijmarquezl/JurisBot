# JurisBot — Instancia DEMO (nativa, sin Docker)

Instancia de demostración que corre la pila completa (backend FastAPI + agente
LangGraph + RAG pgvector + frontend React) sin Docker, usando servicios locales
descargados en esta carpeta y el LLM vía **Ollama en el equipo Koshi** (gratis,
sin cuotas).

## Requisitos
- `uv` (ya usado para crear `demo/venv`)
- MongoDB y PostgreSQL **binarios descargados localmente** en `demo/` (no requieren root)
- **Ollama en Koshi encendido y visible en Tailscale** (`koshi.tailc1c9cf.ts.net`)
  con el modelo `gemma4:latest` (tool-calling verificado)
- Internet solo para la descarga inicial de HuggingFace (modelo de embeddings)

## Arranque

### 1. Servicios de datos (MongoDB :27017 + PostgreSQL :5432)
```bash
bash demo/start_services.sh   # dejarlo corriendo (job de larga duración)
```

### 2. Backend (FastAPI :8000)
```bash
set -a; source demo/.env.demo; set +a
export GROQ_API_KEY="$(grep '^OPENROUTER_API_KEY=' .env | cut -d= -f2-)"
export HF_HOME="$PWD/demo/hf" PYTHONPATH=app:.
cd jurisconsultor
../demo/venv/bin/python -m uvicorn infrastructure.web.main:app --host 127.0.0.1 --port 8000
```

### 3. Frontend (estático + proxy /api :8080)
```bash
# una sola vez: construir el bundle
(cd jurisconsultor/frontend && VITE_API_URL=/api npm run build)
# servir
demo/venv/bin/python demo/serve_frontend.py --port 8080
```
Abrir: **http://127.0.0.1:8080** — usuario `admin@demo.com` / `Demo12345!`

### 4. Corpus legal (RAG)
```bash
set -a; source demo/.env.demo; set +a
export HF_HOME="$PWD/demo/hf" PYTHONPATH=app:.
cd jurisconsultor
../demo/venv/bin/python db_migration.py public          # crea tablas (auto-detecta dims)
cd ..
nice -n 19 demo/venv/bin/python -u demo/ingest_corpus.py # ingesta progresiva
```

## Verificación rápida
```bash
curl http://127.0.0.1:8000/                          # {"status":"ok"}
curl -s -X POST http://127.0.0.1:8000/api/token \
  -d "username=admin@demo.com&password=Demo12345!"   # JWT
```

## Notas
- LLM: **Ollama en Koshi** (`http://koshi.tailc1c9cf.ts.net:11434/v1`, modelo
  `gemma4:latest`). Si Koshi está apagado, el chat no responde. Alternativas
  probadas: Ollama local (`127.0.0.1:11434/v1` con `llama3.2:latest`) u OpenRouter
  free (`minimax/minimax-m3:free`, sujeto a cuota diaria).
- Embeddings: `intfloat/multilingual-e5-small` (384 dims) para que la ingesta y
  las consultas sean rápidas en CPU. Producción usa
  `wilfredomartel/multilingual-e5-large-es-legal-v2` (1024 dims); la demo prioriza
  velocidad (~9x). Para usar el modelo grande: cambiar `EMBEDDING_MODEL_NAME` en
  `demo/.env.demo`, re-migrar (`db_migration.py public`) y re-ingerir.
- Velocidad de respuesta: ~1.5 min (estado/gestión) y ~3-4 min (preguntas RAG)
  con `gemma4:latest` en CPU; el LLM se puede cambiar a otro modelo en
  `demo/.env.demo` (`LLM_MODEL_NAME`) sin tocar código.
- `demo/.env.demo` no contiene secretos reales; la clave de OpenRouter/Groq se
  inyecta al arrancar desde el `.env` raíz si se usan esos proveedores.
