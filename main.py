import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from tortoise.contrib.fastapi import register_tortoise
from config import (
    DATABASE_CONFIG, ALLOWED_HOSTS, ADMIN_SECRET_KEY
)
from api.client_site.v1 import router as client_site_v1_router

# === Logging configuration ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log"),
    ]
)

# === Application initialization ===
app = FastAPI(
    title="SpeakNowly API",
    description="Modular FastAPI backend for SpeakNowly platform.",
    version="1.0.0"
)

# === CORS middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOSTS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# === Routers and static files ===
app.include_router(client_site_v1_router, prefix="/api/v1")
app.mount("/media", StaticFiles(directory="media"), name="media")

# === Database setup ===
register_tortoise(
    app,
    config=DATABASE_CONFIG,
    generate_schemas=False,
    add_exception_handlers=True,
)

import admin

from fastadmin import fastapi_app as admin_app

app.mount("/admin", admin_app, name="admin")
# === Root endpoint ===
@app.get("/")
def read_root():
    return {"message": "Welcome to the SpeakNowly FastAPI application!"}