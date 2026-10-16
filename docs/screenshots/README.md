# Screenshots

Every screenshot the rubric asks for, and where it is.

## Browser

| Module | What the rubric asks for | File |
|---|---|---|
| M1 | Running application in the browser | `01-app-desktop.png` |
| M1 | Responsive UI | `02-app-mobile.png` |
| M3 | Commit history, at least 10 commits | `03-commit-history.jpg` |
| M4 | Browser at `localhost:3000` with the app loaded | `01-app-desktop.png` |
| M5 | GitHub Actions run, green pipeline | `04-github-actions-green.jpg` |
| M5 | GHCR package page with SHA based tags | `05-ghcr-packages.jpg` |
| M6 | Trivy scan output from a pipeline run | `06-trivy-scan.jpg` |
| M9 | Prometheus Targets page showing the app `UP` | `08-prometheus-targets.png` |
| M9 | Grafana dashboard with a populated panel | `09-grafana-dashboard.png` |
| video | Argo CD application synced | `10-argocd-synced.png` |
| M8 | App in a browser through the Ingress at `washq.local` | `17-app-via-ingress.jpg` |
| M7 | AWS Console, EKS cluster Active in `ap-south-1` | `19-aws-eks-console.jpg` |
| M7 | AWS Console, both public subnets in the VPC | `20-aws-vpc-subnets.jpg` |

## Terminal

| Module | Command | File |
|---|---|---|
| M2 | `pytest -v`, 21 passed | `07-pytest-terminal.png` |
| M4 | `docker compose ps` and `/health` | `11-docker-compose.png` |
| M8 | `kubectl get pods / svc / ingress / hpa` and `helm list` | `12-kubectl-helm.png` |
| M9 | `curl /metrics` | `13-metrics-endpoint.png` |
| M7 | `terraform validate` and `terraform plan` | `14-terraform-plan.png` |
| M8 | HPA going from 2 pods to 4 under load | `15-hpa-scaling.png` |
| video | Argo CD synced, from the command line | `16-argocd-cli.png` |
| M8 | The Ingress host answering, and the Ingress object | `18-ingress-curl.png` |
| M7 | The VPC, subnets and cluster read back from AWS | `21-aws-resources.png` |
| M8 | `kubectl`, `helm list` and /health, all against the EKS cluster | `22-eks-kubectl-helm.png` |
| M7 | `terraform destroy` finishing, and AWS confirmed empty afterwards | `23-terraform-destroy.png` |

Each of these is the output in [`../evidence/`](../evidence) drawn into a
terminal image. The text was written by the commands themselves, and the
matching `.txt` file is in the repo next to it so anything can be checked
or copied.

## Everything is captured

Nothing is outstanding. The EKS screenshots were taken against a real
cluster in ap-south-1, which was then destroyed, and the destroy output
is in the table above.

## One thing worth knowing about `helm list`

`helm list` only shows a release while Helm owns it. Argo CD renders the
chart and applies the result, so it never creates a Helm release, and
once Argo takes over the namespace `helm list` comes back empty.

That is why the order matters. The M8 screenshot above was taken after
`helm upgrade --install`, which is what that module is marked on, and
Argo CD was pointed at the namespace afterwards for the GitOps part. Both
are real, they just cannot be true at the same instant.
