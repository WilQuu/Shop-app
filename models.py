from app import db
from flask_login import UserMixin

class Users(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), unique=True)

    email = db.Column(db.String(50), unique=True)

    password = db.Column(db.String(256), unique=False)

    def __init__(self, username=None, email=None, password=None):
        self.username = username
        self.email = email
        self.password = password
