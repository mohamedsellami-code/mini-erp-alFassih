from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional

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
