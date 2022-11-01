from flask_wtf import FlaskForm
from wtforms import SubmitField, FileField, TimeField
from wtforms.validators import DataRequired


class UploadForm(FlaskForm):
    time = TimeField('When did you do the activity?', format='%H:%M')
    file = FileField('Upload', validators=[DataRequired()])
    submit = SubmitField('Submit')