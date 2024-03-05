from MySignalsApp.models.base import BaseModel
from MySignalsApp import db


class ProviderApplication(BaseModel):
    __tablename__ = "providerapplications"
    id = db.Column(db.Integer(), primary_key=True, unique=True, nullable=False)
    user_id = db.Column(
        db.String(34), db.ForeignKey("users.id"), unique=True, nullable=False
    )
    user = db.Relationship("User", back_populates="provider_application", lazy=True)
    wallet = db.Column(db.String(42), nullable=False)
    experience = db.Column(db.String(300), nullable=False)
    socials_and_additional = db.Column(db.String(500), nullable=False)

    def __init__(self, user_id, wallet, experience, socials_and_additional):
        self.user_id = user_id
        self.wallet = wallet
        self.experience = experience
        self.socials_and_additional = socials_and_additional

    def __repr__(self):
        return f"username({self.user.user_name}, wallet({self.wallet}), experience({self.experience}))"

    def format(self):
        return {
            "id": self.id,
            "user": self.user.user_name,
            "wallet": self.wallet,
            "experience": self.experience,
            "socials_and_additional": self.socials_and_additional,
            "date_created": self.date_created,
        }
