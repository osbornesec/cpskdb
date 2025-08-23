#!/bin/sh
# POSIX-safe strict mode (no pipefail in /bin/sh)
set -eu

# Configurable endpoint
QDRANT_HOST="${QDRANT_HOST:-qdrant}"
QDRANT_PORT="${QDRANT_PORT:-6333}"
BASE_URL="http://${QDRANT_HOST}:${QDRANT_PORT}"

# Helper: HEAD/health check using wget or curl
has_wget() { command -v wget >/dev/null 2>&1; }
has_curl() { command -v curl >/dev/null 2>&1; }

# Wait for Qdrant with timeout
attempts=0
max_attempts=30
while [ $attempts -lt $max_attempts ]; do
  if has_wget && wget --quiet --tries=1 --timeout=5 --spider "${BASE_URL}/healthz"; then
    echo 'Qdrant accessible via service discovery'
    break
  elif has_curl && curl -fsS --max-time 5 -o /dev/null "${BASE_URL}/healthz"; then
    echo 'Qdrant accessible via service discovery'
    break
  fi
  echo "Waiting for Qdrant... (attempt $((attempts + 1))/$max_attempts)"
  sleep 2
  attempts=$((attempts + 1))
done
    echo 'Qdrant accessible via service discovery'
    break
  fi
  echo "Waiting for Qdrant... (attempt $((attempts + 1))/$max_attempts)"
  sleep 2
  attempts=$((attempts + 1))
done

if [ $attempts -eq $max_attempts ]; then
  echo "ERROR: Qdrant health check failed after $max_attempts attempts"
  exit 1
fi

# Verify service discovery by getting service info with robust error handling
if wget --quiet --tries=3 --timeout=10 -O /tmp/info.json http://qdrant:6333/; then
  echo 'Service discovery successful - got service info'
  if command -v jq >/dev/null 2>&1; then
    jq -e '.title' /tmp/info.json >/dev/null && echo 'Service info validated with jq'
  else
    grep -q '"title"' /tmp/info.json && echo 'Service info contains expected title field'
  fi
else
  echo 'ERROR: Service discovery failed - could not get service info from http://qdrant:6333/'
  exit 1
fi

echo 'Service discovery verification complete - SUCCESS'
