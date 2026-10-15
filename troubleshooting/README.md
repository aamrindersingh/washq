# Troubleshooting

Two manifests that break on purpose, with the commands that find the
cause. Both were applied to the cluster and the output below is what came
back, not what I expected to come back.

## Broken image tag

```
kubectl apply -f troubleshooting/broken-image.yaml
kubectl get pods -n washq -l demo=broken-image
```

The pod never starts:

```
NAME                            READY   STATUS             RESTARTS   AGE
broken-image-8559975fdb-24qmx   0/1     ImagePullBackOff   0          25s
```

`kubectl logs` is no use here. There is no container yet, so there is
nothing to log. The answer is in the events:

```
kubectl describe pod -n washq -l demo=broken-image
```

```
Warning  Failed   Failed to pull image
  "ghcr.io/aamrindersingh/washq/backend:this-tag-was-never-built":
  failed to resolve reference: failed to authorize: failed to fetch
  anonymous token: unexpected status from GET request to
  https://ghcr.io/token?scope=repository%3A...%3Apull: 403 Forbidden
```

Worth reading that carefully, because the error is not the obvious one.
GHCR answers **403 Forbidden**, not 404, for a tag that does not exist.
A private or missing package looks identical from outside, since the
registry will not tell an anonymous caller which of the two it is.

So 403 here means one of three things, and they need different fixes:

- the tag really does not exist, usually a deploy pointed at a commit
  whose pipeline has not finished pushing
- the package is private and the cluster has no pull secret
- the package name is wrong

Checking the Packages page on GitHub separates them in a few seconds.

Clean up:

```
kubectl delete -f troubleshooting/broken-image.yaml
```

## Service with a selector that matches nothing

```
kubectl apply -f troubleshooting/broken-service.yaml
kubectl get svc -n washq broken-service
```

The Service looks completely healthy. It has a ClusterIP and a port:

```
NAME             TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
broken-service   ClusterIP   10.96.175.29   <none>        8000/TCP   25s
```

But nothing answers on it, and there is no error anywhere. The giveaway
is an empty endpoint list:

```
kubectl get endpoints -n washq broken-service
```

```
NAME             ENDPOINTS   AGE
broken-service   <none>      25s
```

```
kubectl get endpointslice -n washq -l kubernetes.io/service-name=broken-service
```

Empty endpoints means no pod matches the selector. Comparing the two
shows why:

```
kubectl get pods -n washq -l app.kubernetes.io/component=backend --show-labels
```

The pods carry `app.kubernetes.io/component=backend`. The Service asks
for `app.kubernetes.io/component=api`, which nothing has. Correcting the
selector fills the endpoint list immediately.

This is the more useful of the two to have seen before, because
Kubernetes reports no problem at all. `kubectl get svc` looks right, the
deployment is healthy, and requests just hang. Endpoints is the first
thing to check whenever a Service is reachable but never answers.

Note that `kubectl get endpoints` now prints a deprecation warning. The
Endpoints API is being replaced by EndpointSlice, and on newer clusters
`kubectl get endpointslice` is the command to reach for.

Clean up:

```
kubectl delete -f troubleshooting/broken-service.yaml
```
