from MySignalsApp.models.base import BaseModel
from MySignalsApp import db
import enum

class Roles(enum.Enum):
    USER = "User"
    PROVIDER = ("User", "Provider")
    REGISTRAR = ("User", "Registrar")

    @staticmethod
    def fetch_names():
        return [c.value for c in Roles]


class User(BaseModel):
    __tablename__ = "users"

    user_name = db.Column(db.String(345), unique=True, nullable=False)
    email = db.Column(db.String(345), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    api_key = db.Column(db.String(90), nullable=False)
    api_secret = db.Column(db.String(90), nullable=False)
    wallet = db.Column(db.String(43), nullable=True)
    is_active = db.Column(db.Boolean(), nullable=False, default=False)
    roles = db.Column(db.Enum(Roles), nullable=False, default=Roles.USER)
    signals = db.Relationship("Signal", backref="user", lazy=True)
    placed_signals = db.Relationship("PlacedSignals", backref="user", lazy=True)
    tokens = db.Relationship("UserTokens", backref="user", lazy=True)

    def __init__(
        self,
        user_name,
        email,
        password,
        api_key,
        api_secret,
        roles=Roles.USER,
        wallet="",
    ):
        self.user_name = user_name
        self.email = email
        self.password = password
        self.roles = roles
        self.api_key = api_key
        self.api_secret = api_secret
        self.wallet = wallet

    def __repr__(self):
        return f"user_name({self.user_name}), email({self.email}), is_active({self.is_active}), date_created({self.date_created}))"

    def __str__(self):
        return self.email

    def format(self):
        return {
            "id": self.id,
            "email": self.email,
            "user_name": self.user_name,
            "roles": self.roles,
            "is_active": self.is_active,
            "wallet": self.wallet,
            "has_api_keys": True if self.api_key and self.api_secret else False,
            "date_created": self.date_created,
        }