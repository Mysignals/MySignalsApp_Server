from Sig.user.models import User
from flask import jsonify, request, Blueprint, session
from Sig.utils import (
    query_one_filtered,
    get_reset_token,
    verify_reset_token,
    send_email,
)
from Sig import bcrypt, db
import sys


user = Blueprint("user", __name__, url_prefix="/users")


@user.route("/register", methods=["POST"])
def register_user():
    data = request.get_json()
    user_name = str(data.get("user_name"))
    email = str(data.get("email"))
    password = data.get("password")
    confirm_password = data.get("confirm_password")

    if not (data and user_name and email and password and confirm_password):
        return (
            jsonify({"error": "Bad Request", "message": "Did you provide all fields?"}),
            400,
        )

    if password != confirm_password:
        return (
            jsonify({"error": "Bad Request", "message": "Passwords do not match"}),
            400,
        )

    user_name=user_name.lower()

    if query_one_filtered(User, user_name=user_name) or query_one_filtered(
        User, email=email
    ):
        return (
            jsonify(
                {"error": "Conflict", "message": "User_name or email already exists"}
            ),
            403,
        )

    user = User(
        user_name=user_name,
        email=email,
        password=bcrypt.generate_password_hash(password).decode("utf-8"),
    )
    try:
        send_email(user, "user.activate_user")
        user.insert()
        
    except Exception as e:
        print(e)
        print(sys.exc_info())
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "User not registered, It's not you it's us",
                }
            ),
            500,
        )
    return (
        jsonify(
            {"message": "Success", "user_name": user.user_name, "email": user.email}
        ),
        200,
    )


@user.route("/activate/<string:token>")
def activate_user(token):
    user = verify_reset_token(User, token)
    if user:
        user.is_active = True
        try:
            user.update()
        except Exception as e:
            print(e)
            return (
                jsonify(
                    {
                        "error": "Internal server error",
                        "message": "User not activated, It's not you it's us",
                    }
                ),
                500,
            )
        return (
            jsonify(
                {
                    "message": "Success",
                    "user_name": user.user_name,
                    "is_active": user.is_active,
                }
            ),
            200,
        )

    return (
        jsonify(
            {
                "error": "Unauthorized",
                "message": "Token is not valid or has already been used",
            }
        ),
        404,
    )


@user.route("/login", methods=["POST"])
def login_user():
    data = request.get_json()
    user_name_or_mail = str(data.get("user_name_or_mail"))
    password = data.get("password")

    if not (data and user_name_or_mail and password):
        return (
            jsonify({"error": "Bad Request", "message": "Did you provide all fields?"}),
            400,
        )
    try:
        user = query_one_filtered(User, user_name=user_name_or_mail)
        if not user or not bcrypt.check_password_hash(user.password, password):
            user = query_one_filtered(User, email=user_name_or_mail)
            if not user or not bcrypt.check_password_hash(user.password, password):
                return (
                    jsonify(
                        {
                            "error": "Unauthorized",
                            "message": "Incorrect username or password",
                        },
                    ),
                    401,
                )

            session["user"] = {"id": user.id, "permission": ["user"]}
            return (
                jsonify(
                    {
                        "message": "Success",
                        "user_name": user.user_name,
                        "is_active": user.is_active,
                    },
                ),
                200,
            )
        session["user"] = {"id": user.id, "permission": ["user"]}
        return (
            jsonify(
                {
                    "message": "Success",
                    "user_name": user.user_name,
                    "is_active": user.is_active,
                },
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "It's not you it's us",
                }
            ),
            500,
        )


@user.route("/reset_password", methods=["POST"])
def reset_request():
    data = request.get_json()
    email = str(data.get("email"))
    user = query_one_filtered(User, email)
    if user:
        send_email(user, "reset_token")

        return (
            jsonify(
                {
                    "message": f"Reset password token will be sent to {email} if they exist"
                }
            ),
            200,
        )


@user.route("/reset_password/<string:token>", methods=["POST"])
def reset_token(token):
    data = request.get_json()
    password = data.get("password")
    password_confirm = data.get("password_confirm")
    if not password or not password_confirm:
        return (
            jsonify({"error": "Bad Request", "message": "Did you provide all fields?"}),
            400,
        )

    if password != confirm_password:
        return (
            jsonify({"error": "Bad Request", "message": "Passwords do not match"}),
            400,
        )
    user = verify_reset_token(User, token)
    if user:
        try:
            user.password = bcrypt.generate_password_hash(password)
            user.update()
            session.pop("user", None)
            return jsonify({"message": "Password changed"}), 200
        except Exception as e:
            return (
                jsonify(
                    {
                        "error": "Internal server error",
                        "message": "It's not you it's us",
                    }
                ),
                500,
            )

    return jsonify({"error": "Invalid token"}), 400


@user.route("/logout", methods=["GET", "POST"])
def logout_user():
    session.pop("user", None)
    return (
        jsonify(
            {
                "message": "Success",
            }
        ),
        200,
    )
