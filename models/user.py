from flask_login import UserMixin
from sqlalchemy.orm import relationship

from db import db


class LoginUser(UserMixin):
    def __init__(self,
                 id_):
        self.id = id_


class User(UserMixin, db.Model):

    id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    profile_pic = db.Column(db.String(100))
    strava_id = db.Column(db.String(100))
    strava_access_token = db.Column(db.String(100))
    strava_expires = db.Column(db.String(100))
    strava_refresh_token = db.Column(db.String(100))
    mywellness_cookie = db.Column(db.String(1000))
    activities = relationship("Activity")

    def __init__(self,
                 id_,
                 name,
                 email,
                 profile_pic,
                 strava_id='',
                 strava_access_token='',
                 strava_expires='',
                 strava_refresh_token='',
                 mywellness_cookie=''):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic
        self.strava_id = strava_id
        self.strava_access_token = strava_access_token
        self.strava_expires = strava_expires
        self.strava_refresh_token = strava_refresh_token
        self.mywellness_cookie = mywellness_cookie

