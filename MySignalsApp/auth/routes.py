from flask import jsonify, request, Blueprint, session
from cryptography.fernet import Fernet
from MySignalsApp.models import User
from pydantic import ValidationError
from MySignalsApp import bcrypt, db
from MySignalsApp.schemas import (
    RegisterSchema,
    StringQuerySchema,
    LoginSchema,
    ValidEmailSchema,
    ResetPasswordSchema,
    UpdateKeysSchema,
)
from MySignalsApp.utils import (
    query_one_filtered,
    verify_reset_token,
    send_email,
)
import os


auth = Blueprint("auth", __name__, url_prefix="/auth")


KEY = os.getenv("FERNET_KEY")

kryptr = Fernet(KEY.encode("utf-8"))


@auth.route("/register", methods=["POST"])
def register_user():
    data = request.get_json()

    try:
        data = RegisterSchema(**data)
        if query_one_filtered(User, user_name=data.user_name) or query_one_filtered(
            User, email=data.email
        ):
            return (
                jsonify(
                    {
                        "error": "Conflict",
                        "message": "User_name or email already exists",
                    }
                ),
                403,
            )
        user = User(
            user_name=data.user_name,
            email=data.email,
            password=bcrypt.generate_password_hash(data.password).decode("utf-8"),
            api_key=kryptr.encrypt(data.api_key.encode("utf-8")).decode("utf-8"),
            api_secret=kryptr.encrypt(data.api_secret.encode("utf-8")).decode("utf-8"),
        )
        user.insert()
        send_email(user, "auth.activate_user")
        return (
            jsonify(
                {"message": "Success", "user_name": user.user_name, "email": user.email}
            ),
            201,
        )
    except ValidationError as e:
        msg = ""
        for err in e.errors():
            msg += f"{str(err.get('loc')).strip('(),')}:{err.get('msg')}, "
        return (
            jsonify({"error": "Bad Request", "message": msg}),
            400,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "User not registered, It's not you it's us",
                }
            ),
            500,
        )


@auth.route("/activate/<string:token>")
def activate_user(token):
    try:
        token = StringQuerySchema(token=token)
    except ValidationError as e:
        msg = ""
        for err in e.errors():
            msg += f"{str(err.get('loc')).strip('(),')}:{err.get('msg')}, "
        return (
            jsonify({"error": "Bad Request", "message": msg}),
            400,
        )
    user = verify_reset_token(User, token.token)
    if user:
        user.is_active = True
        try:
            user.update()
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
        except Exception as e:
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
                "error": "Unauthorized",
                "message": "Token is not valid or has already been used",
            }
        ),
        404,
    )


@auth.route("/login", methods=["POST"])
def login_user():
    data = request.get_json()
    try:
        data = LoginSchema(**data)
        user = query_one_filtered(User, user_name=data.user_name_or_mail)
        if not user or not bcrypt.check_password_hash(user.password, data.password):
            user = query_one_filtered(User, email=data.user_name_or_mail)
            if not user or not bcrypt.check_password_hash(user.password, data.password):
                return (
                    jsonify(
                        {
                            "error": "Unauthorized",
                            "message": "Incorrect username or password",
                        },
                    ),
                    401,
                )

            session["user"] = {"id": user.id, "permission": user.roles.value}
            return (
                jsonify(
                    {
                        "message": "Success",
                        "user_name": user.user_name,
                        "is_active": user.is_active,
                        "permission": user.roles.value,
                    },
                ),
                200,
            )
        session["user"] = {"id": user.id, "permission": user.roles.value}
        return (
            jsonify(
                {
                    "message": "Success",
                    "user_name": user.user_name,
                    "is_active": user.is_active,
                    "permission": user.roles.value,
                },
            ),
            200,
        )
    except ValidationError as e:
        msg = ""
        for err in e.errors():
            msg += f"{str(err.get('loc')).strip('(),')}:{err.get('msg')}, "
        return (
            jsonify({"error": "Bad Request", "message": msg}),
            400,
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


@auth.route("/reset_password")
def reset_request():
    data = request.get_json()
    try:
        data = ValidEmailSchema(**data)

        user = query_one_filtered(User, email=data.email)
        if user:
            send_email(user, "auth.reset_token")

            return (
                jsonify(
                    {
                        "message": f"Reset password token will be sent to {data.email} if they exist"
                    }
                ),
                200,
            )
        return (
            jsonify(
                {
                    "message": f"Reset password token will be sent to {data.email} if they exist"
                }
            ),
            404,
        )
    except ValidationError as e:
        msg = ""
        for err in e.errors():
            msg += f"{str(err.get('loc')).strip('(),')}:{err.get('msg')}, "
        return (
            jsonify({"error": "Bad Request", "message": msg}),
            400,
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


@auth.route("/reset_password/<string:token>", methods=["POST"])
def reset_password(token):
    data = request.get_json()
    try:
        data = ResetPasswordSchema(token=token, **data)

        user = verify_reset_token(User, data.token)
        if user:
            user.password = bcrypt.generate_password_hash(data.password)
            user.update()
            session.pop("user", None)
            return jsonify({"message": "Password changed"}), 200

        return jsonify({"error": "Unauthorized", "message": "Invalid token"}), 400
    except ValidationError as e:
        msg = ""
        for err in e.errors():
            msg += f"{str(err.get('loc')).strip('(),')}:{err.get('msg')}, "
        return (
            jsonify({"error": "Bad Request", "message": msg}),
            400,
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


@auth.route("/logout", methods=["GET", "POST"])
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


@auth.route("/@me")
def see_sess():
    user = session.get("user")

    if not user:
        return (
            jsonify({"error": "Unauthorized", "message": "You are not logged in"}),
            401,
        )
    try:
        user = query_one_filtered(User, id=user["id"])
        return jsonify(
            {
                "message": "Success",
                "email": user.email,
                "user_name": user.user_name,
                "is_active": user.is_active,
                "roles": user.roles.value,
                "created_on": user.date_created,
            }
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


@auth.route("/update_keys", methods=["POST"])
def update_keys():
    user_id = session.get("user")
    if not user_id:
        return (
            jsonify({"error": "Unauthorized", "message": "You are not logged in"}),
            401,
        )

    data = request.get_json()
    try:
        data = UpdateKeysSchema(**data)

        user = query_one_filtered(User, id=user_id)
        if not user:
            return (
                jsonify(
                    {"error": "Resource not found", "message": "User does not exist"}
                ),
                404,
            )
        user.api_key = kryptr.encrypt(data.api_key.encode("utf-8")).decode("utf-8")
        user.api_secret = kryptr.encrypt(data.api_secret.encode("utf-8")).decode(
            "utf-8"
        )
        user.update()
        return jsonify(
            {
                "message": "success",
                "user_name": user.user_name,
                "is_active": user.is_active,
            }
        )
    except ValidationError as e:
        msg = ""
        for err in e.errors():
            msg += f"{str(err.get('loc')).strip('(),')}:{err.get('msg')}, "
        return (
            jsonify({"error": "Bad Request", "message": msg}),
            400,
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
