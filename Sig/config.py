import os
from dotenv import load_dotenv

load_dotenv(".env")

class App_Config:
    SECRETE_KEY=os.environ.get("SECRETE_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get("USER_NAME")
    MAIL_PASSWORD = os.environ.get("PASS")
