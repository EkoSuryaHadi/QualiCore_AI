# QualiCore AI MVP v0.3.1 Deployment Baseline

## Recommended deployment: one Vercel project using Services

The repository is configured as two services behind one domain:
- `/` -> Next.js frontend
- `/api/*` -> FastAPI backend
- public API base -> `/api/v1`
- health -> `/api/health`

## 1. Provision PostgreSQL
Create a managed PostgreSQL database and obtain a SQLAlchemy-compatible connection string such as `postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require`.

## 2. Configure Vercel
1. Import this GitHub repository into Vercel.
2. In Project Settings -> Build & Deployment, select **Services** as Framework Preset.
3. Add variables from `.env.vercel.example`.
4. First deploy: `AUTO_BOOTSTRAP=true`.
5. `SEED_DEMO=true` only for private demo.
6. Deploy.
7. After tables exist, set `AUTO_BOOTSTRAP=false` and redeploy.

## 3. Verify
- `/` loads the login screen.
- `/api/health` returns status `ok`.
- `/api/v1/projects` returns `401` without a token.
- Login works at `/login`.
- Dashboard loads after login.

## Evidence note
Vercel function `/tmp` storage is temporary. Add object storage before relying on evidence persistence.
