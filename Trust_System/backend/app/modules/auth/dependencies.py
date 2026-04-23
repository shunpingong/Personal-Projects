from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from jose import JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.core.security import decode_token, oauth2_scheme
from app.db.models.user import User
from app.db.session import get_db_session
from app.schemas.auth import TokenPayload
from app.services import user_service


DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    if token is None:
        raise _credentials_exception()

    try:
        payload = TokenPayload.model_validate(
            decode_token(token, expected_type="access")
        )
    except (JWTError, ValidationError) as exc:
        raise _credentials_exception() from exc

    user = await user_service.get_user_by_id(db, payload.sub)
    if user is None:
        raise _credentials_exception()
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


def require_roles(*allowed_roles: UserRole):
    async def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user

    return dependency
