from flask import Flask, request, flash, redirect, url_for, render_template
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    logout_user,
)
from flask_bootstrap import Bootstrap

import json
import os
import sqlite3

# Internal imports
from blueprints.google import google
from db import init_db_command
from form import UploadForm
from models.user import User
import mywellnessfit
from blueprints.strava import strava

application = Flask(__name__)
Bootstrap(application)
application.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

application.register_blueprint(google)
application.register_blueprint(strava)

ALLOWED_EXTENSIONS = {'json'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


login_manager = LoginManager()
login_manager.init_app(application)

try:
    init_db_command()
except sqlite3.OperationalError:
    pass


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@application.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.strava_id:
            show_strava = False
        else:
            show_strava = True

        return render_template('home.html', show_strava=show_strava)
    else:
        return render_template('login.html')


@application.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@application.route("/upload", methods=['GET', 'POST'])
def upload():
    # 'form' is the variable name used in this template: index.html
    form = UploadForm()
    if form.validate_on_submit():
        return redirect(url_for("/"))
    return render_template('upload.html', form=form)

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


