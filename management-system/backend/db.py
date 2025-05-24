# db.py
from sqlalchemy.ext.asyncio import create_async_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/management")
engine = create_async_engine(DATABASE_URL, echo=True, future=True)
