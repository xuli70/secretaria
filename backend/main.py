import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.auth import hash_password, verify_password
from backend.config import settings
from backend.database import init_db, SessionLocal
from backend.models import User
from backend.routers import auth as auth_router
from backend.routers import chat as chat_router
from backend.routers import upload as upload_router
from backend.routers import documents as documents_router
from backend.routers import telegram as telegram_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create data sub-directories
    for subdir in ["documentos", "imagenes", "generados"]:
        os.makedirs(os.path.join(settings.DATA_DIR, subdir), exist_ok=True)
    # Initialize database tables
    init_db()
    # Auto-create/update admin user from env vars
    _ensure_admin_user()
    yield


def _ensure_admin_user():
    """Create or update the admin user from APP_USERNAME / APP_PASSWORD env vars."""
    if not settings.APP_USERNAME or not settings.APP_PASSWORD:
        return
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == settings.APP_USERNAME).first()
        if user:
            if not verify_password(settings.APP_PASSWORD, user.password_hash):
                user.password_hash = hash_password(settings.APP_PASSWORD)
                db.commit()
        else:
            user = User(
                username=settings.APP_USERNAME,
                password_hash=hash_password(settings.APP_PASSWORD),
            )
            db.add(user)
            db.commit()
    finally:
        db.close()


app = FastAPI(
    title="Secretaria",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}


# Routers
app.include_router(auth_router.router)
app.include_router(chat_router.router)
app.include_router(upload_router.router)
app.include_router(documents_router.router)
app.include_router(telegram_router.router)

# Static frontend files — must be last (catches all unmatched paths)
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
frontend_dir = os.path.abspath(frontend_dir)
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
