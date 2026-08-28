#!/bin/bash
# Starts JurisBot demo infra services (MongoDB + PostgreSQL) and keeps them alive.
# Run as a long-lived background job: bash demo/start_services.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export LD_LIBRARY_PATH="$ROOT/demo/postgres/root/usr/lib/postgresql/18/lib:$ROOT/demo/postgres/root/usr/lib/x86_64-linux-gnu"
PGBIN="$ROOT/demo/postgres/root/usr/lib/postgresql/18/bin"

echo "[services] starting mongod..."
"$ROOT/demo/mongodb/bin/mongod" --dbpath "$ROOT/demo/mongodb/data" \
  --logpath "$ROOT/demo/mongodb/log/mongod.log" --bind_ip 127.0.0.1 --port 27017 &
MONGO_PID=$!

echo "[services] starting postgres..."
mkdir -p "$ROOT/demo/postgres/sock"
"$PGBIN/pg_ctl" -D "$ROOT/demo/postgres/data" -l "$ROOT/demo/postgres/log/pg.log" \
  -o "-p 5432 -c listen_addresses=127.0.0.1 -k $ROOT/demo/postgres/sock" start

echo "[services] waiting for mongod on 27017..."
for i in $(seq 1 30); do
  if "$ROOT/demo/mongodb/bin/mongod" --version >/dev/null 2>&1; then break; fi
  # probe via mongosh-less approach: use python if available, else fall back
  python3 - <<'PY' 2>/dev/null && break
import socket
s = socket.socket(); s.settimeout(1)
try:
    s.connect(("127.0.0.1", 27017)); print("mongo up")
except Exception:
    raise SystemExit(1)
PY
  sleep 1
done

echo "[services] checking postgres..."
"$PGBIN/psql" -h 127.0.0.1 -p 5432 -U postgres -c "SELECT 'postgres up';" >/dev/null 2>&1 && echo "[services] postgres OK"

echo "[services] all services up. Keeping job alive (Ctrl+C / job_kill to stop)."
wait $MONGO_PID
