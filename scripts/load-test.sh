#!/usr/bin/env bash
# Drives enough traffic at the backend to make the HPA scale it up.
#
#   ./scripts/load-test.sh http://washq.local 60 20
#
# Watch it work from another terminal:
#   kubectl get hpa -n washq -w
#   kubectl get pods -n washq -w

set -uo pipefail

BASE=${1:-http://washq.local}
SECONDS_TO_RUN=${2:-60}
WORKERS=${3:-20}

echo "hitting $BASE for ${SECONDS_TO_RUN}s with $WORKERS workers"

worker() {
  local deadline=$(( $(date +%s) + SECONDS_TO_RUN ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    # /api/stats is the most expensive read, it aggregates both tables.
    curl -s -o /dev/null "$BASE/api/stats"
    curl -s -o /dev/null "$BASE/api/machines"
    curl -s -o /dev/null "$BASE/api/bookings?limit=50"
  done
}

for _ in $(seq 1 "$WORKERS"); do
  worker &
done
wait

echo "done. check: kubectl get hpa -n washq"
