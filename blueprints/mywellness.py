import json
import os
import re

import requests
from flask import Blueprint, render_template, redirect
import pickle

from flask_login import login_required, current_user
from bs4 import BeautifulSoup

import fitGenerator
from blueprints.strava import stravaUpload
# from models.activity import Activity
# from models.error import Error
from db import db
from models.activity import Activity
from models.error import Error
from models.form import MyWellnessLoginForm
from models.user import User

mywellness = Blueprint('mywellness', __name__)

LOGIN_URL = 'https://www.mywellness.com/cloud/User/Login/'


def save_cookies(requests_cookiejar, filename):
    with open(filename, 'wb') as f:
        pickle.dump(requests_cookiejar, f)


def load_cookies(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)


@mywellness.route('/connect/mywellness', methods=['GET', 'POST'])
@login_required
def login():
    form = MyWellnessLoginForm()
    if form.validate_on_submit():
        body = {
            "UserBinder.username": form.email.data,
            "UserBinder.KeepMeLogged": 'true',
            "UserBinder.Password": form.password.data
        }
        response = requests.post(url=LOGIN_URL, data=body)
        cookie_dict = response.cookies.get_dict()

        current_user.mywellness_cookie = cookie_dict["_mwappseu"]
        db.session.commit()
        return redirect("/")
    return render_template('wellnesslogin.html', form=form)


def sync_sessions(user):
    user_id = user.id
    cookie_value = user.mywellness_cookie
    strava_id = user.strava_id
    if not (cookie_value and strava_id):
        return False
    cookie_dict = {"_mwappseu": cookie_value}

    # TODO: use current date
    url = 'https://www.mywellness.com/cloud/Training/LastPerformedWorkoutSession/?fromDate=30/10/2022&toDate=30/10/2022'
    response = requests.get(url=url, cookies=cookie_dict)
    soup = BeautifulSoup(response.text, "html.parser")
    sessions = soup.findAll('div', class_='single-item')

    for session in sessions:
        href = session.find_next('a').get('href')

        if Activity.query.filter_by(mywellness_href=href).first() is None and Error.query.filter_by(mywellness_href=href).first() is None:
            json_data = json.loads(get_activity(href, cookie_dict))
            fit_activity = fitGenerator.convert(json_data)
            if fit_activity.success:
                file_path = fit_activity.file_path
                with open(file_path, 'rb') as file:
                    data = file.read()

                os.remove(file_path)
                if stravaUpload(data):
                    activity = Activity(href, user_id)
                    db.session.add(activity)
                    db.session.commit()
                    continue
        else:
            continue

        error = Error(href, user_id)
        db.session.add(error)
        db.session.commit()
    return True


def get_activity(url, cookie_dict):
    response = requests.get(url=url, cookies=cookie_dict)
    soup = BeautifulSoup(response.text, "html.parser")
    js_scripts = soup.findAll('script', {"type": "text/javascript"})

    activity_analytics_id = ''
    token = ''

    for script in js_scripts:
        if script.text.find('EU.currentUser') > 0:
            token = re.search("token..:.\"(.*?).\"", script.text).group(1)
        elif script.text.find('window.physicalActivityAnalyticsId') > 0:
            activity_analytics_id = re.search("window.physicalActivityAnalyticsId = '(.*?)'", script.text).group(1)

    url = f"https://services.mywellness.com/Training/CardioLog/{activity_analytics_id}/Details?token={token}"
    activity_response = requests.get(url=url, cookies=cookie_dict)
    return activity_response.text
