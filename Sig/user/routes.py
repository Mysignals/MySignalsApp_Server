from user.models import User
from flask import jsonify, request, Blueprint, session
from Sig.utils import query_one_filtered
from sig import bcrypt


user = Blueprint("user", url_prefix="/users")


@user.route("/register", methods=["POST"])
def register_user():
    data = request.get_json()
    user_name = data.get("user_name")
    email = data.get("email")
    password = data.get("password")
    confirm_password = data.get("confirm_password")

    if not (data and user_name and email and password and confirm_password):
        return (
            jsonify({"error": "Bad Request", "message": "Did you provide all fields?"}),
            304,
        )

    if password != confirm_password:
        return (
            jsonify({"error": "Bad Request", "message": "Passwords do not match"}),
            304,
        )

    if query_one_filtered(user_name=user_name) or query_one_filtered(email=email):
        return (
            jsonify(
                {"error": "Conflict", "message": "User_name or email already exists"}
            ),
            304,
        )

    user = User(
        user_name=user_name,
        email=email,
        password=bcrypt.generate_password_hash(password),
    )
    user.insert()
    return jsonify(
        {"message": "Success", "user_name": user.user_name, "email": user.email}, 200
    )


@user.route("/login", methods=["POST"])
def login_user():
    data = request.get_json()
    user_name_or_mail = data.get("user_name_or_mail")
    password = data.get("password")

    if not (data and user_name_or_mail and password):
        return jsonify(
            {"error": "Bad Request", "message": "Did you provide all fields?"}, 304
        )

    user = query_one_filtered(user_name=user_name_or_mail)
    if not user or not bcrypt.check_password_hash(user.password, password):
        user = query_one_filtered(email=user_name_or_mail)
        if not user or not bcrypt.check_password_hash(user.password, password):
            return jsonify(
                {"error": "Unauthorized", "message": "Incorrect username or password"},
                401,
            )

        session["user"] = user.id
        return jsonify({"message": "Success", "user_name": user.user_name}, 200)
    session["user"] = user.id
    return jsonify(
        {
            "message": "Success",
            "user_name": user.user_name,
        },
        200,
    )


@user.route("/logout", methods=["GET"])
def logout_user():
    session.pop("user", None)
    return jsonify(
        {
            "message": "Success",
        },
        200,
    )
