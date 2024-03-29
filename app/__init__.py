"""Initialize app."""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from flask_migrate import Migrate
from whitenoise import WhiteNoise

app = Flask(__name__)
app.wsgi_app = WhiteNoise(app.wsgi_app, root='app/static/')
app.config.from_object(Config)


db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
# login_manager.init_app(app)
login_manager.login_view = 'login'


from app import models, routes, auth, cluster