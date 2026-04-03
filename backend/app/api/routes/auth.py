from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.api.dependencies import get_user_by_username, verify_password, create_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    display_name: str


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    user = await get_user_by_username(req.username)
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已禁用")

    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return LoginResponse(
        access_token=token,
        role=user["role"],
        display_name=user.get("display_name", user["username"])
    )
