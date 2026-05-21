"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from alaba.api import admin_users, auth, devices, health
from alaba.config import get_settings


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
    return app


app = create_app()
