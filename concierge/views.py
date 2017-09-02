__author__ = "Jeremy Nelson"

from bs4 import BeautifulSoup
from . import app
from flask import jsonify, render_template
from flask import current_app, request
from flask_ldap3_login import LDAP3LoginManager

ldap_manager = LDAP3LoginManager()

@app.route("/login", methods=['POST'])
def login():
    """Login Method """
    username = request.form.get("username")
    return jsonify({"username": username})
    

@app.route("/")
def home():
    return jsonify({"about": "Kean Concierge API"})
