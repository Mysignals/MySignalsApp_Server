from flask import Flask, jsonify, session
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_cors import CORS
from flask_migrate import Migrate

from config import App_Config

app = Flask(__name__)
app.config.from_object(App_Config)
CORS(app)
bcrypt = Bcrypt(app)


@app.route("/")
def home():
    return "hello world"



if __name__ == "__main__":
    app.debug = True
    app.run()
