from MySignalsApp import db
from datetime import datetime, timedelta, timezone


# def lazy_utc_now():
#     return datetime.now(tz=timezone.utc) + timedelta(hours=2)


class UserTokens(db.Model):
    __tablename__ = "usertokens"

    id = db.Column(db.Integer(), primary_key=True, unique=True, nullable=False)
    user_id = db.Column(db.String(), db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(), nullable=False, unique=True)
    expiration = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(tz=timezone.utc) + timedelta(hours=2),
    )

    def __init__(self, user_id, token):
        self.user_id = user_id
        self.token = token

    def __repr__(self):
        return f"id({self.id}), user_id({self.user_id}), token({self.token}), expiration {self.expiration})"

    def insert(self):
        """Insert the current object into the database"""
        db.session.add(self)
        db.session.commit()

    def update(self):
        """Update the current object in the database"""
        db.session.commit()

    def delete(self):
        """Delete the current object from the database"""
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "token": self.token,
            "expiration": self.expiration,
        }
