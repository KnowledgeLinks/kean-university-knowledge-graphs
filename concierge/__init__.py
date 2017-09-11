__author__ = "Jeremy Nelson"

import os

from flask import Flask

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')

from .views import *
