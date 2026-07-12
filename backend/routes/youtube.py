from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import json
import os
from database import get_db
from models import User, YoutubeStats
from cache import is_cache_fresh, minutes_until_refresh

router = APIRouter(prefix="/youtube", tags=["youtube"])

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YT_BASE = "https://www.googleapis.com/youtube/v3"


async def fetch_channel_stats(access_token: str) -> dict:
    """
    Calls YouTube Data API v3 to get the creator's channel stats.
    Uses their OAuth access token (not just the API key) so we get private analytics too.
    """
    async with httpx.AsyncClient() as client:
        # Get channel info + stats
        channel_resp = await client.get(
            f"{YT_BASE}/channels",
            params={
                "part": "snippet,statistics",
                "mine": "true",  # 'mine=true' means the authenticated creator's channel
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if channel_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch YouTube channel")

        channel_data = channel_resp.json()
        items = channel_data.get("items", [])

        if not items:
            raise HTTPException(status_code=404, detail="No YouTube channel found for this account")

        channel = items[0]
        stats = channel.get("statistics", {})
        snippet = channel.get("snippet", {})

        # Get recent videos to calculate avg views + engagement
        videos_resp = await client.get(
            f"{YT_BASE}/search",
            params={
                "part": "id",
                "channelId": channel.get("id"),
                "order": "date",
                "maxResults": 10,
                "type": "video",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        avg_views = 0
        avg_likes = 0
        engagement_rate = 0.0

        if videos_resp.status_code == 200:
            video_ids = [
                item["id"]["videoId"]
                for item in videos_resp.json().get("items", [])
                if "videoId" in item.get("id", {})
            ]

            if video_ids:
                # Get stats for all recent videos in one API call
                video_stats_resp = await client.get(
                    f"{YT_BASE}/videos",
                    params={
                        "part": "statistics",
                        "id": ",".join(video_ids),
                    },
                    headers={"Authorization": f"Bearer {access_token}"}
                )

                if video_stats_resp.status_code == 200:
                    video_items = video_stats_resp.json().get("items", [])
                    if video_items:
                        views_list = [int(v["statistics"].get("viewCount", 0)) for v in video_items]
                        likes_list = [int(v["statistics"].get("likeCount", 0)) for v in video_items]
                        avg_views = sum(views_list) / len(views_list)
                        avg_likes = sum(likes_list) / len(likes_list)
                        # Engagement = (avg likes / avg views) * 100
                        if avg_views > 0:
                            engagement_rate = round((avg_likes / avg_views) * 100, 2)

        subscriber_count = int(stats.get("subscriberCount", 0))
        total_views = int(stats.get("viewCount", 0))
        video_count = int(stats.get("videoCount", 0))

        return {
            "channel_id": channel.get("id"),
            "channel_name": snippet.get("title"),
            "subscriber_count": subscriber_count,
            "total_view_count": total_views,
            "video_count": video_count,
            "avg_views_per_video": round(avg_views),
            "avg_likes_per_video": round(avg_likes),
            "engagement_rate": engagement_rate,
        }


@router.get("/stats/{user_id}")
async def get_youtube_stats(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Main endpoint — returns YouTube stats for a creator.
    Checks cache first. Only calls YouTube API if cache is older than 1 hour.
    """
    # Get the creator
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.google_access_token:
        raise HTTPException(status_code=401, detail="YouTube not connected. Please login with Google first.")

    # Check if we have fresh cached stats
    cached = await db.execute(
        select(YoutubeStats)
        .where(YoutubeStats.user_id == user_id)
        .order_by(YoutubeStats.fetched_at.desc())
    )
    cached_stats = cached.scalar_one_or_none()

    if cached_stats and is_cache_fresh(cached_stats.fetched_at):
        # Return cached data — no API call needed
        return {
            "source": "cache",
            "refreshes_in_minutes": minutes_until_refresh(cached_stats.fetched_at),
            "data": {
                "channel_name": cached_stats.channel_name,
                "subscriber_count": cached_stats.subscriber_count,
                "total_view_count": cached_stats.total_view_count,
                "video_count": cached_stats.video_count,
                "avg_views_per_video": cached_stats.avg_views_per_video,
                "engagement_rate": cached_stats.engagement_rate,
                "age_demographics": json.loads(cached_stats.age_demographics or "{}"),
                "country_demographics": json.loads(cached_stats.country_demographics or "{}"),
            }
        }

    # Cache is stale — fetch fresh data from YouTube API
    fresh_data = await fetch_channel_stats(user.google_access_token)

    # Save to DB (upsert pattern — update if exists, insert if not)
    if cached_stats:
        for key, value in fresh_data.items():
            setattr(cached_stats, key, value)
        # Reset fetched_at so cache timer restarts
        from datetime import datetime, timezone
        cached_stats.fetched_at = datetime.utcnow()
    else:
        cached_stats = YoutubeStats(user_id=user_id, **fresh_data)
        db.add(cached_stats)

    await db.commit()

    return {
        "source": "api",
        "refreshes_in_minutes": 60,
        "data": fresh_data
    }
