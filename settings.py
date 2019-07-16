from flask import Flask
from flask_marshmallow import Marshmallow
import jwt
from flask_login import LoginManager


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\Users\\INTEL\\PycharmProjects\\Rest\\database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'keyfortoken'

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.init_app(app)
ma = Marshmallow(app)