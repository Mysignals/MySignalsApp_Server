from MySignalsApp.models.base import BaseModel
from MySignalsApp import db


class PlacedSignals(BaseModel):
    __tablename__ = "placedsignals"
    id = db.Column(db.Integer(), primary_key=True, unique=True, nullable=False)
    user_id = db.Column(db.String(34), db.ForeignKey("users.id"), nullable=True)
    signal_id = db.Column(db.Integer(), db.ForeignKey("signals.id"), nullable=False)
    tx_hash = db.Column(db.String(66), nullable=False, default="0x0Dead")
    rating = db.Column(db.Integer(), nullable=False, default=0)

    db.UniqueConstraint(user_id, signal_id, name="_unique_user_signal_pair")

    def __init__(self, user_id, signal_id, tx_hash):
        self.user_id = user_id
        self.signal_id = signal_id
        self.tx_hash = tx_hash

    def __repr__(self):
        return f"id({self.id}), user_id({self.user_id}), signal({self.signal_id}), rating({self.rating}), tx_hash({self.tx_hash}), date_placed {self.date_created})"

    def format(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "signal_id": self.signal_id,
            "tx_hash": self.tx_hash,
            "rating": self.rating,
            "date_created": self.date_created,
        }
