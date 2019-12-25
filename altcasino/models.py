from altcasino import db, login_manager
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy
import uuid
from uuid import uuid4
from flask_login import UserMixin

from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    print(user_id)
    return User.query.get(user_id)


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    balance = db.Column(db.REAL, nullable=False, default=0.0)
    address = db.Column(db.String(), unique=True, nullable=True)
    withdrawals = db.relationship('Withdraw', backref='withdrew', lazy=True)
    deposits = db.relationship('Deposit', backref='deposited', lazy=True)


    def __repr__(self):
        return f"User('{self.id}', '{self.username}', '{self.email}', '{self.password}', '{self.balance}', '{self.address}', '{self.deposits}', '{self.withdrawals}')"


class Withdraw(db.Model):
    __tablename__ = "withdraws"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    amount = db.Column(
        db.REAL,
        nullable=False,
    )
    user_id = db.Column(db.String,
                        db.ForeignKey('users.username'),
                        nullable=False)

    def __repr__(self):
        return f"Withdraw('{self.date}', '{self.amount}')"


class Deposit(db.Model):
    __tablename__ = "deposits"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    amount = db.Column(
        db.REAL,
        nullable=False,
    )
    user_id = db.Column(db.String,
                        db.ForeignKey('users.username'),
                        nullable=False)

    def __repr__(self):
        return f"Deposit('{self.date}', '{self.amount}')"


class Card(object):
    def __init__(self, value, suit):
        self.value = value
        self.suit = suit
        pass