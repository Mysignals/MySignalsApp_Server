from Sig import db
from flask import current_app, url_for
from flask_mail import Message
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


# db helpers
def query_one_filtered(table, **kwargs):
    return db.session.execute(db.select(table).filter_by(**kwargs)).scalar_one_or_none()


def query_all_filtered(table, **kwargs):
    return db.session.execute(db.select(table).filter_by(**kwargs)).scalars().all()


def query_one(table):
    return db.session.execute(db.select(table)).scalar_one_or_none()


def query_all(table):
    return db.session.execute(db.select(table)).scalars().all()


def query_paginated(table, page):
    return db.paginate(
        db.select(table).order_by(table.date_posted.desc()), per_page=5, page=page
    )


def query_paginate_filtered(table, page, **kwargs):
    return db.paginate(
        db.select(table).filter_by(**kwargs).order_by(table.date_posted.desc()),
        per_page=5,
        page=page,
    )


# jwt helpers
def get_reset_token(user, expires_sec=1800):
    s = Serializer(current_app.config["SECRET_KEY"], expires_sec)
    return s.dumps({"user_id": user.id}).decode("utf-8")


def verify_reset_token(user, token):
    s = Serializer(current_app.config["SECRET_KEY"])
    try:
        user_id = s.loads(token)["user_id"]
    except:
        return None
    return query_one_filtered(User, id=user_id)


# Flask Mail helpers


def send_email(user, url_func):
    token = user.get_reset_token()
    msg = Message(
        "Secret Link Request", sender="noreply@demo.com", recipients=[user.email]
    )
    msg.body = f""" visit the following link
{url_for(url_func,token=token,_external=True)}

<p style="color: bisque;">If you did not make this request then simply ignore this email, no changes will be made</p>
"""
    mail.send(msg)
