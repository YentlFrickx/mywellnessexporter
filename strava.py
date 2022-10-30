import json
import os

import requests
from flask import request, redirect, url_for
from flask_login import current_user, login_required
from oauthlib.oauth2 import WebApplicationClient

from user import User

STRAVA_CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID", None)
STRAVA_CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET", None)

# OAuth 2 client setup
strava_client = WebApplicationClient(STRAVA_CLIENT_ID)

@login_required
def stravalogin():
    # Find out what URL to hit for Google login
    authorization_endpoint = "https://www.strava.com/oauth/authorize"

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = strava_client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/stravacallback",
        scope=["read"],
    )
    return redirect(request_uri)


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

    # userinfo_endpoint = "https://www.strava.com/api/v3/athlete"
    # uri, headers, body = strava_client.add_token(userinfo_endpoint)
    # userinfo_response = requests.get(uri, headers=headers, data=body)
    # if userinfo_response.json().get("username"):
    #     unique_id = userinfo_response.json()["id"]
    #     users_name = userinfo_response.json()["username"]
    # else:
    #     return "User email not available or not verified by Strava.", 400

    # User.addStravaCreds(current_user.id, token_response.json().)
    # user = User(
    #     id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    # )
    #
    # current_user.id
    #
    #
    # # Doesn't exist? Add it to the database.
    # if not User.get(unique_id):
    #     User.create(unique_id, users_name, users_email, picture)
    #
    # # Begin user session by logging the user in
    # login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))