"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template, request, redirect, url_for, current_app, send_from_directory
from mini_erp_alFassih import app, db, models
from .forms import PatientForm, DocumentForm
from .utils import save_document

@app.route('/')
@app.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
        title='Home Page',
        year=datetime.now().year,
    )

@app.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Contact',
        year=datetime.now().year,
        message='Your contact page.'
    )

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        message='Your application description page.'
    )

# Patient CRUD views
@app.route('/patients')
def list_patients():
    patients = models.Patient.query.all()
    return render_template('patients.html', patients=patients, title='Patients', year=datetime.now().year)

@app.route('/patients/new', methods=['GET', 'POST'])
def create_patient():
    form = PatientForm()
    if form.validate_on_submit():
        new_patient = models.Patient(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            date_of_birth=form.date_of_birth.data,
            contact_info=form.contact_info.data,
            anamnesis=form.anamnesis.data
        )
        db.session.add(new_patient)
        db.session.commit()
        return redirect(url_for('list_patients'))
    return render_template('patient_form.html', form=form, title='Create Patient', year=datetime.now().year)

@app.route('/patients/<int:patient_id>')
def view_patient(patient_id):
    patient = models.Patient.query.get_or_404(patient_id)
    return render_template('patient_detail.html', patient=patient, title='Patient Details', year=datetime.now().year)

@app.route('/patients/<int:patient_id>/edit', methods=['GET', 'POST'])
def edit_patient(patient_id):
    patient = models.Patient.query.get_or_404(patient_id)
    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        form.populate_obj(patient)
        db.session.commit()
        return redirect(url_for('view_patient', patient_id=patient.id))
    return render_template('patient_form.html', form=form, patient=patient, title='Edit Patient', year=datetime.now().year)

@app.route('/patients/<int:patient_id>/documents/upload', methods=['GET', 'POST'])
def upload_document(patient_id):
    patient = models.Patient.query.get_or_404(patient_id)
    form = DocumentForm()
    if form.validate_on_submit():
        file_storage = form.file.data
        saved_filename = save_document(file_storage, patient_id)

        new_document = models.Document(
            patient_id=patient.id,
            title=form.title.data,
            document_type=form.document_type.data,
            description=form.description.data,
            filename=saved_filename
        )
        db.session.add(new_document)
        db.session.commit()
        # flash('Document uploaded successfully!', 'success') # Optional: add flash messaging
        return redirect(url_for('view_patient', patient_id=patient.id))

    return render_template('document_upload_form.html', title='Upload Document', form=form, patient=patient, year=datetime.now().year)

@app.route('/documents/<int:document_id>/download')
def download_document(document_id):
    document = models.Document.query.get_or_404(document_id)
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(
        directory=upload_folder,
        path=document.filename,
        as_attachment=True
    )
