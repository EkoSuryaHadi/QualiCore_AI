# Changelog

## 0.3.1 — Deployable baseline
- Added Vercel Services configuration for Next.js + FastAPI under one domain.
- Added Vercel Python entrypoint and `pyproject.toml`.
- Normalized backend internal routes to `/v1`; Vercel exposes them as `/api/v1`.
- Fixed broken `useProjectFilter` hook contract used by module pages.
- Added serverless-safe PostgreSQL connection handling.
- Added optional first-deploy database bootstrap.
- Added environment-specific upload directory handling.
- Refreshed Docker Compose for automatic local bootstrap and persistent uploads.
- Added production deployment runbook and Vercel environment template.
- Frozen feature expansion until deployment baseline is verified.
