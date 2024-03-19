from MySignalsApp.models.base import BaseModel
from MySignalsApp import db


class Notification(BaseModel):
    __tablename__ = "notifications"

    id = db.Column(db.Integer(), primary_key=True, unique=True, nullable=False)
    user_id = db.Column(
        db.String(34), db.ForeignKey("users.id"), index=True, nullable=False
    )
    message = db.Column(db.String(210), nullable=False)

    def __init__(self, user_id, message):
        self.user_id = user_id
        self.message = message

    def __repr__(self):
        return f"id({self.id}), user_name({self.user.user_name}),user_id({self.user_id}),message({self.message}), date_created({self.date_created})) \n"

    def __str__(self):
        return f"{self.message}"

    def format(self):
        return {
            "id": self.id,
            "message": self.message,
            "user": self.user.user_name,
            "date_created": self.date_created,
        }
