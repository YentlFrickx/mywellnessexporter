import requests
from flask import Blueprint, render_template, redirect
import pickle

from flask_login import login_required, current_user

from models import user
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


@mywellness.route('/connect/mywellness/activity')
@login_required
def get_activity():
    cookie_value = User.get_cookie(current_user.id)
    if not cookie_value:
        return redirect('/connect/mywellness')
    cookie_dict={"_mwappseu": cookie_value}
    url = 'https://www.mywellness.com/cloud/Training/PerformedExerciseDetail/?idCr=1003&position=2&dayOpenSession=20221029&singleView=False'
    response = requests.get(url=url, cookies=cookie_dict)
    return response.text