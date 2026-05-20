"""Health-check endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from alaba.db import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    db_status = "ok"
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() != 1:
            db_status = "unexpected_response"
    except Exception as e:  # pragma: no cover
        db_status = f"error: {type(e).__name__}"
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "service": "alaba-backend",
        "checks": {"database": db_status},
    }
