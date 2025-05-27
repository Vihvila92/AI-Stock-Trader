import json
from datetime import datetime, timedelta
from typing import Optional

from db import engine
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt  # pip install python-jose
from models import User
from passlib.hash import bcrypt
from pydantic import BaseModel
from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# Utility: admin always has all permissions
ALL_PERMISSIONS = {
    "can_manage_users": True,
    "can_edit_settings": True,
    "can_reset_passwords": True,
    # Add possible future permissions here
}
# Permissions that only the original admin can have
ADMIN_ONLY_PERMISSIONS = set()

SECRET_KEY = "supersecretkey"  # nosec B105 - Change to .env in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    async with AsyncSession(engine) as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalars().one_or_none()
        if user is None:
            raise credentials_exception
        perms = {}
        if hasattr(user, "permissions") and isinstance(user.permissions, str):
            try:
                perms = (
                    json.loads(user.permissions)
                    if user.permissions not in (None, "", "null")
                    else {}
                )
            except Exception:
                perms = {}
        # Varmistetaan että adminilla on aina kaikki oikeudet
        if getattr(user, "username", None) == "admin":
            perms.update(
                {
                    "can_manage_users": True,
                    "can_edit_settings": True,
                    "can_reset_passwords": True,
                    "can_see_maintenance": True,
                }
            )
        return {"id": user.id, "username": user.username, "permissions": perms}


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(User).where(User.username == form_data.username)
        )
        user = result.scalars().one_or_none()
        input_password = form_data.password
        db_hash = getattr(user, "hashed_password", "") if user else None
        verify_result = False
        if user and db_hash:
            try:
                verify_result = bcrypt.verify(input_password, db_hash)
            except Exception as e:
                print(f"[DEBUG] bcrypt.verify exception: {e}")
        print(f"[DEBUG] Login attempt for user: {form_data.username}")
        print(f"[DEBUG] Password verification initiated for user: {form_data.username}")
        print(f"[DEBUG] DB hash: {db_hash}")
        print(f"[DEBUG] bcrypt.verify result: {verify_result}")
        if user is None or not verify_result:
            raise HTTPException(
                status_code=401, detail="Incorrect username or password"
            )
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}


async def require_permission(permission: str, user=Depends(get_current_user)):
    if not user["permissions"].get(permission):
        raise HTTPException(status_code=403, detail="No permission")
    return user


def is_admin_user(user_obj):
    return user_obj.username == "admin"


class UserCreate(BaseModel):
    username: str
    password: str
    permissions: dict = {}  # Permissions as JSON object


class UserOut(BaseModel):
    id: int
    username: str
    permissions: dict


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    permissions: Optional[dict] = None
    oldPassword: Optional[str] = None


@router.get("/users", response_model=list[UserOut])
async def get_users():
    async with AsyncSession(engine) as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        user_list = []
        for u in users:
            perms = {}
            if hasattr(u, "permissions") and isinstance(u.permissions, str):
                try:
                    perms = (
                        json.loads(u.permissions)
                        if u.permissions not in (None, "", "null")
                        else {}
                    )
                except Exception:
                    perms = {}
            # Ei enää admin-poikkeusta, vaan luotetaan kannan permissionsiin
            user_list.append({"id": u.id, "username": u.username, "permissions": perms})
        return user_list


@router.get("/users/me", response_model=UserOut)
async def get_me(user=Depends(get_current_user)):
    return user


