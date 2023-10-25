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
    rating = db.Relationship("PlacedSignals", backref="signal", lazy=True)

    def __init__(self, signal, status, provider, is_spot=True):
        self.signal = signal
        self.status = status
        self.provider = provider
        self.is_spot = is_spot

    def __repr__(self):
        return f"signal({self.signal}), status({self.status}), date_created({self.date_created}), provider({self.provider.user_name}))"


    def format(self):
        return {
            "id": self.id,
            "signal": self.signal,
            "status": self.status,
            "is_spot": self.is_spot,
            "provider": self.user.wallet,
            "date_created": self.date_created,
        }