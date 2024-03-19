from flask_admin import BaseView, expose
from MySignalsApp import db, admin, bcrypt
from flask_admin.contrib.sqla import ModelView
from wtforms import EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
from flask import session, redirect, flash
from MySignalsApp.utils import query_one_filtered
from MySignalsApp.models.users import User
from MySignalsApp.models.signals import Signal
from MySignalsApp.models.provider_application import ProviderApplication
from MySignalsApp.models.placed_signals import PlacedSignals
from MySignalsApp.models.notifications import Notification
from flask_wtf import FlaskForm


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
    column_searchable_list = ["user_name", "email", "referrers_code"]
    column_filters = ["is_active", "roles", "referrers_code"]
    column_list = (
        "id",
        "user_name",
        "email",
        "wallet",
        "is_active",
        "roles",
        "referral_code",
        "referrer",
        "referrers_code",
        "date_created",
    )
    form_columns = (
        "user_name",
        "email",
        "wallet",
        "is_active",
        "referrer",
        "roles",
        "date_created",
    )


class SignalModelView(ModelView):
    def is_accessible(self):
        user = session.get("user") if session else None
        return "Registrar" in user.get("permission") if user else False

    def inaccessible_callback(self, name, **kwargs):
        flash("you are not authorized", category="error")
        return redirect("/admin/login", 302)

    can_create = False
    column_searchable_list = ["provider"]
    column_filters = ["user", "is_spot", "status"]
    column_list = (
        "id",
        "signal",
        "is_spot",
        "status",
        "user",
        "short_text",
        "date_created",
    )
    form_columns = ("signal", "status", "user", "short_text", "date_created")


class ProviderApplicationView(ModelView):
    def is_accessible(self):
        user = session.get("user") if session else None
        return "Registrar" in user.get("permission") if user else False

    def inaccessible_callback(self, name, **kwargs):
        flash("You are not Authorized", category="error")
        return redirect("/admin/login", 302)

    column_list = [
        "id",
        "user",
        "user.user_name",
        "wallet",
        "experience",
        "socials_and_additional",
        "date_created",
    ]
    form_columns = [
        "user",
        "wallet",
        "experience",
        "socials_and_additional",
        "date_created",
    ]
    column_searchable_list = ["user_id", "user.user_name", "wallet"]
    column_filters = ["date_created"]


class PlacedSignalsModelView(ModelView):
    def is_accessible(self):
        user = session.get("user") if session else None
        return "Registrar" in user.get("permission") if user else False

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
        "tx_hash",
        "rating",
        "date_created",
    )
    form_columns = ("user", "signal_id", "rating", "date_created")


class NotificationsModelView(ModelView):
    def is_accessible(self):
        user = session.get("user") if session else None
        return "Registrar" in user.get("permission") if user else False

    def inaccessible_callback(self, name, **kwargs):
        flash("you are not authorized", category="error")
        return redirect("/admin/login", 302)

    can_create = True
    column_searchable_list = ["user_id", "message"]
    column_filters = ["user_id", "user", "date_created"]
    column_list = (
        "id",
        "user_id",
        "user",
        "message",
        "date_created",
    )
    form_columns = ("user", "message", "date_created")


# admin.add_view(AdminLoginView(endpoint="login", name="login"))
# admin.add_view(AdminLogoutView(endpoint="logout", name="logout"))
# admin.add_view(UserModelView(User, db.session))
# admin.add_view(ProviderApplicationView(ProviderApplication, db.session))
# admin.add_view(SignalModelView(Signal, db.session))
# admin.add_view(PlacedSignalsModelView(PlacedSignals, db.session))
model_views = [
    AdminLoginView(endpoint="login", name="login"),
    AdminLogoutView(endpoint="logout", name="logout"),
    UserModelView(User, db.session),
    ProviderApplicationView(ProviderApplication, db.session),
    SignalModelView(Signal, db.session),
    PlacedSignalsModelView(PlacedSignals, db.session),
    NotificationsModelView(Notification, db.session),
]
