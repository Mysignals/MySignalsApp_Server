from MySignalsApp import db
from uuid import uuid4
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
import enum


def get_uuid():
    return uuid4().hex


class Roles(enum.Enum):
    USER = "User"
    PROVIDER = ("User", "Provider")
    REGISTRAR = ("User", "Registrar")

    @staticmethod
    def fetch_names():
        return [c.value for c in Roles]


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(
        db.String(34), primary_key=True, unique=True, nullable=False, default=get_uuid
    )
    user_name = db.Column(db.String(345), unique=True, nullable=False)
    email = db.Column(db.String(345), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    api_key = db.Column(db.String(), nullable=False)
    api_secret = db.Column(db.String(), nullable=False)
    wallet = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean(), nullable=False, default=False)
    roles = db.Column(db.Enum(Roles), nullable=False, default=Roles.USER)
    date_registered = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    signals = db.Relationship("Signal", backref="user", lazy=True)

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
        return f"user_name({self.user_name}), email({self.email}), is_active({self.is_active}), date_registered({self.date_registered}))"

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
            "id": self.id,
            "email": self.email,
            "user_name": self.user_name,
            "roles": self.roles,
            "is_active": self.is_active,
            "wallet": self.wallet,
            "has_api_keys": True if self.api_key and self.api_secret else False,
            "date_registered": self.date_registered,
        }


class Signal(db.Model):
    __tablename__ = "signals"
    id = db.Column(db.Integer(), primary_key=True, unique=True, nullable=False)
    signal = db.Column(JSON, nullable=False)
    is_spot = db.Column(db.Boolean(), nullable=False, default=True)
    status = db.Column(db.Boolean(), nullable=False, default=False)
    provider = db.Column(db.String(34), db.ForeignKey("users.id"), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, signal, status, provider, is_spot=True):
        self.signal = signal
        self.status = status
        self.provider = provider
        self.is_spot = is_spot

    def __repr__(self):
        return f"signal({self.signal}), status({self.status}), date_created({self.date_created}), provider({self.provider.user_name}))"

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
            "id": self.id,
            "signal": self.signal,
            "status": self.status,
            "is_spot": self.is_spot,
            "provider": self.user.wallet,
            "date_created": self.date_created,
        }
