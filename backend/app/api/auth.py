from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.deps import get_db
from app.core.security import verify_password, create_access_token
from app.db.models import User

router = APIRouter(tags=["auth"])  # ❌ removed prefix="/auth"

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    id: int
    username: str
    role: str
    token: str
    token_type: str = "bearer"

@router.post("/login", response_model=LoginResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.username, "role": user.role})

    return {
        "id": user.user_id,
        "username": user.username,
        "role": user.role,
        "token": token,
    }

@router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}
