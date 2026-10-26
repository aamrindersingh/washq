#!/usr/bin/env bash
# Puts load on the backend from a pod inside the cluster, so it does not
# depend on a port forward or a load balancer. Use this on EKS, where the
# ingress is reached through a tunnel that would choke on real load.
#
#   ./scripts/load-in-cluster.sh 120
#
# Watch the autoscaler react from another terminal:
#   kubectl get hpa -n washq -w

set -uo pipefail

SECONDS_TO_RUN=${1:-120}
NS=${NS:-washq}
TARGET=${TARGET:-http://washq-washq-backend:8000/api/stats}

kubectl delete pod washq-load -n "$NS" --ignore-not-found >/dev/null 2>&1

# Twelve requests at a time against /api/stats, which is the most
# expensive read because it counts across both tables.
kubectl run washq-load -n "$NS" --image=busybox:1.36 --restart=Never \
  --labels=app=washq-load -- /bin/sh -c "
    end=\$((\$(date +%s) + $SECONDS_TO_RUN))
    while [ \$(date +%s) -lt \$end ]; do
      for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
        wget -q -O /dev/null $TARGET &
      done
      wait
    done" >/dev/null

echo "load running for ${SECONDS_TO_RUN}s from pod washq-load"
echo "remove it after: kubectl delete pod washq-load -n $NS"
