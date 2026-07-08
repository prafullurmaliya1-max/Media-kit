from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Async engine — handles all Postgres connections
# pool_size=10 means up to 10 simultaneous DB connections
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    echo=False,  # Set True to print SQL queries while debugging
)

# Session factory — every API request gets its own isolated session
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# All database models inherit from this base class
class Base(DeclarativeBase):
    pass

# FastAPI dependency — injected into any route that needs DB access
# 'yield' ensures the session always closes after the request finishes
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
