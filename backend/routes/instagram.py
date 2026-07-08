from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import os
from database import get_db
from models import User, InstagramStats
from cache import is_cache_fresh, minutes_until_refresh

router = APIRouter(prefix="/instagram", tags=["instagram"])

INSTAGRAM_APP_ID = os.getenv("INSTAGRAM_APP_ID")
INSTAGRAM_APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Instagram Graph API base URL
IG_BASE = "https://graph.instagram.com"
IG_AUTH_URL = "https://api.instagram.com/oauth/authorize"
IG_TOKEN_URL = "https://api.instagram.com/oauth/access_token"


@router.get("/connect")
async def instagram_connect():
    """
    Redirects creator to Instagram's OAuth page.
    Creator clicks 'Connect Instagram' → lands here → goes to Instagram.
    """
    params = {
        "client_id": INSTAGRAM_APP_ID,
        "redirect_uri": f"{BACKEND_URL}/instagram/callback",
        "scope": "instagram_basic,instagram_manage_insights",
        "response_type": "code",
    }
    from fastapi.responses import RedirectResponse
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"{IG_AUTH_URL}?{query}")


@router.get("/callback")
async def instagram_callback(code: str, user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Instagram redirects back here after the creator approves access.
    We exchange the code for a long-lived access token and save it.

    Note: user_id is passed as a query param from the frontend
    so we know which creator is connecting their Instagram.
    """
    # Step 1: short-lived token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(IG_TOKEN_URL, data={
            "client_id": INSTAGRAM_APP_ID,
            "client_secret": INSTAGRAM_APP_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": f"{BACKEND_URL}/instagram/callback",
            "code": code,
        })

    if token_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get Instagram token")

    short_token = token_resp.json().get("access_token")
    ig_user_id = str(token_resp.json().get("user_id"))

    # Step 2: exchange for long-lived token (valid 60 days)
    async with httpx.AsyncClient() as client:
        long_token_resp = await client.get(
            f"{IG_BASE}/access_token",
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": INSTAGRAM_APP_SECRET,
                "access_token": short_token,
            }
        )

    long_token = long_token_resp.json().get("access_token", short_token)

    # Save tokens to the creator's user record
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.instagram_access_token = long_token
    user.instagram_user_id = ig_user_id
    await db.commit()

    return {"message": "Instagram connected successfully"}


@router.get("/stats/{user_id}")
async def get_instagram_stats(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns Instagram stats — from cache if fresh, from API if stale.
    Same pattern as YouTube stats endpoint.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.instagram_access_token:
        raise HTTPException(status_code=401, detail="Instagram not connected.")

    # Check cache
    cached = await db.execute(
        select(InstagramStats)
        .where(InstagramStats.user_id == user_id)
        .order_by(InstagramStats.fetched_at.desc())
    )
    cached_stats = cached.scalar_one_or_none()

    if cached_stats and is_cache_fresh(cached_stats.fetched_at):
        return {
            "source": "cache",
            "refreshes_in_minutes": minutes_until_refresh(cached_stats.fetched_at),
            "data": {
                "username": cached_stats.username,
                "follower_count": cached_stats.follower_count,
                "media_count": cached_stats.media_count,
                "avg_reel_views": cached_stats.avg_reel_views,
                "avg_story_reach": cached_stats.avg_story_reach,
                "engagement_rate": cached_stats.engagement_rate,
            }
        }

    # Fetch fresh from Instagram Graph API
    async with httpx.AsyncClient() as client:
        profile_resp = await client.get(
            f"{IG_BASE}/{user.instagram_user_id}",
            params={
                "fields": "id,username,followers_count,media_count",
                "access_token": user.instagram_access_token,
            }
        )

    if profile_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch Instagram stats")

    profile = profile_resp.json()

    fresh_data = {
        "instagram_id": profile.get("id"),
        "username": profile.get("username"),
        "follower_count": profile.get("followers_count"),
        "media_count": profile.get("media_count"),
        "avg_reel_views": None,    # Requires advanced insights — add later
        "avg_story_reach": None,
        "engagement_rate": None,
    }

    # Upsert stats
    if cached_stats:
        for key, value in fresh_data.items():
            setattr(cached_stats, key, value)
        from datetime import datetime, timezone
        cached_stats.fetched_at = datetime.now(timezone.utc)
    else:
        cached_stats = InstagramStats(user_id=user_id, **fresh_data)
        db.add(cached_stats)

    await db.commit()

    return {
        "source": "api",
        "refreshes_in_minutes": 60,
        "data": fresh_data,
    }
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.responses import RedirectResponse
import httpx
import os
from database import get_db
from models import User, InstagramStats
from cache import is_cache_fresh, minutes_until_refresh
from datetime import datetime, timezone

router = APIRouter(prefix="/instagram", tags=["instagram"])

INSTAGRAM_APP_ID = os.getenv("INSTAGRAM_APP_ID")
INSTAGRAM_APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

IG_BASE = "https://graph.instagram.com"
IG_AUTH_URL = "https://api.instagram.com/oauth/authorize"
IG_TOKEN_URL = "https://api.instagram.com/oauth/access_token"


@router.get("/connect")
async def instagram_connect():
    params = {
        "client_id": INSTAGRAM_APP_ID,
        "redirect_uri": f"{BACKEND_URL}/instagram/callback",
        "scope": "instagram_basic,instagram_manage_insights",
        "response_type": "code",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"{IG_AUTH_URL}?{query}")


@router.get("/callback")
async def instagram_callback(code: str, user_id: str, db: AsyncSession = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(IG_TOKEN_URL, data={
            "client_id": INSTAGRAM_APP_ID,
            "client_secret": INSTAGRAM_APP_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": f"{BACKEND_URL}/instagram/callback",
            "code": code,
        })

    if token_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get Instagram token")

    short_token = token_resp.json().get("access_token")
    ig_user_id = str(token_resp.json().get("user_id"))

    async with httpx.AsyncClient() as client:
        long_token_resp = await client.get(
            f"{IG_BASE}/access_token",
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": INSTAGRAM_APP_SECRET,
                "access_token": short_token,
            }
        )

    long_token = long_token_resp.json().get("access_token", short_token)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.instagram_access_token = long_token
    user.instagram_user_id = ig_user_id
    await db.commit()

    return RedirectResponse(f"{FRONTEND_URL}/dashboard?user_id={user_id}")


@router.get("/stats/{user_id}")
async def get_instagram_stats(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.instagram_access_token:
        raise HTTPException(status_code=401, detail="Instagram not connected.")

    cached = await db.execute(
        select(InstagramStats)
        .where(InstagramStats.user_id == user_id)
        .order_by(InstagramStats.fetched_at.desc())
    )
    cached_stats = cached.scalar_one_or_none()

    if cached_stats and is_cache_fresh(cached_stats.fetched_at):
        return {
            "source": "cache",
            "refreshes_in_minutes": minutes_until_refresh(cached_stats.fetched_at),
            "data": {
                "username": cached_stats.username,
                "follower_count": cached_stats.follower_count,
                "media_count": cached_stats.media_count,
                "avg_reel_views": cached_stats.avg_reel_views,
                "avg_story_reach": cached_stats.avg_story_reach,
                "engagement_rate": cached_stats.engagement_rate,
            }
        }

    async with httpx.AsyncClient() as client:
        profile_resp = await client.get(
            f"{IG_BASE}/{user.instagram_user_id}",
            params={
                "fields": "id,username,followers_count,media_count",
                "access_token": user.instagram_access_token,
            }
        )

    if profile_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch Instagram stats")

    profile = profile_resp.json()

    fresh_data = {
        "instagram_id": profile.get("id"),
        "username": profile.get("username"),
        "follower_count": profile.get("followers_count"),
        "media_count": profile.get("media_count"),
        "avg_reel_views": None,
        "avg_story_reach": None,
        "engagement_rate": None,
    }

    if cached_stats:
        for key, value in fresh_data.items():
            setattr(cached_stats, key, value)
        cached_stats.fetched_at = datetime.now(timezone.utc)
    else:
        cached_stats = InstagramStats(user_id=user_id, **fresh_data)
        db.add(cached_stats)

    await db.commit()

    return {
        "source": "api",
        "refreshes_in_minutes": 60,
        "data": fresh_data,
    }


@router.get("/test-stats/{user_id}")
async def get_instagram_test_stats(
    user_id: str,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    For testing during development — pass the token directly as a query param.
    Usage: /instagram/test-stats/{user_id}?token=your_token_here
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    async with httpx.AsyncClient() as client:
        profile_resp = await client.get(
            f"{IG_BASE}/me",
            params={
                "fields": "id,username,followers_count,media_count",
                "access_token": token,
            }
        )

    if profile_resp.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Instagram error: {profile_resp.text}"
        )

    profile = profile_resp.json()

    user.instagram_access_token = token
    user.instagram_user_id = profile.get("id")
    await db.commit()

    cached = await db.execute(
        select(InstagramStats)
        .where(InstagramStats.user_id == user_id)
        .order_by(InstagramStats.fetched_at.desc())
    )
    cached_stats = cached.scalar_one_or_none()

    fresh_data = {
        "instagram_id": profile.get("id"),
        "username": profile.get("username"),
        "follower_count": profile.get("followers_count"),
        "media_count": profile.get("media_count"),
        "avg_reel_views": None,
        "avg_story_reach": None,
        "engagement_rate": None,
    }

    if cached_stats:
        for key, value in fresh_data.items():
            setattr(cached_stats, key, value)
        cached_stats.fetched_at = datetime.now(timezone.utc)
    else:
        cached_stats = InstagramStats(user_id=user_id, **fresh_data)
        db.add(cached_stats)

    await db.commit()

    return {
        "message": "Instagram connected successfully",
        "username": profile.get("username"),
        "followers": profile.get("followers_count"),
        "media_count": profile.get("media_count"),
    }