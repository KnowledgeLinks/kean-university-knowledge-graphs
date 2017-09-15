__author__ = "Jeremy Nelson"

import jwt
from . import app
from flask import abort, jsonify
from flask import current_app, request, session
from ldap3 import Server, Connection, ALL

server = Server(app.config.get('LDAP_HOST'), 
                get_info=ALL, 
                use_ssl=True)

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
             app.config.get('LDAP_STAFF_DN').format(username),
             password=password)
    return conn.bind()


def login_required(f):
    def decorator(*args, **kwargs):
        token = request.form.get('token')
        if token is None:
            abort(400)
        try:
            user_info = jwt.decode(token, 
                                   app.config.get("SECRET_KEY"),
                                   algorithm='HS256')
        except jwt.exceptions.DecodeError:
            abort(403)
        is_valid = __auth__(user_info) 
        if is_valid is True:
            return f(*args, **kwargs)
        else:
            return abort(403)
    return decorator
       
@app.errorhandler(400)
def bad_request(e):
    return jsonify({"status": 400,
                    "message": "Bad Request; missing parameters"}), 400
 
@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"status": 401,
                    "message": "Invalid authentication"}), 401



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
    user_info = {"username": username,
                 "password": password}
    is_valid = __auth__(user_info)
    if is_valid is True:
        token = jwt.encode(user_info,
                           app.config.get('SECRET_KEY'),
                           algorithm='HS256')
        return jsonify({"message": "Logged in".format(username),
                        "token": token.decode()})
    else:
        failed_authenticate = jsonify({
            "status": 403,
            "message": "failed authentication"})
        failed_authenticate.status_code = 403
        return failed_authenticate

@app.route("/search", methods=["GET", "POST"])
@login_required
def catalog_search():
    """Searches Elasticsearch Index of BF 2.0 RDF for Kean"""
    if request.method.startswith("POST"):
        token = request.form.get("token")
        query = request.form.get('query')
    else:
        token = request.args.get("token")
        query = request.args.get("query")
    search_results = []
    return jsonify({"message": "Success",
                    "query": query,
                    "results": search_results})

@app.route("/feed", methods=["GET"])
@login_required
def news_feed():
    

@app.route("/")
def home():
    return jsonify({"about": "Kean Concierge API"})
