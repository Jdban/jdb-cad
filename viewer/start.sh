#!/usr/bin/env bash
# Start the model viewer in the background (safe to run again: it won't start twice).
# Usage: viewer/start.sh [port]      stop with: viewer/stop.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PORT="${1:-8765}"
PIDFILE="viewer/.server.pid"

if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "viewer already running: http://localhost:$PORT/ (pid $(cat "$PIDFILE"))"
  exit 0
fi
rm -f "$PIDFILE"   # stale
if curl -sf "http://localhost:$PORT/api/models" >/dev/null 2>&1; then
  echo "something is already serving http://localhost:$PORT/ (started elsewhere?)"
  exit 0
fi

nohup python3 viewer/serve.py "$PORT" >viewer/.server.log 2>&1 &
echo $! >"$PIDFILE"
for _ in 1 2 3 4 5 6 7 8 9 10; do
  curl -sf "http://localhost:$PORT/api/models" >/dev/null 2>&1 && break
  sleep 0.3
done
echo "viewer running: http://localhost:$PORT/ (pid $(cat "$PIDFILE"), log viewer/.server.log)"
