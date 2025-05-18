from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes_users import router as users_router
from sqlalchemy.ext.asyncio import create_async_engine
import os
from models import Base, Setting
from sqlalchemy import text
from db import engine

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/management")

app = FastAPI()

# Salli vain frontendin osoite (esim. http://localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router, prefix="/api")

@app.get("/api/health")
async def health():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        return {"status": "error", "db": str(e)}
