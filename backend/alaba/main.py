"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from alaba.api import admin_users, auth, devices, health, me
from alaba.config import get_settings

# Ensure dev loggers (notably alaba.otp.mock) propagate to uvicorn's stdout
# so `docker logs alaba-backend-api` shows OTP codes in dev. Uvicorn's default
# config doesn't configure non-uvicorn loggers; this fills the gap.
logging.getLogger("alaba").setLevel(logging.INFO)
if not logging.getLogger("alaba").handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    logging.getLogger("alaba").addHandler(_h)


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title="Alaba API",
        version="0.1.0",
        description="Backend for the Alaba Nollywood distribution platform.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(devices.router)
    app.include_router(admin_users.router)
    app.include_router(me.router)
    return app


app = create_app()
