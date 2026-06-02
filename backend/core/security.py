import hashlib
import secrets
import warnings
from datetime import timedelta

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from backend.core.config import settings
from backend.core.time import utc_now

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Salt size for password hashing
SALT_SIZE = 16
HASH_ITERATIONS = 100000


def _hash_password(password: str) -> tuple[str, str]:
    """Hash a password using PBKDF2-HMAC-SHA256."""
    salt = secrets.token_hex(SALT_SIZE)
    password_bytes = password.encode('utf-8')
    hash_obj = hashlib.pbkdf2_hmac('sha256', password_bytes, salt.encode('utf-8'), HASH_ITERATIONS)
    hash_hex = hash_obj.hex()
    return salt, hash_hex


def _verify_password(plain_password: str, salt: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    password_bytes = plain_password.encode('utf-8')
    hash_obj = hashlib.pbkdf2_hmac('sha256', password_bytes, salt.encode('utf-8'), HASH_ITERATIONS)
    return secrets.compare_digest(hash_obj.hex(), hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password and return salt$hash format."""
    salt, hash_hex = _hash_password(password)
    return f"{salt}${hash_hex}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    if '$' not in hashed_password:
        return False
    try:
        salt, stored_hash = hashed_password.split('$', 1)
        return _verify_password(plain_password, salt, stored_hash)
    except ValueError:
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = utc_now() + expires_delta
    else:
        expire = utc_now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = utc_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"datetime\.datetime\.utcnow\(\) is deprecated.*",
                category=DeprecationWarning,
                module=r"jose\.jwt",
            )
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
