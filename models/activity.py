from sqlalchemy import ForeignKey

from db import db


class Activity(db.Model):

    mywellness_href = db.Column(db.String(900), primary_key=True)
    user_id = db.Column(db.String(100), ForeignKey("user.id"))

    def __init__(self,
                 mywellness_href,
                 user_id):
        self.mywellness_href = mywellness_href
        self.user_id = user_id

