# Demo

Two files go in this folder before submitting. Both are required by
SUBMISSION.md, and a missing video scores zero for M10 regardless of
everything else.

```
demo/presentation.mp4     the walkthrough video
demo/slides.pdf           the slide deck, at least 8 slides
```

## What the video has to show, in this order

1. The slides: what was built and the architecture
2. The codebase: folder structure and the key files
3. CI/CD: push a commit and show the GitHub Actions run go green
4. Terraform: `terraform plan`, then the AWS console showing the VPC and
   the EKS cluster
5. Argo CD: the application synced
6. Kubernetes: `kubectl get pods`, services and ingress, all healthy
7. Prometheus: the Targets page with the app `UP`
8. Grafana: the dashboard with live data

## Slides

At least eight, covering project overview, tech stack, architecture
diagram, CI/CD flow, infrastructure, Kubernetes setup, observability,
and what was learned.