@router.post("/users", response_model=UserOut)
async def create_user(user: UserCreate, request: Request):
    client_ip = getattr(getattr(request, "client", None), "host", "unknown")
    async with AsyncSession(engine) as session:
        # Estetään adminin luonti, jos käyttäjiä on jo olemassa
        result = await session.execute(select(User))
        all_users = result.scalars().all()
        if user.username == "admin":
            if len(all_users) > 0:
                print(
                    f"[AUDIT] {client_ip} tried to create admin when "
                    f"users already exist -> denied"
                )
                raise HTTPException(
                    status_code=403,
                    detail="Admin can only be created as the first user",
                )
            # Kirjoitetaan adminille aina kaikki oikeudet
            permissions = {
                "can_manage_users": True,
                "can_edit_settings": True,
                "can_reset_passwords": True,
                "can_see_maintenance": True,
            }
            user.permissions = permissions
        else:
            # Estetään muiden käyttäjien luonti, jos adminia ei ole olemassa
            admin_exists = any(u.username == "admin" for u in all_users)
            if not admin_exists:
                print(
                    f"[AUDIT] {client_ip} tried to create non-admin user "
                    f"before admin exists -> denied"
                )
                raise HTTPException(
                    status_code=403, detail="Admin must be created first"
                )
        # Check if admin already exists when trying to create admin
        if user.username == "admin":
            result = await session.execute(select(User).where(User.username == "admin"))
            existing_admin = result.scalars().one_or_none()
            if existing_admin is not None:
                print(
                    f"[AUDIT] {client_ip} tried to create a second admin "
                    f"account -> denied"
                )
                raise HTTPException(
                    status_code=403, detail="Admin account already exists"
                )
        # Prevent admin-only permissions for non-admins
        if user.username != "admin" and any(
            k in ADMIN_ONLY_PERMISSIONS and v
            for k, v in (user.permissions or {}).items()
        ):
            print(
                f"[AUDIT] {client_ip} tried to create user {user.username} "
                f"with admin-only permissions -> denied"
            )
            raise HTTPException(
                status_code=403,
                detail="You cannot create a user with admin-only permissions",
            )
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.username == user.username)
        )
        existing = result.scalars().one_or_none()
        if existing is not None:
            raise HTTPException(status_code=400, detail="User already exists")
        hashed_pw = bcrypt.hash(user.password)
        print(f"[DEBUG] Creating user {user.username}, hashed password: {hashed_pw}")
        permissions_str = json.dumps(user.permissions or {})
        new_user = User(
            username=user.username,
            hashed_password=hashed_pw,
            is_active=1,
            permissions=permissions_str,
        )
        session.add(new_user)
        await session.flush()
        user_id = new_user.id
        username = new_user.username
        await session.commit()
        print(f"[AUDIT] {client_ip} created user {username}")
    return {"id": user_id, "username": username, "permissions": user.permissions or {}}


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdate,
    request: Request,
    user=Depends(lambda: require_permission("can_manage_users")),
):
    async with AsyncSession(engine) as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        client_ip = getattr(getattr(request, "client", None), "host", "unknown")
        # Protect admin: admin's permissions CANNOT be changed, admin CANNOT be renamed
        if getattr(user, "username", None) == "admin":
            if data.username and data.username != "admin":
                print(f"[AUDIT] {client_ip} tried to change admin's username -> denied")
                raise HTTPException(
                    status_code=403, detail="You cannot change the admin username"
                )
            if data.permissions is not None:
                print(
                    f"[AUDIT] {client_ip} tried to change admin's permissions -> denied"
                )
                raise HTTPException(
                    status_code=403, detail="You cannot change admin permissions"
                )
            if data.password:
                setattr(user, "hashed_password", bcrypt.hash(data.password))
                print(f"[AUDIT] {client_ip} changed admin's password")
            await session.commit()
            return {
                "id": user.id,
                "username": user.username,
                "permissions": ALL_PERMISSIONS,
            }
        # Prevent admin-only permissions for non-admins
        if data.permissions:
            for k, v in data.permissions.items():
                if k in ADMIN_ONLY_PERMISSIONS and v is True:
                    print(
                        f"[AUDIT] {client_ip} tried to give admin-only "
                        f"permission ({k}) to user {user.username} -> denied"
                    )
                    raise HTTPException(
                        status_code=403,
                        detail="You cannot grant admin-only permissions",
                    )
        # Update other fields
        if data.username:
            if data.username == "admin":
                print(
                    f"[AUDIT] {client_ip} tried to rename user "
                    f"{user.username} to admin -> denied"
                )
                raise HTTPException(
                    status_code=403, detail="You cannot rename a user to admin"
                )
            setattr(user, "username", data.username)
        if data.password:
            setattr(user, "hashed_password", bcrypt.hash(data.password))
        if data.permissions is not None:
            setattr(user, "permissions", json.dumps(data.permissions))
        await session.commit()
        perms = data.permissions if data.permissions is not None else {}
        return {"id": user.id, "username": user.username, "permissions": perms}


@router.delete("/users/{user_id}")
async def delete_user(user_id: int):
    async with AsyncSession(engine) as session:
        result = await session.execute(select(User).order_by(asc(User.id)).limit(1))
        first_user = result.scalars().one_or_none()
        result2 = await session.execute(select(User).where(User.id == user_id))
        user = result2.scalars().one_or_none()
        # Ensure first_user.id is a real int, not a ColumnElement
        if (
            first_user is not None
            and hasattr(first_user, "id")
            and isinstance(first_user.id, int)
        ):
            if user_id == first_user.id:
                raise HTTPException(
                    status_code=403, detail="You cannot delete the first admin account."
                )
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        await session.delete(user)
        await session.commit()
    return {"status": "ok"}
