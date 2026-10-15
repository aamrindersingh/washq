# GitOps with Argo CD

The cluster is not deployed to by hand. Argo CD watches this repository
and makes the cluster match it. A deploy is a commit.

## Install Argo CD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --for=condition=available --timeout=300s \
  deployment/argocd-server -n argocd
```

## Point it at this repo

```bash
kubectl apply -f gitops/argocd-application.yaml
kubectl get application -n argocd washq
```

Within a minute the app reports `Synced` and `Healthy`, and the washq
namespace has the same pods `helm install` would have created.

## Open the UI

```bash
kubectl port-forward -n argocd svc/argocd-server 8081:443
```

Then <https://localhost:8081>, user `admin`. The first password is
generated at install:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d
```

## How a deploy works

1. Push to `main`
2. The pipeline runs tests, builds both images, scans them with Trivy and
   pushes them to GHCR tagged with the commit SHA
3. Update `image.tag` in `gitops/argocd-application.yaml` to that SHA and
   push
4. Argo CD notices within three minutes and rolls the new images out

Nobody runs `helm upgrade` against the cluster. If someone does, Argo
puts it back, because `selfHeal` is on.

## Two settings worth explaining

**`selfHeal: true`** means manual changes to the cluster are reverted.
That is the point of GitOps: the repo is the only source of truth. It
also means debugging by editing a live Deployment will not stick, which
is surprising the first time.

**`ignoreDifferences` on `/spec/replicas`** stops Argo fighting the HPA.
The chart does not set `replicas` when autoscaling is on, but the running
Deployment always has a number in that field. Without this rule Argo
reads the scaled count as drift and resets it, undoing the autoscaler
every few minutes.
