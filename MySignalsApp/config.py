import os
import datetime
from dotenv import load_dotenv


load_dotenv(".env")


class App_Config:
    SESSION_TYPE = "sqlalchemy"
    SESSION_USE_SIGNER = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "None"
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=1)

    SECRET_KEY = os.environ.get("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get("USER_NAME")
    MAIL_PASSWORD = os.environ.get("PASS")

    CACHE_TYPE = "RedisCache" if os.environ.get("REDIS") else "FileSystemCache"
    CACHE_REDIS_HOST = os.environ.get("REDISHOST")
    CACHE_REDIS_PORT = os.environ.get("REDISPORT")
    CACHE_DIR = "cache"

    FLASK_ADMIN_SWATCH = "slate"

    TIMEZONE = "UTC"
