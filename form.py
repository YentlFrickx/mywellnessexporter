from flask_wtf import FlaskForm
from wtforms import SubmitField, FileField, DateTimeLocalField
from wtforms.validators import DataRequired


class UploadForm(FlaskForm):
    name = DateTimeLocalField('When did you do the activity?', format='%d/%m/%y-%h:%m')
    file = FileField('Upload', validators=[DataRequired()])
    submit = SubmitField('Submit')