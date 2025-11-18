# ===================================================
# Autor: Moisés Silva de Azevedo
#
# Universidade Federal do Mato Grosso do Sul,
# Câmpus de Três Lagoas (UFMS/CPTL),
# Sistemas de Informaçao,
# Computaçao Distribuída,
# Novembro de 2025
# ===================================================

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

# Configuration
SECRET_KEY = "your-super-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Admin user credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def authenticate_user(username: str, password: str) -> bool:
    if username != ADMIN_USERNAME:
        return False

    return password == ADMIN_PASSWORD


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    if username != ADMIN_USERNAME:
        raise credentials_exception

    return username


def get_current_user(username: str = Depends(verify_token)) -> str:
    return username
