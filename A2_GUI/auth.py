# auth.py

import os
import bcrypt
import jwt
import datetime
from typing import Generator, Optional

from sqlalchemy.orm import Session
from db import SessionLocal, User
from config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MIN

# -----------------------------------------------------------------------------
# Database Session Helper
# -----------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session, ensuring it is closed after use.
    Usage:
        db = next(get_db())
        # ... use db ...
        db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------------------------------------------------------
# Password Hashing / Verification
# -----------------------------------------------------------------------------
def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    Returns the hashed password as a UTF-8 string.
    """
    hashed = bcrypt.hashpw(
        plain_password.encode("utf-8"),
        bcrypt.gensalt()
    )
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check a plaintext password against its bcrypt hash.
    Returns True if they match, False otherwise.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


# -----------------------------------------------------------------------------
# JWT Token Creation / Validation
# -----------------------------------------------------------------------------
def create_access_token(subject: str) -> str:
    """
    Create a JWT token with 'sub' = subject (e.g. username) and an expiry.
    """
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)
    payload = {
        "sub": subject,
        "exp": expire
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: str) -> Optional[str]:
    """
    Decode and verify a JWT. Returns the 'sub' (username) if valid, else None.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


# -----------------------------------------------------------------------------
# User Lookup
# -----------------------------------------------------------------------------
def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Retrieve a User object by username. Returns None if not found.
    """
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Retrieve a User object by email. Returns None if not found.
    """
    return db.query(User).filter(User.email == email).first()