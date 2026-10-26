# Presentation video

The video is in this folder as [`presentation.mp4`](presentation.mp4),
about 30 minutes, 1080p with audio.

It is also on Google Drive, which plays in the browser without
downloading the 84 MB file first:

**https://drive.google.com/file/d/1IlXBg1v_Q8c3KanZbE9rdtLnG4AWGIO-/view?usp=sharing**

## What it covers, in order

1. The slides: what WashQ is and the architecture
2. The codebase on GitHub
3. A change pushed to main, and the GitHub Actions pipeline running end
   to end, including the Trivy scan and the image landing in GHCR
4. `terraform plan`, then the VPC and EKS cluster in the AWS Console
5. Argo CD synced, a live deploy of that change, and self healing
6. `kubectl get pods`, services, ingress, HPA and `helm list` on EKS,
   and the booking rule working in the app
7. Prometheus targets showing the backend UP
8. The Grafana dashboard live, with the autoscaler adding pods under load
9. Troubleshooting a broken Service

The slides are [`slides.pdf`](slides.pdf).
