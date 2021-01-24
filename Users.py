from sqlalchemy.testing import db


class User(db.Model):

    __tablename__ = 'usertable'

    id = db.Column(db.Integer, primary_key=True)

    name= db.Column(db.String(15), unique=True)

    username = db.Column(db.String(15), unique=True)

    email = db.Column(db.String(50), unique=True)

    password = db.Column(db.String(256), unique=True)