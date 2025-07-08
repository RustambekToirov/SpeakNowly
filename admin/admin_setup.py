from fastadmin import fastapi_app as admin_app
from fastadmin.settings import Settings
from models.users.users import User
from config import ADMIN_SECRET_KEY

Settings.ADMIN_USER_MODEL = User
Settings.ADMIN_USER_MODEL_USERNAME_FIELD = "email"
Settings.ADMIN_SECRET_KEY = ADMIN_SECRET_KEY
Settings.ADMIN_SITE_NAME = "SpeakNowly Admin"

admin_app.openapi_url = None
admin_app.docs_url    = None
admin_app.redoc_url   = None

