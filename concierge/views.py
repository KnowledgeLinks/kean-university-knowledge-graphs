__author__ = "Jeremy Nelson"

import json
import os

from functools import wraps
import jwt
import requests

from . import app
from .es_views import api_instructions, get_lookup_list, get_lookup_item
from flask import abort, jsonify
from flask import current_app, request, session
from ldap3 import Server, Connection, ALL

server = Server(app.config.get('LDAP_HOST'),
                get_info=ALL,
                use_ssl=True)

COLLEAGUE_LOGIN_URL = "{}/session/login".format(
    app.config.get("COLLEAGUE_BASE_URL"))
COLLEAGUE_PROGRAM_TMPLATE = "{}/students/{{}}/programs".format(
    app.config.get("COLLEAGUE_BASE_URL"))

CONCIERGE_BASE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(CONCIERGE_BASE, "static/js/programs.json")) as fo:
    PROGRAMS = json.load(fo)


def __auth__(user):
    """Internal function takes a user dict and
    returns a dictionary with a token or raises a 401
    error.

    Args:
        user(dict): User creditials
    """
    conn = Connection(server,
                      app.config.get('LDAP_STUDENT_DN').format(
                          user.get("username")),
                      password=user.get("password"))
    if conn.bind() is False:
         # Tries to authenticate as staff
         conn = Connection(server,
             app.config.get('LDAP_STAFF_DN').format(user.get("username")),
             password=user.get('password'))
    return conn

def __get_employee_number__(user_info, conn=None):
    """ searches LDAP for the employee number

    Args:
        conn: the LDAP connection instance
        user_info: the username and password
    """
    if not conn:
        conn = __auth__(user_info)
    has_employee_number = conn.search(
        app.config.get("LDAP_SEARCH_BASE"),
        "(uid={0})".format(user_info.get("username")),
        attributes=["employeeNumber"])
    program_name = "Unknown"
    if has_employee_number is True:
        session['employee_number'] = conn.entries[0].employeeNumber.value
        return conn.entries[0].employeeNumber.value
    return None

def __program_info__(user_info):
    # Retrieve major information from Colleague API
    program_name = "Unknown"
    if session.get('program_name'):
      return session['program_name']
    employee_number = session.get("employee_number")
    if not employee_number:
        employee_number = __get_employee_number__(user_info)
    if employee_number:
        colleague_user = {"UserId": app.config.get("COLLEAGUE_USER_ID"),
                          "Password": app.config.get("COLLEAGUE_USER_PWD")}
        colleague_login = requests.post(
             COLLEAGUE_LOGIN_URL,
             data=colleague_user)
        if colleague_login.status_code != 200:
             raise ValueError("Did not login successfully to Colleague")
        token = colleague_login.text
        # Now search Colleague API for program
        program_info_url = COLLEAGUE_PROGRAM_TMPLATE.format(
             employee_number)
        program_result = requests.get(program_info_url,
            headers={"X-CustomCredentials": token,
                     "Accept": "application/vnd.ellucian.v1+json",
                     "Content-Type": "application/json"})
        if program_result.status_code < 400:
            program_info = program_result.json()
            if len(program_info) > 0:
                program_code = program_info[0].get("ProgramCode")
                program_name = PROGRAMS.get(program_code)
    session['program_name'] = program_name
    return program_name

def kean_required(f):
    @wraps(f)
    def __decorator__(*args, **kwargs):
        token = request.form.get('token')
        if token is None:
            abort(400)
        # if the session token and passed in token match continue
        if session.get('token') == token:
            return f(*args, **kwargs)
        # if sesion info did not work try the LDAP connection
        session.clear()
        try:
            user_info = jwt.decode(token,
                                   app.config.get("SECRET_KEY"),
                                   algorithm='HS256')
        except jwt.exceptions.DecodeError:
            abort(403)
        connection = __auth__(user_info)
        if connection.bind() is False:
            return abort(403)
        else:
            session['token'] = token
            return f(*args, **kwargs)
    return __decorator__

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"status": 400,
                    "message": "Bad Request; missing parameters"}), 400

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"status": 401,
                    "message": "Invalid authentication"}), 401


@app.route("/doc")
def doc_home():
    return api_instructions()

@app.route("/work/<work_id>", methods=["GET", "POST"])
@kean_required
def work_detail(work_id=None):
    """Returns detailed JSON for an individual ES document"""
    if work_id is None:
        if request.method.startswith("POST"):
            work_id = request.form.get('id')
        else:
            work_id = request.args.get('id')
    detail_info = get_lookup_item("catalog",
                                  "work",
                                  id=work_id)
    return detail_info

@app.route("/login", methods=['POST'])
def login():
    """Login Method """
    session.clear()
    username = request.form.get("username")
    password = request.form.get("password")
    if username is None or password is None:
        error_response = jsonify(
            {"status": 500,
             "message": "username or password cannot be blank"})
        error_response.status_code = 500
        return error_response
    user_info = {"username": username,
                 "password": password}
    connection = __auth__(user_info)
    if connection.bind() is True:
        token = jwt.encode(user_info,
                           app.config.get('SECRET_KEY'),
                           algorithm='HS256')
        session['token'] = token.decode()
        __get_employee_number__(user_info, connection)
        return jsonify({"message": "Logged in".format(username),
                        "token": token.decode()})
                        #"program": __program_info__(connection, user_info)})
    else:
        failed_authenticate = jsonify({
            "status": 403,
            "message": "failed authentication"})
        failed_authenticate.status_code = 403
        return failed_authenticate

@app.route("/program", methods=['POST'])
@kean_required
def student_program():
    token = request.form.get("token")
    try:
        user_info = jwt.decode(token,
                               app.config.get("SECRET_KEY"),
                               algorithm='HS256')
    except jwt.exceptions.DecodeError:
        abort(403)
    return jsonify({"program": __program_info__(user_info),
                    "username": user_info.get('username')})

@app.route("/search", methods=["GET", "POST"])
@kean_required
def catalog_search():
    """Searches Elasticsearch Index of BF 2.0 RDF for Kean"""
    if request.method.startswith("POST"):
        token = request.form.get("token")
        query = request.form.get('query')
        size = request.form.get("size", 10)
        offset = request.form.get("offset", 0)
    else:
        token = request.args.get("token")
        query = request.args.get("query")
        size = request.form.get("size", 10)
        offset = request.args.get("offset", 0)
    search_results = get_lookup_list("catalog",
                                     "work",
                                     term=query,
                                     size=size,
                                     offset=offset)
    return jsonify({"message": "Success",
                    "query": query,
                    "results": search_results})

@app.route("/feed", methods=["GET"])
@kean_required
def news_feed():
    return jsonify({"message": "News Feed"})


@app.route("/")
def home():
    return jsonify({"about": "Kean Concierge API"})
