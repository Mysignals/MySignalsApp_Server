from MySignalsApp.models.base import BaseModel
from MySignalsApp import db, admin
from flask import session, flash, redirect
from flask_admin.contrib.sqla import ModelView


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


class PlacedSignalsModelView(ModelView):
    def is_accessible(self):
        user = session.get("user") if session else None
        return "Registrar" in user.get("permission") if user else False

    # def _handle_view(self, name, **kwargs):
    #     print(self.is_accessible())
    #     if not self.is_accessible():
    #         return self.render("admin/login.html")
    #     else:
    #         return self.render("admin/index.html")

    def inaccessible_callback(self, name, **kwargs):
        flash("you are not authorized", category="error")
        return redirect("/admin/login", 302)

    can_create = True
    column_searchable_list = ["user_id", "signal_id"]
    column_filters = ["user_id", "signal_id", "rating"]
    column_list = (
        "id",
        "user_id",
        "user",
        "signal_id",
        "signal",
        "rating",
        "date_created",
    )
    form_columns = ("user_id", "signal_id", "rating", "date_created")


admin.add_view(PlacedSignalsModelView(PlacedSignals, db.session))
