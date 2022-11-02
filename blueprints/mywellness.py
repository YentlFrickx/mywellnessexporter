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


@mywellness.route('/connect/mywellness/sessions')
@login_required
def get_sessions():
    # TODO: get userid via param
    user_id = current_user.id
    cookie_value = User.get_cookie(user_id)
    if not cookie_value:
        return redirect('/connect/mywellness')
    cookie_dict = {"_mwappseu": cookie_value}

    # TODO: use current date
    url = 'https://www.mywellness.com/cloud/Training/LastPerformedWorkoutSession/?fromDate=30/10/2022&toDate=30/10/2022'
    response = requests.get(url=url, cookies=cookie_dict)
    soup = BeautifulSoup(response.text, "html.parser")
    sessions = soup.findAll('div', class_='single-item')

    for session in sessions:
        href = session.find_next('a').get('href')

        # if Activity.get(href) is None and Error.get(href) is None:
        json_data = json.loads(get_activity(href, cookie_dict))
        file_path = fitGenerator.convert(json_data)
        with open(file_path, 'rb') as file:
            data = file.read()

        os.remove(file_path)
        if stravaUpload(data):
            print('success')
            # Activity.create(href, user_id)

    return response.text


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
