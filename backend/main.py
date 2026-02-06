import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database import init_db
from backend.routers import auth as auth_router
from backend.routers import chat as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create data sub-directories
    for subdir in ["documentos", "imagenes", "generados"]:
        os.makedirs(os.path.join(settings.DATA_DIR, subdir), exist_ok=True)
    # Initialize database tables
    init_db()
    yield


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

# Static frontend files — must be last (catches all unmatched paths)
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
frontend_dir = os.path.abspath(frontend_dir)
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
