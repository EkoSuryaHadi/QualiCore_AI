# QualiCore AI MVP — Deployable Baseline v0.3.1

QualiCore AI is an EPC Project Assurance MVP. This release intentionally freezes feature expansion and establishes a deployable baseline before each module is developed further.

## Current modules
- Authentication + RBAC
- Projects + Project Assurance Workspace
- Inspections
- NCR workflow
- Punchlist
- Document Control
- Risk Register + Heatmap
- Executive Reports
- Audit Trail + Notifications

## Production-shaped stack
- Next.js 16 / React 19
- FastAPI / Python 3.12
- PostgreSQL
- SQLAlchemy + Alembic
- Vercel Services for one-domain frontend + backend deployment
- Docker Compose for local integration testing

## Local Docker
```bash
cp .env.example .env
docker compose up --build
```

Frontend: http://localhost:3000  
Backend: http://localhost:8000  
Swagger: http://localhost:8000/docs

The Docker baseline creates and seeds the local database automatically. Demo login:

- `admin@qualicore.ai`
- `Admin123!`

## Vercel
See `docs/DEPLOYMENT.md` and `.env.vercel.example`.

External routes on Vercel:
- Frontend: `/`
- API health: `/api/health`
- API v1: `/api/v1/*`

## Important MVP boundary
Evidence upload uses persistent Docker storage locally, but Vercel uses temporary function storage. Connect object storage before treating uploaded evidence as production data.

## SDLC rule from this release onward
v0.3.1 is the deployment baseline. New work should be isolated by module and released incrementally rather than expanding the platform horizontally in one sprint.
