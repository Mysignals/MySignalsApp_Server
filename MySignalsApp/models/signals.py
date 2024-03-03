from sqlalchemy.dialects.postgresql import JSON
from MySignalsApp.models.base import BaseModel
from MySignalsApp import db, admin
from flask import session, flash, redirect
from flask_admin.contrib.sqla import ModelView


class Signal(BaseModel):
    __tablename__ = "signals"

    id = db.Column(db.Integer(), primary_key=True, unique=True, nullable=False)
    signal = db.Column(JSON, nullable=False)
    is_spot = db.Column(db.Boolean(), nullable=False, default=True)
    status = db.Column(db.Boolean(), nullable=False, default=False)
    provider = db.Column(db.String(34), db.ForeignKey("users.id"), nullable=False)
    placed_signals = db.Relationship(
        "PlacedSignals", backref="signal", lazy=True, cascade="all, delete-orphan"
    )

    def __init__(self, signal, status, provider, is_spot):
        self.signal = signal
        self.status = status
        self.provider = provider
        self.is_spot = is_spot

    def __repr__(self):
        return f"id({self.id}), signal({self.signal}), status({self.status}), date_created({self.date_created}), provider({self.user.user_name}), provider_id({self.provider}))"

    def __str__(self):
        return f"{self.signal}"

    def format(self):
        return {
            "id": self.id,
            "signal": self.signal,
            "status": self.status,
            "is_spot": self.is_spot,
            "provider": self.user.user_name,
            "provider_wallet": self.user.wallet,
            "date_created": self.date_created,
        }
