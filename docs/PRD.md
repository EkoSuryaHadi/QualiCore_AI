# QualiCore AI — Product Requirements Document (MVP v0.1)

**Status:** Development Baseline  
**Date:** 26 August 2026  
**Vision:** AI-ready Project Assurance Platform for EPC Projects  
**Tagline:** Assure Before Failure

## Product objective
Deliver a usable EPC Project Assurance MVP focused on authentication/RBAC, projects, inspections, NCR, punchlist and an assurance dashboard.

## In scope
- Authentication and RBAC: ADMIN, QA_MANAGER, QA_ENGINEER, VIEWER
- Admin user management
- Project register
- Inspection register
- NCR lifecycle including root cause, corrective action and closure gate
- Punchlist lifecycle
- Executive assurance dashboard and MVP PAI-like score
- OpenAPI, health endpoint, Alembic migrations, seed/demo data, Docker packaging
- Next.js frontend

## Current deployable baseline
v0.3.1 freezes horizontal feature expansion and establishes GitHub + Vercel deployment foundations before each module is developed further.

## Acceptance criteria
- Valid user can login; invalid credentials are rejected.
- VIEWER cannot mutate business data.
- Authorized user can create/retrieve a project.
- Authorized user can create/list inspections.
- Authorized user can create/update NCR.
- NCR cannot close before required RCA/corrective action is complete.
- Punch items can be created and closed.
- Dashboard reflects persisted quality exposure.
- `/health` responds successfully.

## Non-functional requirements
- PostgreSQL production target.
- UTC timestamps.
- PBKDF2 password hashing.
- Signed expiring access tokens.
- Environment-based secrets.
- Alembic migrations.
- Automated critical API tests.
- Frontend production build and deployment verification are release gates.

## Module roadmap
1. Project Management
2. Inspection / ITP
3. NCR Management
4. Punchlist
5. Document Control
6. Risk Management
7. Vendor Quality
8. Dashboard & KPI
9. Reporting
10. AI Assurance
11. QualiCore Copilot
