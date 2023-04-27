from Sig import db
from uuid import uuid4
from datetime import datetime
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
    api_key = db.Column(db.String(160), nullable=True)
    is_active = db.Column(db.Boolean(), nullable=False, default=False)
    roles = db.Column(db.Enum(Roles), nullable=False, default=Roles.USER)
    date_registered = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, user_name, email, password, roles=Roles.USER, api_key=None):
        self.user_name = user_name
        self.email = email
        self.password = password
        self.roles = roles
        self.api_key = api_key

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
