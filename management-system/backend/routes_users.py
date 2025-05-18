from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import User
from db import engine
from pydantic import BaseModel
from passlib.hash import bcrypt

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    password: str

@router.get("/users")
async def get_users():
    async with AsyncSession(engine) as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        return [{"id": u.id, "username": u.username} for u in users]

@router.post("/users")
async def create_user(user: UserCreate):
    async with AsyncSession(engine) as session:
        # Tarkista onko admin jo olemassa
        result = await session.execute(select(User).where(User.username == user.username))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")
        hashed_pw = bcrypt.hash(user.password)
        new_user = User(username=user.username, hashed_password=hashed_pw, is_active=1)
        session.add(new_user)
        await session.commit()
        return {"id": new_user.id, "username": new_user.username}
