# Screenshots

What the rubric asks for, and where each one is. Anything not here yet is
listed at the bottom with the reason.

| Module | Rubric asks for | File |
|---|---|---|
| M1 | Running application in the browser | `01-app-desktop.png` |
| M1 | Responsive UI | `02-app-mobile.png` |
| M3 | Commit history, at least 10 commits | `03-commit-history.jpg` |
| M4 | Browser at `localhost:3000` with the app loaded | `01-app-desktop.png` |
| M5 | GitHub Actions run, green pipeline | `04-github-actions-green.jpg` |
| M5 | GHCR package page with SHA based tags | `05-ghcr-packages.jpg` |
| M6 | Trivy scan output from a pipeline run | `06-trivy-scan.jpg` |
| M9 | Prometheus Targets page, app `UP` | `08-prometheus-targets.png` |
| M9 | Grafana dashboard with a populated panel | `09-grafana-dashboard.png` |
| video | Argo CD application synced | `10-argocd-synced.png` |

## Terminal output

The rubric asks for these as screenshots. They are in
[`../evidence/`](../evidence) as text files instead, captured straight
from the commands, so the exact output can be read and searched rather
than squinted at:

| Module | Command | File |
|---|---|---|
| M2 | `pytest -v`, 21 passed | `evidence/01-pytest.txt` |
| M4 | `docker compose ps` and `/health` | `evidence/02-docker-compose.txt` |
| M7 | `terraform validate` and `plan` | `evidence/05-terraform-plan.txt` |
| M8 | `kubectl get pods / svc / ingress / hpa`, `helm list` | `evidence/03-kubernetes.txt` |
| M8 | HPA scaling from 2 pods to 4 under load | `evidence/06-hpa-scaling.txt` |
| M9 | `curl /metrics` | `evidence/04-metrics.txt` |
| video | Argo CD synced and healthy | `evidence/07-argocd.txt` |

These same commands are run live in the presentation video, which is
where the terminal screenshots the rubric describes actually come from.

## Still to capture

Four, all of which need the EKS cluster running, and all of which are
captured in the same session as the video recording:

- AWS Console showing the VPC and the EKS cluster in `ap-south-1` (M7)
- `terraform destroy` completing (M7, and it is on the submission
  checklist)
- `kubectl get pods`, `get svc` and `helm list` against EKS rather than
  the local kind cluster (M8)
- The app in a browser through the EKS LoadBalancer address (M8)

The Prometheus, Grafana and Argo CD screenshots above were taken against
a local kind cluster. They are real and reproducible, but they will be
retaken against EKS during recording so every screenshot shows the same
cluster.
