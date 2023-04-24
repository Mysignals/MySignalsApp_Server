from Sig import db


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
