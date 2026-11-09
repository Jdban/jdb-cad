#!/usr/bin/env bash
# Stop the model viewer started by viewer/start.sh.
cd "$(dirname "$0")/.."
PIDFILE="viewer/.server.pid"
PID="$(cat "$PIDFILE" 2>/dev/null || true)"
if [[ -n "$PID" ]] && grep -q "viewer/serve.py" "/proc/$PID/cmdline" 2>/dev/null && kill "$PID"; then
  echo "viewer stopped"
else
  echo "viewer was not running (from start.sh)"
fi
rm -f "$PIDFILE"
