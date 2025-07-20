# Hybrid Infra Orchestrator

A **FastAPI + Temporal + PostgreSQL** platform that provisions hybrid infrastructure resources using a flexible **GitOps _and_ API-based** model.

![architecture](docs/architecture.svg)

---

## 🚀 Quick-Start (Local)

```bash
# 1. Clone & install deps (Python 3.11)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Run Postgres & Temporal via docker-compose
docker compose -f dev/compose.yml up -d

# 3. Create DB schema
alembic upgrade head  # migrations TBD

# 4. Start Temporal worker (in a new shell)
python gitops_orchestrator/temporal_worker.py

# 5. Launch FastAPI server
uvicorn gitops_orchestrator.main:app --reload
```

Open http://localhost:8000/docs for interactive Swagger UI.

---

## 🏢 Production Deployment

1. **Container build**
   ```bash
   docker build -t hybrid-orchestrator:latest .
   ```
2. **Database migrations** – run once (e.g., in an init job):
   ```bash
   docker run --env-file .env hybrid-orchestrator:latest alembic upgrade head
   ```
3. **Application containers**
   * **API:**
     ```bash
     docker run -d --env-file .env \
       -p 8000:8000 \
       --name orchestrator-api \
       hybrid-orchestrator:latest \
       uvicorn gitops_orchestrator.main:app --host 0.0.0.0 --port 8000 --workers 4
     ```
   * **Temporal worker:**
     ```bash
     docker run -d --env-file .env \
       --name orchestrator-worker \
       hybrid-orchestrator:latest \
       python gitops_orchestrator/temporal_worker.py
     ```
4. **Environment variables** – mount a secret `.env` or use a secret manager to inject:
   * `DB_*` – production Postgres
   * `TEMPORAL_*` – Temporal Cloud or self-hosted endpoint
   * `GIT_PAT`, `GIT_USERNAME` – Git credentials
   * `RESOURCE_REPO_MAP_JSON`, `RESOURCE_MERGE_STRATEGY_MAP_JSON`
5. **Ingress & TLS** – front the API container with NGINX/Traefik; enable HTTPS.
6. **Observability** – scrape `/metrics` endpoints, export logs to your stack.
7. **Scaling** – stateless API and worker containers; scale horizontally as needed.


---

## 🧠 Design Highlights

| Pillar | Details |
|--------|---------|
| **Hybrid provisioning** | Combine GitOps (Jinja → Git commit/PR) _and_ direct vendor API calls. |
| **Modular handlers** | Each resource category has its own class in `gitops_orchestrator/jobs/`, inheriting a common `BaseJobHandler`. |
| **Temporal workflows** | `JobWorkflow` coordinates activities: pre-checks → git/api → wait → post-actions. Durable, retryable, observable. |
| **PostgreSQL truth-source** | Jobs, resources, history recorded once; API reads never talk to Git or external systems. |
| **Per-resource Git repos & merge strategy** | Configure repo URL _and_ `direct` vs `pr` merge behaviour per resource type via env vars. |
| **Extensible** | Add a new resource by: 1) adding enum value, 2) creating handler class, 3) mapping in `dispatcher.py`, 4) optional Jinja template. |

---

## 🔧 Configuration

All settings are env-driven (`.env` supported). Key variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DB_HOST/PORT/NAME/USER/PASSWORD` | localhost / 5432 / gitops_orchestrator / postgres / postgres | Postgres connection |
| `TEMPORAL_HOST/PORT/NAMESPACE/TASK_QUEUE` | localhost / 7233 / default / gitops-jobs | Temporal |
| `GIT_PAT` / `GIT_USERNAME` |  | GitHub auth if required |
| `RESOURCE_REPO_MAP_JSON` |  | JSON mapping resource-group → repo URL |
| `RESOURCE_MERGE_STRATEGY_MAP_JSON` |  | JSON mapping resource-group → `"direct"` or `"pr"` |

---

## 🗺️ API Cheatsheet (v1)

```
POST /api/v1/tenants                       create tenant
GET  /api/v1/tenants                       list tenants

POST /api/v1/tenants/{tid}/resources/{category}   create resource (starts job)
GET  /api/v1/tenants/{tid}/resources/{category}   list resources
GET  /api/v1/tenants/{tid}/resources/{category}/{rid}  get resource

GET  /api/v1/tenants/{tid}/jobs           list jobs
GET  /api/v1/tenants/{tid}/jobs/{jid}     job status
POST /api/v1/tenants/{tid}/jobs/{jid}/retry   retry failed job

POST /api/v1/tenants/{tid}/callbacks/{jid}    webhook update

GET /api/v1/tenants/{tid}/metrics              job metrics
GET /api/v1/tenants/{tid}/resources/summary    resource counts
```

Try the interactive docs at `/docs` once the server is running.

---

## 🏗️ Add a New Resource Type

1. Add enum value in `models.py::ResourceCategory` (e.g., `storage/object`)
2. Create handler under `jobs/<group>/<name>.py` implementing required methods.
3. Register mapping in `dispatcher.py`.
4. Provide Jinja template in `gitops/templates/` if GitOps-managed.
5. Add repo URL & merge strategy in env vars if GitOps.
6. Profit 🚀

---

## 🤝 Contributing

Pull requests welcome! Please adhere to the coding standards:

* Use **async** SQLAlchemy.
* Keep **handlers stateless**; persist via DB or Temporal only.
* Write unit tests (`pytest`) and, where possible, Temporal workflow tests.
* Run `ruff` & `black` before pushing.

---

## License

Apache-2.0 © 2025 Windsurf Engineering
