__author__ = "Jeremy Nelson"

import jwt
from . import app
from flask import abort, jsonify
from flask import current_app, request, session
from ldap3 import Server, Connection, ALL

server = Server(app.config.get('LDAP_HOST'), 
                get_info=ALL, 
                use_ssl=True)

def login_required(f):
    def decorator(*args, **kwargs):
        token = kwargs.get("token")
        if token is None:
            abort(401)
        user_info = jwt.decode(token, 
                               app.config.get("SECRET_KEY"),
                               algorithm='HS256')
        conn = Connection(server, 
                          app.config.get('LDAP_STUDENT_DN').format(
                              user_info.get("username")),
                          password=user_info.get("password"))
        if conn.bind() is False:
            # Tries to authenticate as staff
            conn = Connection(server, 
                app.config.get('LDAP_STAFF_DN').format(username),
                password=password)
        if conn.bind() is True:
            return f(*args, **kwargs)
        else:
            return abort(401)
    return decorator
        

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
    conn = Connection(server, 
                      app.config.get('LDAP_STUDENT_DN').format(username),
                      password=password)
    # Try to authenticate with credentials as a student
    if conn.bind() is False:
        # Tries to authenticate as staff
        conn = Connection(server, 
                      app.config.get('LDAP_STAFF_DN').format(username),
                      password=password)
    if conn.bind() is True:
        token = jwt.encode({"username": username, 
                            "password": password},
                           app.config.SECRET_KEY,
                           algorithm='HS256')
        session['token'] = token
        return jsonify({"message": "Logged in".format(username),
                        "token": token})
    else:
        failed_authenticate = jsonify({
            "status": 403,
            "message": "failed authentication"})
        failed_authenticate.status_code = 403
        return failed_authenticate

@app.route("/logout", methods=['GET', 'POST'])
def logout():
    """Logout method"""
    if "token" in session:
        session.pop("token")
    return jsonify({"message": "Logged out Kean Concierge API"})

@app.route("/search", methods=["GET", "POST"])
@login_required
def catalog_search():
    """Searches Elasticsearch Index of BF 2.0 RDF for Kean"""
    token = request.form.get("token")
    query = request.form.get('query')
    search_results = []
    return jsonify({"message": "Searched on {}".format(query),
                    "results": search_results})

@app.route("/")
def home():
    return jsonify({"about": "Kean Concierge API"})
