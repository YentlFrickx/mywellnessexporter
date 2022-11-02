from flask import Blueprint, render_template
from flask_login import login_required, current_user

general = Blueprint('general', __name__)


@general.route("/connections")
@login_required
def connections():
    if current_user.strava_id:
        strava_status = 'connected'
    else:
        strava_status = 'not connected'

    if current_user.mywellness_cookie:
        mywellness_status = 'connected'
    else:
        mywellness_status = 'not connected'

    return render_template('connect.html', strava_status=strava_status, mywellness_status=mywellness_status )


@general.route("/")
@login_required
def index():
    if current_user.strava_id:
        show_strava = False
    else:
        show_strava = True

    return render_template('home.html', show_strava=show_strava)