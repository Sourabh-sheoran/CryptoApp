import os
import time
import bcrypt
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from app.database import get_db

SECRET_KEY = os.environ.get("JWT_SECRET", "super_secret_crypto_ai_jwt_key_2026_secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 60 * 60 * 24 * 7 # 7 days

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)

# Pydantic models
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    virtual_balance_usd: float

class AuthResponse(BaseModel):
    token: str
    user: UserResponse
    message: str

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = int(time.time()) + ACCESS_TOKEN_EXPIRE_SECONDS
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is expired or invalid")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, virtual_balance_usd FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "virtual_balance_usd": float(row["virtual_balance_usd"])
        }

def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if not credentials:
        return None
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None

@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest):
    name = req.name.strip()
    email = req.email.strip().lower()
    password = req.password

    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Name must be at least 2 characters long")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="An account with this email already exists")

        pwd_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, virtual_balance_usd) VALUES (?, ?, ?, 50000.0)",
            (name, email, pwd_hash)
        )
        user_id = cursor.lastrowid
        conn.commit()

        token = create_access_token({"sub": str(user_id), "email": email, "name": name})
        user_obj = UserResponse(id=user_id, name=name, email=email, virtual_balance_usd=50000.0)
        return AuthResponse(token=token, user=user_obj, message="Registration successful! $50,000 virtual balance credited.")

@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    email = req.email.strip().lower()
    password = req.password

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, password_hash, virtual_balance_usd FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row or not verify_password(password, row["password_hash"]):
            raise HTTPException(status_code=400, detail="Invalid email or password")

        user_id = row["id"]
        name = row["name"]
        balance = float(row["virtual_balance_usd"])

        token = create_access_token({"sub": str(user_id), "email": email, "name": name})
        user_obj = UserResponse(id=user_id, name=name, email=email, virtual_balance_usd=balance)
        return AuthResponse(token=token, user=user_obj, message="Welcome back, " + name + "!")

@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
        virtual_balance_usd=current_user["virtual_balance_usd"]
    )

@router.post("/reset-balance")
def reset_balance(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET virtual_balance_usd = 50000.0 WHERE id = ?", (current_user["id"],))
        cursor.execute("DELETE FROM portfolios WHERE user_id = ?", (current_user["id"],))
        cursor.execute("DELETE FROM transactions WHERE user_id = ?", (current_user["id"],))
        conn.commit()
    return {"message": "Portfolio and virtual balance reset to $50,000.00 USD successfully"}
