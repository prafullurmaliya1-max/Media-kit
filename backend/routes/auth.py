from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import os
import re
from database import get_db
from models import User

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Scopes we request — read-only YouTube access + basic profile
SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def slugify(name: str) -> str:
    """Convert 'Aryan Kapoor' → 'aryankapoor' for the public URL"""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "", slug)
    return slug


@router.get("/google")
async def google_login():
    """
    Step 1 of OAuth — redirect the creator to Google's login page.
    Frontend calls this when the creator clicks 'Connect YouTube'.
    """
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": f"{BACKEND_URL}/auth/callback",
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",   # 'offline' gives us a refresh token
        "prompt": "consent",        # Always show consent screen so we get refresh token
    }
    # Build the Google auth URL with all params
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{query}")


@router.get("/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    """
    Step 2 of OAuth — Google redirects back here with a 'code'.
    We exchange that code for real access + refresh tokens.
    Then we save the creator to our DB and redirect them to their dashboard.
    """
    # Exchange the auth code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": f"{BACKEND_URL}/auth/callback",
            "grant_type": "authorization_code",
        })

    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")

    tokens = token_response.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    # Use the access token to get the creator's Google profile
    async with httpx.AsyncClient() as client:
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )

    if userinfo_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch user info")

    userinfo = userinfo_response.json()
    email = userinfo.get("email")
    name = userinfo.get("name", "Creator")
    avatar = userinfo.get("picture")

    # Check if this creator already exists in our DB
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        # Existing creator — update their tokens (they may have re-authorized)
        user.google_access_token = access_token
        if refresh_token:
            user.google_refresh_token = refresh_token
        user.avatar_url = avatar
    else:
        # New creator — create their account
        base_slug = slugify(name)
        slug = base_slug

        # Make sure the slug is unique — add a number if taken
        counter = 1
        while True:
            existing = await db.execute(select(User).where(User.slug == slug))
            if not existing.scalar_one_or_none():
                break
            slug = f"{base_slug}{counter}"
            counter += 1

        user = User(
            email=email,
            name=name,
            slug=slug,
            avatar_url=avatar,
            google_access_token=access_token,
            google_refresh_token=refresh_token,
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    # Redirect creator back to their dashboard on the frontend
    # Pass their user ID as a query param so the frontend knows who logged in
    return RedirectResponse(f"{FRONTEND_URL}/dashboard?user_id={user.id}")


@router.get("/me")
async def get_current_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns the creator's profile data.
    Frontend calls this on page load to get logged-in user info.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "slug": user.slug,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "location": user.location,
        "contact_email": user.contact_email,
        "niche": user.niche,
        "kit_url": f"{FRONTEND_URL}/kit/{user.slug}",
    }
