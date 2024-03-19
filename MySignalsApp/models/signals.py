from sqlalchemy.dialects.postgresql import JSON
from MySignalsApp.models.base import BaseModel
from MySignalsApp import db


class Signal(BaseModel):
    __tablename__ = "signals"

    id = db.Column(db.Integer(), primary_key=True, unique=True, nullable=False)
    signal = db.Column(JSON, nullable=False)
    is_spot = db.Column(db.Boolean(), nullable=False, default=True)
    status = db.Column(db.Boolean(), nullable=False, default=False)
    provider = db.Column(db.String(34), db.ForeignKey("users.id"), nullable=False)
    short_text = db.Column(db.String(100), nullable=True)
    placed_signals = db.Relationship(
        "PlacedSignals", backref="signal", lazy=True, cascade="all, delete-orphan"
    )

    def __init__(self, signal, status, provider, is_spot, short_text):
        self.signal = signal
        self.status = status
        self.provider = provider
        self.is_spot = is_spot
        self.short_text = short_text

    def __repr__(self):
        return f"id({self.id}), signal({self.signal}), status({self.status}), date_created({self.date_created}), provider({self.user.user_name}), provider_id({self.provider})) \n"

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
            "short_text": self.short_text,
            "date_created": self.date_created,
        }
