import logging
import os

from db import engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes_settings import router as settings_router
from routes_users import router as users_router
from sqlalchemy import text

logging.basicConfig(level=logging.ERROR)
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/management"
)

app = FastAPI()

# Allow only the frontend origin (e.g. http://localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router, prefix="/api")
app.include_router(settings_router, prefix="/api")


@app.get("/api/health")
async def health():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception:
        import logging

        logging.error("Database health check failed", exc_info=True)
        return {"status": "error", "db": "unavailable"}
