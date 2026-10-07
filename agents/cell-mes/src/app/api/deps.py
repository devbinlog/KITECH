"""API dependencies for authentication and database access."""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import decode_access_token
from ..core.config import settings
from ..db.session import get_db
from ..models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


class ServiceUser:
    """Pseudo-user for internal service authentication."""

    def __init__(self):
        self.id = 0
        self.username = "internal-service"
        self.role = "SERVICE"
        self.is_active = True


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[Optional[str], Depends(oauth2_scheme)] = None,
    x_internal_service_key: Annotated[Optional[str], Header(alias="X-Internal-Service-Key")] = None,
) -> User:
    """
    Get the current authenticated user from JWT token or internal service key.

    Internal services (like NL-Router) can use X-Internal-Service-Key header
    to bypass normal user authentication.
    """
    # Check for internal service key first
    if x_internal_service_key:
        if x_internal_service_key == settings.INTERNAL_SERVICE_KEY:
            return ServiceUser()
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid internal service key",
            )

    # Normal JWT authentication
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require admin role for the current user."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


# Type aliases for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]
DBSession = Annotated[AsyncSession, Depends(get_db)]


# ============================================================================
# Event Publisher Dependency
# ============================================================================

from ..services.event_publisher import get_event_publisher, EventPublisher


def get_event_publisher_dep() -> EventPublisher:
    """Get EventPublisher instance."""
    return get_event_publisher()


EventPublisherDep = Annotated[EventPublisher, Depends(get_event_publisher_dep)]
