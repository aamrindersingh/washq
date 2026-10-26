# WashQ

Book a washing machine in your hostel so two people never claim the same
one at the same time.

Every hostel has the same Sunday evening problem. All the machines are
taken, someone's wet clothes have been sitting in one for two hours, and
nobody knows which machine is actually broken. WashQ puts the laundry
room on a screen: every machine shows whether it is free, running or out
of order, and a student can take a 45 minute slot that nobody else can
take.

Built as the DevOps capstone project. The app itself is deliberately
small, because the point of the project is everything around it: tests,
containers, a pipeline, a security gate, infrastructure as code,
Kubernetes, and monitoring.

**Amrinder Singh, 24BCS10596**

---

## What it does

- A board of every machine, colour coded: green is free, amber is
  running, red is out of order
- Book a 45 minute slot on a machine
- The same machine cannot be booked twice for overlapping times. This is
  the one real rule in the app and most of the tests are about it
- Report a machine broken, so nobody books it
- Mark a wash collected, or cancel a booking, which frees the slot again
- A counter row showing free machines, machines running, broken
  machines, and bookings today

Back to back slots are allowed on purpose. A wash ending at 10:45 and
another starting at 10:45 do not clash, because touching edges are not an
overlap.

---

## Architecture

```
                         browser
                            |
                            v
                   +------------------+
                   |     Ingress      |   nginx ingress controller
                   +------------------+
                     /              \
                 "/"                "/api"
                   |                   |
         +-----------------+   +-----------------+
         |    frontend     |   |     backend     |
         |  React + nginx  |   | FastAPI, uvicorn|
         |   2 replicas    |   |  2 to 6 replicas|
         +-----------------+   +-----------------+
                                        |
                                        v
                               +-----------------+
                               |    Postgres     |
                               |   StatefulSet   |
                               +-----------------+

         Prometheus scrapes the backend's /metrics
         Grafana reads Prometheus and draws the dashboard
```

The frontend container is nginx serving a built React bundle. It also
proxies `/api` through to the backend, so the browser only ever talks to
one origin and there is no CORS in production.

The backend is FastAPI. It owns all the booking logic and the database.

Postgres runs as a StatefulSet with a volume, so restarting a pod does
not wipe the bookings.

The backend scales on CPU between 2 and 6 pods. The frontend stays at 2.

---

## Tech stack

| Layer | What |
|---|---|
| Frontend | React 18, Vite, plain CSS, served by nginx |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Pydantic v2 |
| Database | PostgreSQL 16, schema managed by Alembic |
| Tests | pytest, 22 tests against a throwaway SQLite database |
| Containers | Docker, multi-stage build for the frontend |
| CI/CD | GitHub Actions, images published to GHCR |
| Security | Trivy image scan, fails the build on HIGH or CRITICAL |
| Infrastructure | Terraform, AWS VPC and EKS |
| Orchestration | Kubernetes, Helm chart, Ingress, HPA |
| Monitoring | Prometheus and Grafana via kube-prometheus-stack |

---

## Running it locally

You need Docker. Nothing else.

```bash
git clone https://github.com/aamrindersingh/washq.git
cd washq
docker compose up --build
```

Then open <http://localhost:3000>.

Three containers start. Postgres comes up first and compose waits for
`pg_isready` before starting the backend. The backend runs the Alembic
migration, seeds five machines so the board is not empty, then starts
uvicorn. The frontend is nginx serving the built React app.

| What | Where |
|---|---|
| App | <http://localhost:3000> |
| API docs | <http://localhost:3000/api/docs> |
| Metrics | <http://localhost:8000/metrics> |

To stop it and throw the database away:

```bash
docker compose down -v
```

### Running the backend without Docker

```bash
cd backend
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -v
```

The tests need no database running. They create a temporary SQLite file
and point the app at it.

---

## The API

