from MySignalsApp import db
from MySignalsApp.models.base import BaseModel
from MySignalsApp.models.notifications import Notification
from MySignalsApp.utils import query_one_filtered
from datetime import datetime
from random import choices
from uuid import uuid4
import enum


class Roles(enum.Enum):
    USER = "User"
    PROVIDER = ("User", "Provider")
    REGISTRAR = ("User", "Provider", "Registrar")

    @staticmethod
    def fetch_names():
        return [c.value for c in Roles]


class User(BaseModel):
    __tablename__ = "users"

    user_name = db.Column(db.String(345), unique=True, nullable=False, index=True)
    email = db.Column(db.String(345), unique=True, nullable=False, index=True)
    password = db.Column(db.String(64), nullable=False)
    api_key = db.Column(db.String(), nullable=True)
    api_secret = db.Column(db.String(), nullable=True)
    wallet = db.Column(db.String(43), nullable=True)
    is_active = db.Column(db.Boolean(), nullable=False, default=False)
    roles = db.Column(db.Enum(Roles), nullable=False, default=Roles.USER)
    last_notification_read_time = db.Column(db.DateTime(), nullable=True)
    referral_code = db.Column(
        db.String(8), unique=True, nullable=True
    )  # TODO:make non nullable
    referrers_code = db.Column(
        db.String(8), db.ForeignKey("users.referral_code"), nullable=True
    )
    referrals = db.Relationship("User", back_populates="referrer", lazy="dynamic")
    referrer = db.Relationship(
        "User", back_populates="referrals", lazy=True, remote_side=[referral_code]
    )
    provider_application = db.Relationship(
        "ProviderApplication", back_populates="user", lazy="dynamic"
    )
    signals = db.Relationship("Signal", backref="user", lazy=True)
    placed_signals = db.Relationship("PlacedSignals", backref="user", lazy=True)
    tokens = db.Relationship(
        "UserTokens", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    notifications = db.Relationship("Notification", backref="user", lazy=True)

    def __init__(
        self,
        user_name,
        email,
        password,
        roles=Roles.USER,
        referrers_code=None,
        wallet="",
    ):
        self.user_name = user_name
        self.email = email
        self.password = password
        self.roles = roles
        self.referrers_code = referrers_code
        self.wallet = wallet
        self.set_referral_code()

    def __repr__(self):
        return f"id({self.id}), user_name({self.user_name}), email({self.email}), is_active({self.is_active}), date_created({self.date_created}))"

    def __str__(self):
        return f"{self.email}"

    def set_referral_code(self):
        uuid = "".join(choices(uuid4().hex, k=8))
        while query_one_filtered(User, referral_code=uuid):
            uuid = "".join(choices(uuid4().hex, k=8))
        self.referral_code = uuid

    def get_unread_notifications_count(self):
        last_read_time = self.last_notification_read_time or datetime(1900, 1, 1)
        query = db.select(Notification).where(
            Notification.user_id == self.id,
            Notification.date_created > last_read_time,
        )

        return db.session.scalar(
            db.select(db.func.count()).select_from(query.subquery())
        )

    def format(self):
        return {
            "id": self.id,
            "email": self.email,
            "user_name": self.user_name,
            "roles": self.roles,
            "is_active": self.is_active,
            "unread_notifications": self.get_unread_notifications_count(),
            "referral_code": self.referral_code,
            "referrals": self.referrals.filter_by(is_active=True).count(),
            "referrers_wallet": self.referrer.wallet if self.referrer else None,
            "wallet": self.wallet,
            "has_api_keys": bool(self.api_key and self.api_secret),
            "date_created": self.date_created,
        }
