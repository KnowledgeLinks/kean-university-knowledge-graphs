__author__ = "Jeremy Nelson"

from flask import Flask

app = Flask(__name__)

from .views import *
