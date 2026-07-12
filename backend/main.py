from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from database import engine, Base
from routes import auth, youtube, instagram, profile
import os

load_dotenv()

# --- App setup ---
app = FastAPI(
    title="Creator Media Kit API",
    description="Backend for the Creator Media Kit Dashboard",
    version="1.0.0",
)

# --- CORS Middleware ---
# This allows your Next.js frontend (running on localhost:3000) to call this API
# Without this, the browser will block all requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
        "http://localhost:3000",
        "https://media-kit-tan.vercel.app",
        "https://influencerskit.netlify.app",
        "https://media-kit-izqd.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register all route groups ---
app.include_router(auth.router)
app.include_router(youtube.router)
app.include_router(instagram.router)
app.include_router(profile.router)


# --- Create all DB tables on startup ---
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # Creates all tables defined in models.py if they don't exist yet
        # In production, you'd use Alembic migrations instead
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables ready")


# --- Health check endpoint ---
# Hit this first after starting the server to confirm everything works
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "message": "Creator Media Kit API is running",
    }


# --- All available routes (for reference) ---
@app.get("/")
async def root():
    return {
        "api": "Creator Media Kit",
        "version": "1.0.0",
        "routes": {
            "health":           "GET  /health",
            "google_login":     "GET  /auth/google",
            "oauth_callback":   "GET  /auth/callback",
            "current_user":     "GET  /auth/me?user_id=xxx",
            "youtube_stats":    "GET  /youtube/stats/{user_id}",
            "instagram_connect":"GET  /instagram/connect",
            "instagram_stats":  "GET  /instagram/stats/{user_id}",
            "update_profile":   "PATCH /profile/{user_id}",
            "update_rates":     "PUT  /profile/{user_id}/rates",
            "public_kit":       "GET  /profile/kit/{slug}",
        }
    }
