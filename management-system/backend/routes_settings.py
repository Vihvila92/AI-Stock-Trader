import json
from typing import Any, List, Optional

from db import engine
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from models import Setting
from pydantic import BaseModel
from routes_users import get_current_user
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class SettingOut(BaseModel):
    key: str
    value: str
    label: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None
    enum: Optional[Any] = None


class SettingUpdate(BaseModel):
    value: str


async def get_optional_user(request: Request):
    auth = request.headers.get("authorization")
    if not auth:
        return None
    try:
        return await get_current_user(token=auth.split(" ")[1])
    except Exception:
        return None


@router.get("/settings", response_model=List[SettingOut])
async def get_settings(
    category: Optional[str] = Query(None), user=Depends(get_optional_user)
):
    # If appearance category is requested, no authentication required
    if category == "appearance":
        async with AsyncSession(engine) as session:
            result = await session.execute(select(Setting))
            settings = result.scalars().all()
            out = []
            for s in settings:
                value_str = s.value if isinstance(s.value, str) else str(s.value)
                label = None
                labels_value = getattr(s, "labels", None)
                if labels_value and isinstance(labels_value, str):
                    try:
                        labels_dict = json.loads(labels_value)
                        label = labels_dict.get("en") or labels_dict.get("fi")
                    except Exception:
                        label = None
                out.append(
                    {
                        "key": str(s.key),
                        "value": value_str,
                        "label": label,
                        "category": s.category,
                        "type": s.type,
                        "enum": s.enum,
                    }
                )
            return out
    # Muut kategoriat vaativat autentikoinnin
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    async with AsyncSession(engine) as session:
        result = await session.execute(select(Setting))
        settings = result.scalars().all()
        out = []
        for s in settings:
            value_str = s.value if isinstance(s.value, str) else str(s.value)
            label = None
            labels_value = getattr(s, "labels", None)
            if labels_value and isinstance(labels_value, str):
                try:
                    labels_dict = json.loads(labels_value)
                    label = labels_dict.get("en") or labels_dict.get("fi")
                except Exception:
                    label = None
            out.append(
                {
                    "key": str(s.key),
                    "value": value_str,
                    "label": label,
                    "category": s.category,
                    "type": s.type,
                    "enum": s.enum,
                }
            )
        return out


@router.put("/settings/{key}")
async def update_setting(key: str, data: SettingUpdate, user=Depends(get_current_user)):
    # Only users with permission can edit settings
    if not user["permissions"].get("can_edit_settings"):
        raise HTTPException(status_code=403, detail="No permission to edit settings")
    async with AsyncSession(engine) as session:
        result = await session.execute(select(Setting).where(Setting.key == key))
        setting = result.scalars().one_or_none()
        if not setting:
            raise HTTPException(status_code=404, detail="Setting not found")
        # Update only value column, don't touch other fields
        setattr(setting, "value", str(data.value))
        await session.commit()
        return {"status": "ok"}
