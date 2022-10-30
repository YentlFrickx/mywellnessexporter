from flask_login import UserMixin

from db import get_db


class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic, strava_id, strava_access_token, strava_expires, strava_refresh_token):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic
        self.strava_id = strava_id
        self.strava_access_token = strava_access_token
        self.strava_expires = strava_expires
        self.strava_refresh_token = strava_refresh_token

    @staticmethod
    def get(user_id):
        db = get_db()
        user = db.execute(
            "SELECT * FROM user WHERE id = ?", (user_id,)
        ).fetchone()
        if not user:
            return None

        user = User(
            id_=user[0],
            name=user[1],
            email=user[2],
            profile_pic=user[3],
            strava_id=user[4],
            strava_access_token=user[5],
            strava_expires=user[6],
            strava_refresh_token=user[7]
        )
        return user

    @staticmethod
    def create(id_, name, email, profile_pic):
        db = get_db()
        db.execute(
            "INSERT INTO user (id, name, email, profile_pic) "
            "VALUES (?, ?, ?, ?)",
            (id_, name, email, profile_pic),
        )
        db.commit()

    @staticmethod
    def addStravaCreds(user_id, strava_id, strava_access_token, strava_expires, strava_refresh_token):
        db = get_db()
        db.execute(
            "UPDATE user set strava_id=?, strava_access_token=?, strava_expires=?, strava_refresh_token=? "
            "WHERE (id = ?)",
            (strava_id, strava_access_token, strava_expires, strava_refresh_token, user_id)
        )
        db.commit()

    def updateStravaTokens(user_id, strava_access_token, strava_expires, strava_refresh_token):
        db = get_db()
        db.execute(
            "UPDATE user set strava_access_token=?, strava_expires=?, strava_refresh_token=? "
            "WHERE (id = ?)",
            (strava_access_token, strava_expires, strava_refresh_token, user_id)
        )
        db.commit()
