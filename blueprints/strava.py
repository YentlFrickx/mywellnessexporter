import json
import os

import requests
from flask import request, redirect, url_for, Blueprint
from flask_login import current_user
from oauthlib.oauth2 import WebApplicationClient

from models.user import User

strava = Blueprint('strava', __name__)

STRAVA_CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID", None)
STRAVA_CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET", None)

# OAuth 2 client setup
strava_client = WebApplicationClient(STRAVA_CLIENT_ID)

@strava.route("/connect/strava-oauth")
def stravalogin():
    if not current_user.is_authenticated:
        return redirect(url_for('/users/google-oauth'))

    authorization_endpoint = "https://www.strava.com/oauth/authorize"

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = strava_client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["activity:write"],
    )
    return redirect(request_uri)


def refreshToken():
    token_url, headers, body = strava_client.prepare_refresh_token_request(
        token_url="https://www.strava.com/oauth/token",
        refresh_token=current_user.strava_refresh_token,
        scope=["activity:write"],
        client_id=STRAVA_CLIENT_ID,
        client_secret=STRAVA_CLIENT_SECRET
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET),
    )

    strava_client.parse_request_body_response(json.dumps(token_response.json()))

    refresh_token = token_response.json()["refresh_token"]
    expires = token_response.json()["expires_at"]
    access_token = token_response.json()["access_token"]
    User.updateStravaTokens(current_user.id, access_token, expires, refresh_token)

def stravaUpload(file):

    upload_endpoint = "https://www.strava.com/api/v3/uploads"
    uri, headers, body = strava_client.add_token(upload_endpoint,)
    response = requests.post(uri, headers=headers, data=body, files={'file': ('activity.fit', file, 'application/vnd.ant.fit', {'Expires': '0'})})

    if response.status_code == 201:
        return 'success!'

@strava.route("/connect/strava-oauth/callback")
def stravacallback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = strava_client.prepare_token_request(
        "https://www.strava.com/oauth/token",
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
        client_id=STRAVA_CLIENT_ID,
        client_secret=STRAVA_CLIENT_SECRET
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET),
    )

    # Parse the tokens!
    strava_client.parse_request_body_response(json.dumps(token_response.json()))

    refresh_token = token_response.json()["refresh_token"]
    expires = token_response.json()["expires_at"]
    access_token = token_response.json()["access_token"]
    strava_id = token_response.json()["athlete"]["id"]
    User.addStravaCreds(current_user.id, strava_id, access_token, expires, refresh_token)

    # Send user back to homepage
    return redirect(url_for("index"))