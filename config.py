from datetime import timedelta
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent

# === Core settings ===
SECRET_KEY = config("SECRET_KEY")
ALGORITHM = config("ALGORITHM", default="HS256")
DEBUG = config("DEBUG", cast=bool, default=False)

# === Allowed hosts / CORS ===
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*")

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = [
    "accept-language",
    "authorization",
    "content-type",
]

# === Database settings ===
DATABASE_URL = config("DATABASE_URL")
DATABASE_CONFIG = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": [
                "models.users.users",
                "models.users.verification_codes",
                "models.tests.listening",
                "models.tests.reading",
                "models.tests.speaking",
                "models.tests.writing",
                "models.tests.test_type",
                "models.analyses",
                "models.comments",
                "models.notifications",
                "models.tariffs",
                "models.transactions",
                "models.payments",
                "aerich.models"
            ],
            "default_connection": "default",
        }
    },
}

REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/0")

# === Email settings ===
EMAIL_BACKEND = config("EMAIL_BACKEND", default="http")  # smtp или http
EMAIL_FROM = config("EMAIL_FROM", default="no-reply@example.com")

# === SMTP backend ===
SMTP_HOST = config("SMTP_HOST", default="")
SMTP_PORT = config("SMTP_PORT", cast=int, default=0)
SMTP_USER = config("SMTP_USER", default="")
SMTP_PASSWORD = config("SMTP_PASSWORD", default="")

# === HTTP API email backend ===
EMAIL_PROVIDER_URL = config("EMAIL_PROVIDER_URL", default="")
EMAIL_PROVIDER_APIKEY = config("EMAIL_PROVIDER_APIKEY", default="")

# === JWT settings ===
ACCESS_TOKEN_EXPIRE = timedelta(days=5)
REFRESH_TOKEN_EXPIRE = timedelta(days=90)

# === API keys ===
GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET", default="https://maps.googleapis.com/maps/api/place/autocomplete/json")
OPENAI_API_KEY = config("OPENAI_API_KEY", default="")

# === Telegram bot settings ===
TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN", default="")

# === Admin settings ===
ADMIN_USER_MODEL = config("ADMIN_USER_MODEL")
ADMIN_USER_MODEL_USERNAME_FIELD = config("ADMIN_USER_MODEL_USERNAME_FIELD")
ADMIN_SECRET_KEY = config("ADMIN_SECRET_KEY")