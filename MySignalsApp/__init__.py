from flask import Flask, session
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_cors import CORS
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from MySignalsApp.config import App_Config

db = SQLAlchemy()

bcrypt = Bcrypt()

sess = Session()
mail = Mail()


def create_app(config_class=App_Config):
    """
    Create a new instance of the app with the given configuration.

    :param config_class: configuration class
    :return: app
    """
    # Initialize Flask-
    app = Flask(__name__)
    app.config["SESSION_SQLALCHEMY"] = db
    app.config.from_object(App_Config)
    # Initialize CORS
    CORS(app)
    # Initialize SQLAlchemy
    db.init_app(app)
    # Initialize Flask-Mail
    mail.init_app(app)
    # Initialize Bcrypt
    bcrypt.init_app(app)
    # Initialize Flask-Session
    sess.init_app(app)
    migrate = Migrate(app, db)

    from MySignalsApp.main.routes import main
    from MySignalsApp.auth.routes import auth
    from MySignalsApp.provider.routes import provider
    from MySignalsApp.registrar.routes import registrar
    from MySignalsApp.errors.handlers import error

    app.register_blueprint(main)
    app.register_blueprint(auth)

    app.register_blueprint(provider)
    app.register_blueprint(registrar)
    app.register_blueprint(error)

    with app.app_context():
        db.create_all()

    return app