| Method | Path | What it does |
|---|---|---|
| GET | `/health` | Liveness. Does not touch the database |
| GET | `/health/ready` | Readiness. Runs a query |
| GET | `/api/machines` | Every machine with its live status |
| POST | `/api/machines` | Add a machine |
| PUT | `/api/machines/{id}/status` | Mark free or out of order |
| DELETE | `/api/machines/{id}` | Remove a machine |
| GET | `/api/bookings` | Bookings, paged and filterable |
| GET | `/api/bookings/{id}` | One booking |
| POST | `/api/bookings` | Book a slot |
| PUT | `/api/bookings/{id}` | Reschedule or change status |
| DELETE | `/api/bookings/{id}` | Cancel |
| GET | `/api/stats` | Counts for the dashboard |
| GET | `/metrics` | Prometheus format |

Booking a taken slot returns `409` with a message saying when the machine
frees up:

```
$ curl -X POST localhost:8000/api/bookings -H 'Content-Type: application/json' \
    -d '{"machine_id":1,"student_name":"Rahul","room_number":"B-101","slot_start":"2026-10-16T10:00:00"}'

{"detail":"W1 is taken until 10:45"}
```

---

## Tests

```bash
cd backend && pytest -v
```

22 tests, all passing. Real output is in
[`docs/evidence/01-pytest.txt`](docs/evidence/01-pytest.txt).

The ones that matter are the clash cases:

- the same slot booked twice is refused
- a slot that starts partway through another is refused
- back to back slots are allowed
- cancelling frees the slot so it can be booked again
- the same time on a different machine is fine
- rescheduling onto a taken slot is refused

Tests never touch the real database. `conftest.py` sets `DATABASE_URL` to
a temporary SQLite file before `app.db` is imported, and overrides the
`get_db` dependency.

---

## CI/CD

