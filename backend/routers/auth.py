import os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from jose import jwt
from models.schemas import LoginRequest, LoginResponse

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
USE_SUPABASE = SUPABASE_URL and "placeholder" not in SUPABASE_URL
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")

# Local dev users (when Supabase is not configured)
LOCAL_USERS = {
    "admin@dwv.com.br": {"id": "local-admin-001", "senha": "dwv2025", "nome": "Admin DWV"},
    "operadora@dwv.com.br": {"id": "local-user-002", "senha": "dwv2025", "nome": "Operadora DWV"},
}


def _make_token(user_id: str, email: str) -> str:
    return jwt.encode(
        {"sub": user_id, "email": email, "exp": datetime.utcnow() + timedelta(days=7)},
        JWT_SECRET,
        algorithm="HS256",
    )


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    if USE_SUPABASE:
        try:
            from supabase import create_client
            supabase = create_client(SUPABASE_URL, os.getenv("SUPABASE_KEY", ""))
            res = supabase.auth.sign_in_with_password({
                "email": req.email,
                "password": req.senha,
            })
            user = res.user
            token = _make_token(user.id, user.email)
            return LoginResponse(
                user={"id": user.id, "email": user.email, "nome": user.email.split("@")[0]},
                token=token,
            )
        except Exception:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
    else:
        # Local auth
        local = LOCAL_USERS.get(req.email)
        if not local or local["senha"] != req.senha:
            raise HTTPException(status_code=401, detail="Credenciais inválidas. Use admin@dwv.com.br / dwv2025")
        token = _make_token(local["id"], req.email)
        return LoginResponse(
            user={"id": local["id"], "email": req.email, "nome": local["nome"]},
            token=token,
        )


@router.post("/logout")
async def logout():
    return {"ok": True}
