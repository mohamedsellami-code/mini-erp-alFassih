from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.fields import DateTimeLocalField # Corrected import for WTForms 3.x
from wtforms.validators import DataRequired, Optional, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from .. import models # Use .. to import models from parent package (app level)

# Factory functions for QuerySelectField
def patient_query():
    return models.Patient.query

def therapist_query(): # For SessionForm
    # Select Therapist profiles whose associated User is active and has 'therapist' role
    return models.Therapist.query.join(models.User, models.Therapist.user_id == models.User.id)\
                                      .filter(models.User.is_active == True, models.User.role == 'therapist')

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
