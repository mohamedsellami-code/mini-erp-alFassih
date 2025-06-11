from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional

class PatientForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    contact_info = TextAreaField('Contact Information', validators=[Optional()])
    anamnesis = TextAreaField('Anamnesis', validators=[Optional()])
    submit = SubmitField('Save Patient')
