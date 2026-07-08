from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from database import get_db
from models import User, YoutubeStats, InstagramStats, SponsorshipRate
import json
import os

router = APIRouter(prefix="/profile", tags=["profile"])
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


# --- Request body schemas (Pydantic validates incoming JSON automatically) ---

class ProfileUpdate(BaseModel):
    bio: str | None = None
    location: str | None = None
    contact_email: str | None = None
    niche: str | None = None


class RateItem(BaseModel):
    package_name: str
    price: str
    description: str | None = None


class RatesUpdate(BaseModel):
    rates: list[RateItem]


# --- Endpoints ---

@router.patch("/{user_id}")
async def update_profile(
    user_id: str,
    body: ProfileUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Creator updates their public profile info.
    Only updates fields that are actually sent — None fields are ignored.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.bio is not None:
        user.bio = body.bio
    if body.location is not None:
        user.location = body.location
    if body.contact_email is not None:
        user.contact_email = body.contact_email
    if body.niche is not None:
        user.niche = body.niche

    await db.commit()
    return {"message": "Profile updated"}


@router.put("/{user_id}/rates")
async def update_rates(
    user_id: str,
    body: RatesUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Creator sets their sponsorship rates.
    Replaces all existing rates with the new list.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete old rates
    old_rates = await db.execute(
        select(SponsorshipRate).where(SponsorshipRate.user_id == user_id)
    )
    for rate in old_rates.scalars().all():
        await db.delete(rate)

    # Insert new rates
    for item in body.rates:
        rate = SponsorshipRate(
            user_id=user_id,
            package_name=item.package_name,
            price=item.price,
            description=item.description,
        )
        db.add(rate)

    await db.commit()
    return {"message": "Rates updated"}


@router.get("/kit/{slug}")
async def get_public_kit(slug: str, db: AsyncSession = Depends(get_db)):
    """
    PUBLIC endpoint — no login required.
    This is what brands see when they open the shareable link.
    Returns all the creator's cached stats + rates in one response.
    """
    result = await db.execute(select(User).where(User.slug == slug))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Creator not found")

    # Get latest YouTube stats
    yt_result = await db.execute(
        select(YoutubeStats)
        .where(YoutubeStats.user_id == user.id)
        .order_by(YoutubeStats.fetched_at.desc())
    )
    yt = yt_result.scalar_one_or_none()

    # Get latest Instagram stats
    ig_result = await db.execute(
        select(InstagramStats)
        .where(InstagramStats.user_id == user.id)
        .order_by(InstagramStats.fetched_at.desc())
    )
    ig = ig_result.scalar_one_or_none()

    # Get sponsorship rates
    rates_result = await db.execute(
        select(SponsorshipRate)
        .where(SponsorshipRate.user_id == user.id)
        .where(SponsorshipRate.is_active == True)
    )
    rates = rates_result.scalars().all()

    return {
        "creator": {
            "name": user.name,
            "slug": user.slug,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
            "location": user.location,
            "contact_email": user.contact_email,
            "niche": user.niche,
        },
        "youtube": {
            "channel_name": yt.channel_name if yt else None,
            "subscriber_count": yt.subscriber_count if yt else None,
            "avg_views_per_video": yt.avg_views_per_video if yt else None,
            "engagement_rate": yt.engagement_rate if yt else None,
            "age_demographics": json.loads(yt.age_demographics or "{}") if yt else {},
            "country_demographics": json.loads(yt.country_demographics or "{}") if yt else {},
        } if yt else None,
        "instagram": {
            "username": ig.username if ig else None,
            "follower_count": ig.follower_count if ig else None,
            "avg_reel_views": ig.avg_reel_views if ig else None,
            "engagement_rate": ig.engagement_rate if ig else None,
        } if ig else None,
        "sponsorship_rates": [
            {
                "package_name": r.package_name,
                "price": r.price,
                "description": r.description,
            }
            for r in rates
        ],
    }
