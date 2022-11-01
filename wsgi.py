from flask import Flask, request, redirect, url_for, render_template
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    logout_user,
)
from flask_bootstrap import Bootstrap

import os
import sqlite3

# Internal imports
from blueprints.google import google
from blueprints.mywellness import mywellness
from db import init_db_command
from models.user import User
from blueprints.strava import strava

application = Flask(__name__)
Bootstrap(application)
application.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

application.register_blueprint(google)
application.register_blueprint(strava)
application.register_blueprint(mywellness)


login_manager = LoginManager()
login_manager.init_app(application)

try:
    init_db_command()
except sqlite3.OperationalError:
    pass


@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/users/google-oauth?next=' + request.path)


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@application.route("/")
@login_required
def index():
    if current_user.strava_id:
        show_strava = False
    else:
        show_strava = True

    return render_template('home.html', show_strava=show_strava)


@application.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


if __name__ == "__main__":
    application.run(ssl_context="adhoc")


