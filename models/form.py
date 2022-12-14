from flask_wtf import FlaskForm
from wtforms import SubmitField, FileField, TimeField, EmailField, PasswordField
from wtforms.validators import DataRequired


class UploadForm(FlaskForm):
    time = TimeField('When did you do the activity?', format='%H:%M')
    file = FileField('Upload', validators=[DataRequired()])
    submit = SubmitField('Submit')


class MyWellnessLoginForm(FlaskForm):
    email = EmailField('Email')
    password = PasswordField('Password')
    submit = SubmitField('Submit')
