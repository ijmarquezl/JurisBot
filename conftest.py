import os

# Hermetic environment for the test suite: dummy credentials and local
# endpoints so tests never depend on real API keys, external services,
# or a particular developer shell. Values set with setdefault can still
# be overridden by individual test modules that need specific mocks.
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("LLM_URL", "http://localhost:11434/v1")
os.environ.setdefault("LLM_MODEL_NAME", "test-model")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGO_DB_NAME", "test_jurisconsultor")
os.environ.setdefault("MONGO_MEMORY_DB_NAME", "test_jurisconsultor_memory")
os.environ.setdefault("PUBLIC_POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/public")
os.environ.setdefault("PRIVATE_POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/private")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
