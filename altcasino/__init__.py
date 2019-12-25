import psycopg2
import urllib
import pymongo
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import time
import random
import json
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from altcasino.fetch import *
from flask_socketio import SocketIO, send, emit, disconnect, join_room, leave_room
import eventlet

# yapf: disable
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = ''
app.config['SQLALCHEMY_DATABASE_URI'] = ''
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True, "pool_recycle": 300}
app.config['RECAPTCHA_PUBLIC_KEY']=''
app.config['RECAPTCHA_PRIVATE_KEY']=''
app.config['RECAPTCHA_OPTIONS'] = dict(
    theme='custom',
    custom_theme_widget='recaptcha_widget'
)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app)

from altcasino.models import load_user
from altcasino import routes

# yapf: enable