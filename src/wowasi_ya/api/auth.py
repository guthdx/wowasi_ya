"""Authentication utilities for the API."""

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from wowasi_ya.config import Settings, get_settings

# Security setup
security = HTTPBasic()
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


async def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """Get the current authenticated user.

    Args:
        credentials: HTTP Basic credentials.
        settings: Application settings.

    Returns:
        Authenticated user.

    Raises:
        HTTPException: If authentication fails.
    """
    user = authenticate_user(credentials, settings)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user


# Dependency for requiring authentication
RequireAuth = Annotated[User, Depends(get_current_user)]
