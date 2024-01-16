from flask_admin import BaseView, expose
from MySignalsApp import db, admin, bcrypt
from MySignalsApp.models.base import BaseModel
from MySignalsApp.models.notifications import Notification
from flask_admin.contrib.sqla import ModelView
from wtforms import EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
from flask import session, redirect, flash
from MySignalsApp.utils import query_one_filtered
from flask_wtf import FlaskForm
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


class AdminForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class AdminLoginView(BaseView):
    @expose("/", methods=["GET", "POST"])
    def admin_form_login(self):
        form = AdminForm()

        if form.validate_on_submit():
            email, password = form.email.data, form.password.data
            if not email or not password:
                flash("One or more missing fields", category="error")
                return redirect("/admin/login", 302)
            user = query_one_filtered(User, email=email)
            if not user or not bcrypt.check_password_hash(user.password, password):
                flash("Incorrect email or password", category="error")
                return redirect("/admin/login", 302)

            session["user"] = {"id": user.id, "permission": user.roles.value}
            return redirect("/admin", 302)
        return self.render("admin/login.html", form=form)


class AdminLogoutView(BaseView):
    @expose("/")
    def logout_admin(self):
        session.pop("user", None)
        return redirect("/admin/login", 302)


class UserModelView(ModelView):
    def is_accessible(self):
        user = session.get("user") if session else None
        return "Registrar" in user.get("permission") if user else False

    # def _handle_view(self, name, **kwargs):
    #     print(self.is_accessible())
    #     if not self.is_accessible():
    #         return redirect("admin/login")
    #     else:
    #         return redirect("admin/user")

    def inaccessible_callback(self, name, **kwargs):
        flash("You are not Authorized", category="error")
        return redirect("/admin/login", 302)

    can_create = False
    can_delete = False
    column_searchable_list = ["user_name", "email"]
    column_filters = ["is_active", "roles"]
    column_list = (
        "id",
        "user_name",
        "email",
        "wallet",
        "is_active",
        "roles",
        "date_created",
    )
    form_columns = (
        "user_name",
        "email",
        "wallet",
        "is_active",
        "roles",
        "date_created",
    )


admin.add_view(UserModelView(User, db.session))
admin.add_view(AdminLoginView(endpoint="login", name="login"))
admin.add_view(AdminLogoutView(endpoint="logout", name="logout"))
