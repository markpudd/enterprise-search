from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import json

from models.user import User, UserRole
from config import settings

security = HTTPBearer()

# Mock user data - in production, this would come from a database
MOCK_USERS = {
    "john.smith@testbank.com": {
        "id": "1",
        "name": "John Smith",
        "email": "john.smith@testbank.com",
        "department": "IT Leadership",
        "position": "CTO",
        "role": "executive",
        "company": "Test Bank"
    },
    "sarah.johnson@testbank.com": {
        "id": "2", 
        "name": "Sarah Johnson",
        "email": "sarah.johnson@testbank.com",
        "department": "Risk Management", 
        "position": "Risk Manager",
        "role": "manager",
        "company": "Test Bank"
    },
    "mike.chen@testbank.com": {
        "id": "3",
        "name": "Mike Chen", 
        "email": "mike.chen@testbank.com",
        "department": "Software Engineering",
        "position": "Senior Developer",
        "role": "employee",
        "company": "Test Bank"
    },
    "lisa.davis@testbank.com": {
        "id": "4",
        "name": "Lisa Davis",
        "email": "lisa.davis@testbank.com", 
        "department": "Business Analysis",
        "position": "Senior Business Analyst",
        "role": "employee",
        "company": "Test Bank"
    },
    "admin@testbank.com": {
        "id": "5",
        "name": "System Admin",
        "email": "admin@testbank.com",
        "department": "IT Administration", 
        "position": "System Administrator",
        "role": "admin",
        "company": "Test Bank"
    }
}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.API_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.API_SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from JWT token"""
    try:
        payload = verify_token(credentials.credentials)
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from mock data (in production, query database)
    user_data = MOCK_USERS.get(email)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return User(**user_data)


async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[User]:
    """Get current user if token provided, otherwise return None"""
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_role(required_roles: list[UserRole]):
    """Decorator to require specific roles"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


# Role-based dependencies
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def require_manager_or_above(current_user: User = Depends(get_current_user)) -> User:
    """Require manager role or higher"""
    allowed_roles = [UserRole.ADMIN, UserRole.EXECUTIVE, UserRole.MANAGER]
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access or higher required"
        )
    return current_user