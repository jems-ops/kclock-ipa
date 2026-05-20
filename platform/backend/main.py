from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.base import Base, engine
import models  # ensure all models are registered before create_all
from routers import apps, onboarding, diagnose, compliance, audit
from routers import federation

Base.metadata.create_all(bind=engine)

# Auto-seed default apps on first run
from seed import APPS
from models import App
from db.base import SessionLocal as _SL
_db = _SL()
for _a in APPS:
    if not _db.get(App, _a["id"]):
        _db.add(App(**_a))
_db.commit(); _db.close()

app = FastAPI(
    title="Keycloak-IPA Integration Platform API",
    description="Identity orchestration, SAML onboarding, AI diagnostics, and compliance automation.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(apps.router)
app.include_router(onboarding.router)
app.include_router(diagnose.router)
app.include_router(compliance.router)
app.include_router(audit.router)
app.include_router(federation.router)

@app.get("/health")
def health():
    return {"status": "ok"}
