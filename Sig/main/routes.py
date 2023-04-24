from flask import jsonify, request, Blueprint, session


main = Blueprint("main", __name__)


@main.route("/")
def home():
    return "Hello World!"