[`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) runs on every
push to `main`.

```
   test (pytest)        frontend-build (npm ci + vite build)
          \                        /
           \                      /
            +--------+-----------+
                     |
          build image (backend and frontend, in parallel)
                     |
             Trivy scan HIGH,CRITICAL
                     |
          push to GHCR tagged with the commit SHA
```

Tests and the frontend build run first and in parallel. Nothing is built
until both pass, so a failing test stops the pipeline before any image
exists.

Each image is then built and loaded locally so Trivy scans the exact
image that would be published. The push only runs if the scan passes.

Images are tagged with the commit SHA. There is no `latest` tag, so any
deployment names one exact build and you can always tell which commit is
running.

```
ghcr.io/aamrindersingh/washq/backend:<sha>
ghcr.io/aamrindersingh/washq/frontend:<sha>
```

---

## Security scanning

Trivy scans both images in the pipeline for HIGH and CRITICAL
vulnerabilities and fails the job if it finds any that have a fix
available. Because the push step runs after the scan, a vulnerable image
is never published.

The scan uses `ignore-unfixed`, which skips CVEs that have no released
patch yet. That is a deliberate line: we cannot fix what upstream has not
fixed, but anything that does have a fix has to be fixed.

### A real finding

The first scan of the frontend image failed with 43 HIGH or CRITICAL
findings, and they all had fixes available. The worst was
**CVE-2026-31789**, a CRITICAL in `libcrypto3`, which is OpenSSL. The
`nginx:1.27-alpine` base image ships whatever Alpine packages were current
on the day that tag was built, and OpenSSL had been patched since.

The fix was one line in the Dockerfile:

```dockerfile
RUN apk upgrade --no-cache
```

That pulls Alpine's patched packages at build time. The rescan came back
with zero HIGH or CRITICAL findings with fixes available. The backend
image was already clean by the same standard: it reports 44 findings from
Debian packages, but every one of them is unfixed upstream, so there is
nothing to apply.

The lesson is that a pinned base image tag is not a safe base image tag.
It is frozen in time, and the longer it sits the more known holes it
carries.

---

## Infrastructure with Terraform

[`terraform/`](terraform) builds the AWS side.

| Resource | Detail |
|---|---|
| VPC | `10.20.0.0/16`, DNS support and hostnames on |
| Public subnets | Two, in two availability zones |
| Internet gateway and route table | Public route out |
| EKS cluster | Kubernetes 1.31 |
| Managed node group | 2 to 4 `m7i-flex.large` workers |
| Addons | vpc-cni, kube-proxy, coredns, metrics-server, aws-ebs-csi-driver |
| IAM | Roles for the control plane and the nodes, plus an IRSA role for the EBS driver |

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
aws eks update-kubeconfig --region ap-south-1 --name washq-cluster
```

`terraform plan` reports 24 resources to add. The real output is in
[`docs/evidence/05-terraform-plan.txt`](docs/evidence/05-terraform-plan.txt).

**The node instance type has to be Free Tier eligible** if the account is
on the AWS Free plan. `t3.medium` is not, and the failure is confusing:
the cluster builds normally, then the node group sits in `CREATE_FAILED`
for half an hour with `AsgInstanceLaunchFailures: The specified instance
type is not eligible for Free Tier`. The types that do work come from:

```bash
aws ec2 describe-instance-types --region ap-south-1 \
  --filters Name=free-tier-eligible,Values=true
```

`m7i-flex.large` is on that list and has 8 GiB, so it is the default
here. On a paid account any sensible type works.

**EKS does not install the EBS CSI driver**, even though it ships a `gp2`
StorageClass that points at `ebs.csi.aws.com`. Without the driver a
PersistentVolumeClaim sits in `Pending` with "waiting for a volume to be
created by the external provisioner", Postgres never schedules, and the
backend init container crash loops against a database that does not
exist. The backend looks like the problem and is only the symptom. The
addon is in `eks.tf`.

**That driver needs IRSA, not the node role.** Attaching
`AmazonEBSCSIDriverPolicy` to the node role is not enough: the controller
pod is not on the host network, cannot reach instance metadata, and dies
with `no EC2 IMDS role found`. So `iam.tf` creates an OIDC provider and a
role scoped to `system:serviceaccount:kube-system:ebs-csi-controller-sa`,
and the addon is given that role.

**An AWS Free plan account cannot create load balancers at all.** A
Service of type LoadBalancer stays `<pending>` and the event reads
`OperationNotPermitted: This AWS account currently does not support
creating load balancers`. Nothing in the config fixes that. The app was
reached through the ingress controller by port forward instead, and on a
paid account the same Ingress gets an ELB with no changes.

Two more details that are easy to miss:

The subnets carry `kubernetes.io/role/elb` and the cluster tag. Without
those tags a Service of type LoadBalancer never gets an address, and it
looks like the ingress controller is broken when the problem is really
the subnet.

The metrics-server addon is included because the HPA reads pod CPU from
it, and EKS does not install it by default. Without it the HPA sits at
`<unknown>` and never scales.

When you are done, and this matters because EKS is charged by the hour:

```bash
terraform destroy
```

```
Destroy complete! Resources: 24 destroyed.
```

**One thing `terraform destroy` will not clean up.** The Postgres volume
is created by Kubernetes, not by Terraform, so Terraform does not know it
exists. `helm uninstall` does not remove it either, because a
StatefulSet keeps its PersistentVolumeClaims on purpose so data survives
a reinstall. Destroy the cluster and the EBS volume is simply orphaned,
unattached and still billing.

So check after every destroy:

```bash
aws ec2 describe-volumes --region ap-south-1 \
  --filters Name=status,Values=available --query 'Volumes[].VolumeId'
```

Anything listed there is attached to nothing and costing money. Delete
the PVC before destroying, or delete the volume afterwards.

No AWS credentials are committed. Terraform reads them from the AWS CLI
config or the environment, and `terraform.tfvars` is gitignored.

---

## Kubernetes and Helm

```bash
kubectl apply -f k8s/namespace.yaml

helm upgrade --install washq ./helm/washq \
  -n washq \
  -f helm/washq/values-prod.yaml \
  --set image.tag=<commit-sha>
```

The chart creates:

- a Deployment and a ClusterIP Service for the backend
- a Deployment and a ClusterIP Service for the frontend
- Postgres as a StatefulSet with a volume claim, plus its Service
- an Ingress sending `/api` and `/metrics` to the backend and everything
  else to the frontend
- an HPA on backend CPU
- a ServiceMonitor so Prometheus finds the backend

Checking it:

```bash
kubectl get pods -n washq
kubectl get svc -n washq
kubectl get ingress -n washq
helm list -n washq
```

Real output is in
[`docs/evidence/03-kubernetes.txt`](docs/evidence/03-kubernetes.txt).

### Three things worth explaining

**Migrations run in an init container**, not at app startup. The API pod
does not accept traffic until the migration has finished, so it can never
serve requests against a database whose schema is behind.

**Liveness and readiness use different endpoints.** Liveness hits
`/health`, which does not touch the database. Readiness hits
`/health/ready`, which does. If both used the database, a slow query
would get healthy pods killed and restarted instead of just temporarily
pulled out of the Service.

**The backend Deployment has no `replicas` field when autoscaling is on.**
If Helm sets replicas and the HPA also sets it, every `helm upgrade`
resets the count and the two fight. Leaving it out hands ownership to the
HPA.

### Testing the chart without AWS

The whole stack runs on a local kind cluster for free, which is how it
was developed:

```bash
kind create cluster --config k8s/kind-cluster.yaml
docker build -t washq-backend:dev ./backend
docker build -t washq-frontend:dev ./frontend
kind load docker-image washq-backend:dev washq-frontend:dev --name washq

kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.3/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller --timeout=180s

kubectl apply -f k8s/namespace.yaml
helm upgrade --install washq ./helm/washq -n washq -f helm/washq/values-dev.yaml --wait
```

Add `127.0.0.1 washq.local` to `/etc/hosts`, then open
<http://washq.local:8080>.

---

## Autoscaling

The backend HPA targets 70% CPU and scales between 2 and 6 pods.

```bash
./scripts/load-test.sh http://washq.local 60 20
kubectl get hpa -n washq -w
```

Captured during a real run on the kind cluster:

```
# before load
NAME                  TARGETS       MINPODS   MAXPODS   REPLICAS
washq-washq-backend   cpu: 2%/70%   2         6         2

# during load
NAME                  TARGETS        MINPODS   MAXPODS   REPLICAS
washq-washq-backend   cpu: 93%/70%   2         6         4
```

Full output in
[`docs/evidence/06-hpa-scaling.txt`](docs/evidence/06-hpa-scaling.txt).

Scale down has a 120 second stabilisation window, otherwise the replica
count flaps every time traffic dips for a moment.

---

## Monitoring

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f monitoring/prometheus-values.yaml

kubectl create configmap washq-dashboard -n monitoring \
  --from-file=washq-dashboard.json=monitoring/dashboards/washq-dashboard.json
kubectl label configmap washq-dashboard -n monitoring grafana_dashboard=1
```

The backend exposes `/metrics` through
`prometheus-fastapi-instrumentator`, which gives request counts, latency
histograms and status codes for free. On top of that the app records four
of its own:

| Metric | Meaning |
|---|---|
| `washq_bookings_created_total` | Slots successfully booked |
| `washq_double_booking_rejected_total` | Booking attempts refused as clashes |
| `washq_bookings_cancelled_total` | Bookings cancelled |
| `washq_machines_busy` | Machines running a wash right now |
| `washq_machines_out_of_order` | Machines marked broken |

The dashboard is loaded automatically from a labelled ConfigMap, so there
is nothing to import by hand. It has eight panels: the four app counters
at the top, then request rate by endpoint, 95th percentile latency,
responses by status code, and backend pods up.

Prometheus finds the backend through the ServiceMonitor in the chart. The
kube-prometheus-stack chart only watches its own ServiceMonitors by
default, which is why `monitoring/prometheus-values.yaml` sets the
`serviceMonitorSelectorNilUsesHelmValues: false` overrides.

Getting at the UIs:

```bash
kubectl port-forward -n monitoring svc/monitoring-prometheus 9090:9090
kubectl port-forward -n monitoring svc/monitoring-grafana 3001:80
```

Grafana logs in with `admin` and the password in
`monitoring/prometheus-values.yaml`.

---

## GitOps with Argo CD

The cluster is not deployed to by hand. Argo CD watches this repo and
makes the cluster match it, so a deploy is a commit.

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

kubectl apply -f gitops/argocd-application.yaml
kubectl get application washq -n argocd
```

```
NAME    SYNC STATUS   HEALTH STATUS
washq   Synced        Healthy
```

Full output in [`docs/evidence/07-argocd.txt`](docs/evidence/07-argocd.txt)
and a screenshot of the tree view in
[`docs/screenshots/10-argocd-synced.png`](docs/screenshots/10-argocd-synced.png).

A deploy goes: push to `main`, the pipeline builds and scans and pushes
both images tagged with the commit SHA, then that SHA goes into
`gitops/argocd-application.yaml` and Argo rolls it out. More detail in
[`gitops/README.md`](gitops/README.md).

Two settings in the Application are doing real work:

**`selfHeal: true`** puts back anything changed directly on the cluster.
That is the point of GitOps, and it also means editing a live Deployment
to debug something will not stick.

**`ignoreDifferences`** on two paths. One is `/spec/replicas` on the
backend, which the HPA owns. Without it Argo reads the scaled replica
count as drift and resets it every few minutes, fighting the autoscaler.
The other is the Postgres `volumeClaimTemplates`, because Kubernetes
stamps `apiVersion`, `kind` and a `status` block onto them after
creation. None of that can be written in the chart, so without the rule
the StatefulSet sits OutOfSync forever with nothing actually wrong.

---

## Troubleshooting

Two manifests that break on purpose, with the commands that find the
cause, are in [`troubleshooting/`](troubleshooting). One is a bad image
tag, the other is a Service whose selector matches nothing. Both were
applied to a real cluster and the notes record the actual output,
including the fact that GHCR answers 403 rather than 404 for a tag that
does not exist.

---

## Layout

```
backend/            FastAPI app, tests, Alembic migrations
  app/              config, models, schemas, routers, metrics
  tests/            22 pytest tests
  alembic/          one migration
frontend/           React app, nginx config, multi-stage Dockerfile
  src/              components
k8s/                namespace and the kind cluster config
helm/washq/         the chart
terraform/          VPC, EKS, IAM
monitoring/         Prometheus values and the Grafana dashboard
gitops/             Argo CD application
troubleshooting/    two deliberately broken manifests
scripts/            load test for the HPA
docs/evidence/      real command output
docs/screenshots/   app, Prometheus and Grafana
demo/               presentation video and slides
```

---

## Known limits

Being straight about what this is not.

**Postgres is a single pod.** It has a volume so a restart keeps the
data, but there is no replication and no automated backup. For a hostel
noticeboard that is fine. For anything real it is not.

**The database password is in `values.yaml`** as a default so the chart
installs cleanly out of the box. A real deploy sets
`postgres.existingSecret` and points at a secret created separately. The
chart supports that already.

**No authentication.** Anyone who can reach the page can book as anyone
and mark any machine broken. A real version would sit behind the hostel
login. Adding it would not change any of the DevOps layers, which is why
it was left out.

**The clash check is in application code, not a database constraint.**
Two requests arriving in the same instant could in theory both pass the
check before either commits. Postgres can enforce this properly with an
exclusion constraint on a time range, and that is the right fix. The
index on `(machine_id, slot_start, slot_end)` is already there for it.

**No HTTPS.** The ingress serves plain HTTP. On a real cluster this would
be cert-manager and a real hostname.

**One environment.** There are dev and prod values files, but only one
cluster. No staging, and no promotion between environments.

**Migrations run at pod start, so a recreated database needs a pod
restart.** The init container migrates and seeds when the backend pod
starts. If Postgres is wiped while the backend pods keep running, those
pods carry on pointing at an empty database and every request fails with
`relation "machines" does not exist` until the Deployment is restarted. I
hit this while testing. In normal use it does not come up, because any
deploy creates new pods anyway, but a migration Job with a Helm hook
would be the more correct shape.

**StatefulSet volume claims cannot be changed in place.**
`volumeClaimTemplates` are immutable, so changing the storage class or
the size means deleting and recreating the StatefulSet. Argo CD cannot
roll that out on its own.
