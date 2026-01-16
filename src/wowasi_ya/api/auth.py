"""Authentication utilities for the API."""

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from wowasi_ya.config import Settings, get_settings

# Security setup
security = HTTPBasic(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


class Token(BaseModel):
    """JWT token response model."""

    access_token: str
    token_type: str = "bearer"


class User(BaseModel):
    """User model."""

    username: str
    is_admin: bool = False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, settings: Settings) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm=ALGORITHM,
    )


def authenticate_user(
    credentials: HTTPBasicCredentials,
    settings: Settings,
) -> User | None:
    """Authenticate a user with username/password."""
    # For now, only support the admin user from config
    if credentials.username != settings.admin_username:
        return None

    # In production, this would check against a database
    # For MVP, we compare against the config password directly
    if credentials.password != settings.admin_password.get_secret_value():
        return None

    return User(username=credentials.username, is_admin=True)


def verify_api_key(api_key: str, settings: Settings) -> User | None:
    """Verify an API key."""
    if settings.api_key is None:
        return None
    if api_key == settings.api_key.get_secret_value():
        return User(username="api_user", is_admin=False)
    return None


async def get_current_user(
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
    api_key: Annotated[str | None, Depends(api_key_header)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """Get the current authenticated user.

    Supports both HTTP Basic auth and API key (X-API-Key header).

    Args:
        credentials: HTTP Basic credentials (optional).
        api_key: API key from X-API-Key header (optional).
        settings: Application settings.

    Returns:
        Authenticated user.

    Raises:
        HTTPException: If authentication fails.
    """
    # Try API key first (preferred for portal/external access)
    if api_key:
        user = verify_api_key(api_key, settings)
        if user:
            return user

    # Try HTTP Basic auth
    if credentials:
        user = authenticate_user(credentials, settings)
        if user:
            return user

    # Neither worked
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Basic"},
    )


# Dependency for requiring authentication
RequireAuth = Annotated[User, Depends(get_current_user)]
