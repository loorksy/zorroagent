from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Operator
from app.db.session import get_db
from app.security import decode_token

bearer = HTTPBearer(auto_error=False)


async def current_operator(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Operator:
    if creds is None:
        raise HTTPException(401, "Not authenticated")
    sub = decode_token(creds.credentials)
    if not sub:
        raise HTTPException(401, "Invalid token")
    row = await db.scalar(select(Operator).where(Operator.id == sub))
    if not row:
        raise HTTPException(401, "Unknown operator")
    return row
