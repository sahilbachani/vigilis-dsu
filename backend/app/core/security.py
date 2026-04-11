import bcrypt
from jose import jwt
from datetime import datetime, timedelta
from app.core.config import settings

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt directly.
    Bcrypt has a 72-byte limit, so we truncate if necessary.
    """
    # Truncate password to 72 bytes (bcrypt's maximum)
    truncated = password[:72] if len(password) > 72 else password
    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(truncated.encode('utf-8'), salt)
    # Return as string for database storage
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify password against bcrypt hash.
    """
    try:
        # Truncate password to 72 bytes (same as hashing)
        truncated = password[:72] if len(password) > 72 else password
        # Ensure hashed is bytes
        if isinstance(hashed, str):
            hashed = hashed.encode('utf-8')
        return bcrypt.checkpw(truncated.encode('utf-8'), hashed)
    except Exception as e:
        print(f"Warning: Password verification issue: {e}")
        return False

def create_access_token(data: dict, expires_minutes: int = 60):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
    return token
