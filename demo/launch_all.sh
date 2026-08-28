#!/bin/bash
# Launch ALL JurisBot demo services as detached processes (survive shell/job cleanup).
# Usage: bash demo/launch_all.sh
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export LD_LIBRARY_PATH="$ROOT/demo/postgres/root/usr/lib/postgresql/18/lib:$ROOT/demo/postgres/root/usr/lib/x86_64-linux-gnu"
PGBIN="$ROOT/demo/postgres/root/usr/lib/postgresql/18/bin"
mkdir -p "$ROOT/demo/run" "$ROOT/demo/postgres/sock"

say() { echo "[launch] $*"; }

# --- 1. MongoDB ---
if ! pgrep -f "mongod.*demo/mongodb" >/dev/null; then
  say "starting mongod..."
  setsid "$ROOT/demo/mongodb/bin/mongod" --dbpath "$ROOT/demo/mongodb/data" \
    --logpath "$ROOT/demo/mongodb/log/mongod.log" --bind_ip 127.0.0.1 --port 27017 \
    --pidfilepath "$ROOT/demo/run/mongod.pid" >/dev/null 2>&1 < /dev/null &
  disown
else
  say "mongod already running"
fi

# --- 2. PostgreSQL ---
if ! pgrep -f "postgres.*demo/postgres/data" >/dev/null; then
  say "starting postgres..."
  "$PGBIN/pg_ctl" -D "$ROOT/demo/postgres/data" -l "$ROOT/demo/postgres/log/pg.log" \
    -o "-p 5432 -c listen_addresses=127.0.0.1 -k $ROOT/demo/postgres/sock" start
else
  say "postgres already running"
fi

# --- wait for data services ---
for i in $(seq 1 30); do
  pg_ok=0; mongo_ok=0
  "$PGBIN/psql" -h 127.0.0.1 -p 5432 -U postgres -c "SELECT 1" >/dev/null 2>&1 && pg_ok=1
  "$ROOT/demo/venv/bin/python" -c "import socket;s=socket.socket();s.settimeout(1);s.connect(('127.0.0.1',27017))" >/dev/null 2>&1 && mongo_ok=1
  [ $pg_ok -eq 1 ] && [ $mongo_ok -eq 1 ] && break
  sleep 1
done
say "mongodb: $([ $mongo_ok -eq 1 ] && echo UP || echo DOWN) | postgres: $([ $pg_ok -eq 1 ] && echo UP || echo DOWN)"

# --- 3. Backend (FastAPI) ---
if ! pgrep -f "uvicorn infrastructure.web.main:app" >/dev/null; then
  say "starting backend..."
  set -a
  source "$ROOT/demo/.env.demo"
  set +a
  ORKEY=$(grep "^OPENROUTER_API_KEY=" "$ROOT/.env" | cut -d= -f2-)
  export GROQ_API_KEY="$ORKEY" OPENROUTER_API_KEY="$ORKEY"
  export HF_HOME="$ROOT/demo/hf" PYTHONPATH=app:.
  cd "$ROOT/jurisconsultor"
  setsid "$ROOT/demo/venv/bin/python" -m uvicorn infrastructure.web.main:app \
    --host 127.0.0.1 --port 8000 >>"$ROOT/demo/run/backend.log" 2>&1 < /dev/null &
  disown
  cd "$ROOT"
else
  say "backend already running"
fi

# --- 4. Frontend web server ---
if ! pgrep -f "serve_frontend.py" >/dev/null; then
  say "starting web server..."
  setsid "$ROOT/demo/venv/bin/python" "$ROOT/demo/serve_frontend.py" --port 8080 \
    >>"$ROOT/demo/run/web.log" 2>&1 < /dev/null &
  disown
else
  say "web server already running"
fi

sleep 8
say "--- status ---"
for p in 27017 5432 8000 8080; do
  (timeout 2 bash -c "echo > /dev/tcp/127.0.0.1/$p" 2>/dev/null && say "port $p UP") || say "port $p DOWN"
done
