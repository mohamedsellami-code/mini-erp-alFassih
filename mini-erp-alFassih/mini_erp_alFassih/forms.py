from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, DateField, TextAreaField, SubmitField, SelectField, PasswordField, BooleanField # Added PasswordField, BooleanField
from wtforms.fields import DateTimeLocalField # Corrected import for WTForms 3.x
from wtforms.validators import DataRequired, Optional, ValidationError, Email # Added Email validator
from wtforms_sqlalchemy.fields import QuerySelectField
from . import models # Import models to be used by query_factory

# Factory functions for QuerySelectField
def patient_query():
    return models.Patient.query

def therapist_query(): # For SessionForm
    # Select Therapist profiles whose associated User is active and has 'therapist' role
    return models.Therapist.query.join(models.User, models.Therapist.user_id == models.User.id)\
                                      .filter(models.User.is_active == True, models.User.role == 'therapist')

class PatientForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    contact_info = TextAreaField('Contact Information', validators=[Optional()])
    anamnesis = TextAreaField('Anamnesis', validators=[Optional()])
    submit = SubmitField('Save Patient')

class DocumentForm(FlaskForm):
    title = StringField('Document Title', validators=[DataRequired()])
    document_type = StringField('Document Type (e.g., Bilan, Plan Thérapeutique)', validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional()])
    file = FileField('Document File', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx', 'txt'], 'Allowed file types: Images, PDF, DOC, TXT')
    ])
    submit = SubmitField('Upload Document')

class SessionForm(FlaskForm):
    patient = QuerySelectField(
        'Patient',
        query_factory=patient_query,
        get_label=lambda p: f"{p.first_name} {p.last_name} (ID: {p.id})",
        allow_blank=False,
        validators=[DataRequired()]
    )
    therapist = QuerySelectField(
        'Therapist',
        query_factory=therapist_query,
        get_label=lambda t: f"{t.first_name} {t.last_name} (ID: {t.id})",
        allow_blank=False,
        validators=[DataRequired()]
    )
    start_time = DateTimeLocalField('Start Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_time = DateTimeLocalField('End Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    session_type = StringField('Session Type (e.g., Consultation, Follow-up)', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('No Show', 'No Show')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Session')

    def validate_end_time(self, field):
        if self.start_time.data and field.data: # Ensure both fields have data
            if field.data <= self.start_time.data:
                raise ValidationError('End time must be after start time.')

class TherapistForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    specialization = StringField('Specialization', validators=[Optional()])
    email = StringField('User Email', validators=[DataRequired(), Email()])
    password = PasswordField('Set User Password', validators=[DataRequired()])
    # confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')]) # Optional
    submit = SubmitField('Save Therapist and Create User')

class EditTherapistProfileForm(FlaskForm):
    first_name = StringField('Therapist First Name', validators=[DataRequired()])
    last_name = StringField('Therapist Last Name', validators=[DataRequired()])
    specialization = StringField('Specialization', validators=[Optional()])
    # user_is_active = BooleanField("User Account Active", default=True) # Example for future
    submit = SubmitField('Save Profile Changes')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')
