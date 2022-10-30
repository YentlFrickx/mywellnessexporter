import io

from flask import Flask, request, flash, redirect, send_file, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from oauthlib.oauth2 import WebApplicationClient
import requests

import json
import os
import sqlite3

# Internal imports
from db import init_db_command
from user import User
import mywellnessfit
import strava

# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

application = Flask(__name__)
application.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

application.add_url_rule('/stravalogin', view_func=strava.stravalogin)
application.add_url_rule('/stravalogin/stravacallback', view_func=strava.stravacallback)

ALLOWED_EXTENSIONS = {'json'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(application)

# Naive database setup
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)


# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@application.route("/")
def index():
    if current_user.is_authenticated:
        return (
            "<p>Hello, {}! You're logged in! Email: {}</p>"
            "<div><p>Google Profile Picture:</p>"
            '<img src="{}" alt="Google profile pic"></img></div>'
            '<a class="button" href="/logout">Logout</a>'
            '<a class="button" href="/upload">Upload</a>'
            '<a class="button" href="/stravalogin">Strava Login</a>'.format(
                current_user.name, current_user.email, current_user.profile_pic
            )
        )
    else:
        return '<a class="button" href="/login">Google Login</a>'


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@application.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@application.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add it to the database.
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))


@application.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@application.route("/upload")
def upload():
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action='/uploadjson' method=post enctype=multipart/form-data>
      <input type=file name=file required>
      <input type="time" name="time" required>
      <input type=submit value=Upload>
    </form>'''


@application.route('/uploadjson', methods=['POST', 'GET'])
def uploadJson():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect("index.html")
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect("index.html")
        if file and allowed_file(file.filename):
            data = file.read()
            jsonData = json.loads(data.decode('utf-8'))
            jsonData["data"]["time"] = request.form["time"]
            filePath = mywellnessfit.convert(jsonData)

            # return_data = io.BytesIO()
            # with open(filePath, 'rb') as fo:
            #     return_data.write(fo.read())
            # # (after writing, cursor will be at last byte, so move it to start)
            # return_data.seek(0)
            strava.stravaUpload(open(filePath, 'rb'))

            # os.remove(filePath)

            # return send_file(return_data, mimetype='application/vnd.ant.fit',
            #                  download_name='converted.fit')
            return 'success!'
            # return send_file(filePath, as_attachment=True)


if __name__ == "__main__":
    application.run(ssl_context="adhoc")


