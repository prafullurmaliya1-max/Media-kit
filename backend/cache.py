from datetime import datetime, timedelta, timezone


# How long before we refresh stats from the real API
CACHE_DURATION_HOURS = 1


def is_cache_fresh(fetched_at: datetime | None) -> bool:
    """
    Returns True if cached data is still fresh (< 1 hour old).
    Returns False if it's stale or never been fetched — meaning we need to call the API.

    Usage:
        if not is_cache_fresh(stats.fetched_at):
            stats = await fetch_fresh_youtube_stats(user)
    """
    if fetched_at is None:
        return False  # Never fetched — definitely stale

    # Make sure both datetimes are timezone-aware for comparison
    now = datetime.now(timezone.utc)

    if fetched_at.tzinfo is None:
        # If DB returned a naive datetime, assume UTC
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)

    age = now - fetched_at
    return age < timedelta(hours=CACHE_DURATION_HOURS)


def minutes_until_refresh(fetched_at: datetime | None) -> int:
    """
    Returns how many minutes until the cache expires.
    Useful for showing the creator 'Stats refresh in 34 minutes'.
    """
    if fetched_at is None:
        return 0

    now = datetime.now(timezone.utc)

    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)

    refresh_at = fetched_at + timedelta(hours=CACHE_DURATION_HOURS)
    remaining = refresh_at - now

    if remaining.total_seconds() <= 0:
        return 0

    return int(remaining.total_seconds() // 60)
