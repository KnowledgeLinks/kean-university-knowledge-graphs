__author__ = "Jeremy Nelson"

from . import app
from flask import abort, jsonify
from flask import current_app, request, session
from flask_login import login_required, login_user, logout_user, current_user
from flask_ldap3_login import LDAP3LoginManager

from .patrons import Student, Staff, Faculty

ldap_manager = LDAP3LoginManager()
ldap_manager.init_config(app.config)

@app.route("/login", methods=['POST'])
def login():
    """Login Method """
    username = request.form.get("username")
    password = request.form.get("password")
    if username is None or password is None:
        error_response = jsonify(
            {"status": 500,
             "message": "username or password cannot be blank"})
        error_response.status_code = 500
        return error_response
    check_user = ldap_manager.authenticate(username, password)
    if check_user.status is True:
        login_user(Student(username=username, password=password))
        return jsonify({"message": "Logged in".format(username)})
    else:
        failed_authenticate = jsonify({
            "status": 403,
            "message": "failed authentication"})
        failed_authenticate.status_code = 403
        return failed_authenticate

@app.route("/logout", methods=['GET', 'POST'])
def logout():
    """Logout method"""
    logout_user()
    return jsonify({"message": "Logged out Kean Concierge API"})

@app.route("/search", methods=["GET", "POST"])
@login_required
def catalog_search():
    """Searches Elasticsearch Index of BF 2.0 RDF for Kean"""
    query = request.form.get('query')
    search_results = []
    return jsonify({"message": "Searched on {}".format(query),
                    "results": search_results})

@app.route("/")
def home():
    return jsonify({"about": "Kean Concierge API"})
