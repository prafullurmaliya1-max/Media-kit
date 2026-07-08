from sqlalchemy import String, Integer, BigInteger, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from database import Base
import uuid


class User(Base):
    """
    One row per creator who signs up.
    Stores their OAuth tokens so we can call YouTube/Instagram on their behalf.
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # e.g. "aryankapoor" → /kit/aryankapoor
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Google OAuth tokens
    google_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_token_expiry: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)

    # Instagram OAuth tokens
    instagram_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    instagram_user_id: Mapped[str | None] = mapped_column(String, nullable=True)

    # Profile info the creator fills in manually
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String, nullable=True)
    niche: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g. "Tech, AI, Education"

    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    youtube_stats: Mapped[list["YoutubeStats"]] = relationship("YoutubeStats", back_populates="user")
    instagram_stats: Mapped[list["InstagramStats"]] = relationship("InstagramStats", back_populates="user")
    sponsorship_rates: Mapped[list["SponsorshipRate"]] = relationship("SponsorshipRate", back_populates="user")


class YoutubeStats(Base):
    """
    Cached YouTube stats per creator.
    We only call the YouTube API once per hour — results stored here.
    """
    __tablename__ = "youtube_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)

    # Channel-level stats
    channel_id: Mapped[str | None] = mapped_column(String, nullable=True)
    channel_name: Mapped[str | None] = mapped_column(String, nullable=True)
    subscriber_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    total_view_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    video_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Engagement metrics (calculated from last 10 videos)
    avg_views_per_video: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_likes_per_video: Mapped[float | None] = mapped_column(Float, nullable=True)
    engagement_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Monthly view trend — stored as comma-separated values for simplicity
    # e.g. "890000,1050000,980000,1240000,1380000,1420000"
    monthly_views_trend: Mapped[str | None] = mapped_column(Text, nullable=True)
    monthly_subs_trend: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audience demographics (percentages stored as JSON string)
    age_demographics: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON
    country_demographics: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # When this cache was last refreshed
    fetched_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="youtube_stats")


class InstagramStats(Base):
    """
    Cached Instagram stats per creator.
    Same pattern as YouTube — cached hourly to avoid API rate limits.
    """
    __tablename__ = "instagram_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)

    # Account-level stats
    instagram_id: Mapped[str | None] = mapped_column(String, nullable=True)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    follower_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    following_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    media_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Engagement
    avg_reel_views: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_story_reach: Mapped[float | None] = mapped_column(Float, nullable=True)
    engagement_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    fetched_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="instagram_stats")


class SponsorshipRate(Base):
    """
    Rates the creator sets manually for brand deals.
    Displayed on their public media kit page.
    """
    __tablename__ = "sponsorship_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)

    package_name: Mapped[str] = mapped_column(String, nullable=False)   # e.g. "Dedicated video"
    price: Mapped[str] = mapped_column(String, nullable=False)           # e.g. "₹80,000"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship("User", back_populates="sponsorship_rates")
