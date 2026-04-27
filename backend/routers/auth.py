# routers/auth.py

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from typing import Optional
from routers.deps import get_supabase
from config.supabase_config import supa_client as sb
import uuid
router = APIRouter()

import os

FRONTEND_URL = os.getenv("FRONTEND_URL")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization_id: Optional[str] = None
    role: str = "clinical_staff"


@router.get("/organizations")
async def list_organizations(request: Request):
    """Public endpoint — needed for signup form dropdown."""
    sb = get_supabase(request)
    from config.supabase_config import supa_client as sb
    result = sb.table("organizations").select("*").order("name").execute()
    return result.data


@router.post("/login")
async def login(body: LoginRequest, request: Request):
    sb = get_supabase(request)
    try:
        res = sb.auth.sign_in_with_password({"email": body.email, "password": body.password})
        print(res)
        return {
            "access_token": res.session.access_token,
            "user": {
                "id": res.user.id,
                "email": res.user.email,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/signup")
async def signup(body: SignupRequest, request: Request):
    print("entra")
    print(body)
    print(request)
    sb = get_supabase(request)
    try:
        res = sb.auth.sign_up({"email": body.email, "password": body.password,
                "options": {
                        "email_redirect_to": f"{FRONTEND_URL}/login"
                    }
        })
        user_id = res.user.id

        # Create profile
        profile = {
            "id": user_id,
            "full_name": body.full_name,
            "organization_id": body.organization_id,
            "role": body.role,
        }
 
        sb.table("profiles").insert(profile).execute()

        return {"message": "Account created. Check your email to confirm."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/logout")
async def logout(request: Request):
    sb = get_supabase(request)
    sb.auth.sign_out()
    return {"message": "Logged out"}