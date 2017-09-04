__author__ = "Jeremy Nelson"

import os

from flask import Flask
from flask_login import LoginManager



app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
login_manager = LoginManager(app)

from .views import *
