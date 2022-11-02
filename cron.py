import time
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

from blueprints.mywellness import sync_sessions
from models.user import User

global application


def sync():
    with application.app_context():
        print(f'Starting sync: {time.strftime("%A, %d. %B %Y %I:%M:%S %p")}')
        users = User.query.all()
        for user in users:
            sync_sessions(user)


def schedule(app):
    global application
    application = app
    scheduler = BackgroundScheduler()

    with application.app_context():
        scheduler.add_job(func=sync, trigger="interval", seconds=10)
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
