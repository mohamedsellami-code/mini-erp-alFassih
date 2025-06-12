from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField # BooleanField can be added if user_is_active is used
from wtforms.validators import DataRequired, Optional, Email # EqualTo can be added for confirm_password

# Note: models are typically imported from the app level, e.g. from ..models import ...
# However, these forms don't directly reference models, only views using them do.

class TherapistForm(FlaskForm): # This form will now be primarily for CREATING therapists + linked user
    first_name = StringField('Therapist First Name', validators=[DataRequired()])
    last_name = StringField('Therapist Last Name', validators=[DataRequired()])
    specialization = StringField('Specialization', validators=[Optional()])
    email = StringField('User Email', validators=[DataRequired(), Email()])
    password = PasswordField('Set User Password', validators=[DataRequired()])
    # confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')]) # Optional
    submit = SubmitField('Save Therapist and Create User')

class EditTherapistProfileForm(FlaskForm):
    first_name = StringField('Therapist First Name', validators=[DataRequired()])
    last_name = StringField('Therapist Last Name', validators=[DataRequired()])
    specialization = StringField('Specialization', validators=[Optional()])
    # Potentially: field for User's is_active status if admin should manage this here
    # from wtforms import BooleanField
    # user_is_active = BooleanField("User Account Active", default=True)
    submit = SubmitField('Save Profile Changes')
