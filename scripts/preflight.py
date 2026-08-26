import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    "vercel.json",
    "frontend/package.json",
    "frontend/src/lib/api.ts",
    "backend/main.py",
    "backend/pyproject.toml",
    "backend/app/main.py",
    ".env.vercel.example",
    "docs/DEPLOYMENT.md",
]
missing = [p for p in required if not (ROOT / p).exists()]
if missing:
    raise SystemExit(f"Missing deployment files: {missing}")

cfg = json.loads((ROOT / "vercel.json").read_text())
services = cfg.get("experimentalServices", {})
assert services.get("frontend", {}).get("routePrefix") == "/"
assert services.get("backend", {}).get("routePrefix") == "/api"
assert services.get("backend", {}).get("entrypoint") == "backend/main.py"

api_source = (ROOT / "frontend/src/lib/api.ts").read_text()
assert "NEXT_PUBLIC_BACKEND_URL" in api_source
assert "/v1" in api_source

print("preflight: PASS")
