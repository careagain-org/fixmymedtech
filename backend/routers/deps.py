# deps.py — shared dependencies

from fastapi import HTTPException, Header
from supabase import Client

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_API_ANON_KEY")


def get_supabase(request) -> Client:
    return request.app.state.supabase


async def get_current_user(authorization: str = Header(...)):
    """
    Validates the Supabase JWT passed as Bearer token.
    Returns the user payload from Supabase.
    """
    from supabase import create_client
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ")[1]

    # Use anon client to verify user token
    client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    try:
        user = client.auth.get_user(token)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user.user
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate token")