import re

import requests
from flask import Blueprint, render_template, redirect
import pickle

from flask_login import login_required, current_user
from bs4 import BeautifulSoup

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

        User.add_mywellness_cookie(current_user.id, cookie_dict["_mwappseu"])
        return redirect("/")
    return render_template('wellnesslogin.html', form=form)


@mywellness.route('/connect/mywellness/sessions')
@login_required
def get_sessions():
    cookie_value = User.get_cookie(current_user.id)
    if not cookie_value:
        return redirect('/connect/mywellness')
    cookie_dict = {"_mwappseu": cookie_value}
    url = 'https://www.mywellness.com/cloud/Training/LastPerformedWorkoutSession/?fromDate=27/10/2022&toDate=27/10/2022'
    response = requests.get(url=url, cookies=cookie_dict)
    soup = BeautifulSoup(response.text, "html.parser")
    sessions = soup.findAll('div', class_='single-item')
    sessionIds = []
    for session in sessions:
        href = session.find_next('a')
        return get_activity(href.get('href'), cookie_dict)
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
