from flask import jsonify, request,Blueprint


main= Blueprint("main", __name__)

@main.route("/")
def home():
    return "Hello World!"



