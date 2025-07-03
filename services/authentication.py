# THIS SERVICE HANDLES USER AUTHENTICATION AND TOKEN MANAGEMENT
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from pydantic_settings import BaseSettings 

import os

# SETTINGS CLASS FOR AUTH CONFIGURATION
class Settings(BaseSettings):
    secret_key: str = "default-secret-key" 
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"
        extra = "allow" 

# INITIALIZE SETTINGS AND PASSWORD CONTEXT
settings = Settings()
pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")

# HASH A USER PASSWORD
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# VERIFY A USER PASSWORD
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# CREATE A JWT ACCESS TOKEN
def create_access_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

# DECODE A JWT ACCESS TOKEN
def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.PyJWTError:
        return None