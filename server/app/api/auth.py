"""
Authentication API endpoints.
Credentials loaded from environment variables.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt
from app.config.settings import DEMO_USERNAME, DEMO_PASSWORD, DEMO_DISPLAY_NAME, JWT_SECRET_KEY

router = APIRouter()

# JWT Configuration
SECRET_KEY = JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Demo credentials from environment variables
DEMO_USERS = {
    DEMO_USERNAME: {
        "password": DEMO_PASSWORD,
        "display_name": DEMO_DISPLAY_NAME,
    },
}


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    display_name: str


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    user = DEMO_USERS.get(request.username)
    if not user or user["password"] != request.password:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    token = create_access_token(
        data={
            "sub": request.username,
        }
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        username=request.username,
        display_name=user["display_name"],
    )
