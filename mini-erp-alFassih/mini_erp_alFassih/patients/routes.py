from flask import render_template, request, redirect, url_for, current_app, send_from_directory, flash
from flask_login import login_required
from datetime import datetime

from . import patients_bp
from .forms import PatientForm, DocumentForm
from ..models import Patient, Document, Session # Use .. for parent package
from .. import db # Use .. for parent package
from ..utils import save_document # Use .. for parent package

@patients_bp.route('/') # Corresponds to /patients/ due to url_prefix in __init__.py blueprint registration
@login_required
def list_patients():
    patients = Patient.query.all()
    return render_template('patients/patients.html', patients=patients, title='Patients', year=datetime.now().year)

@patients_bp.route('/new', methods=['GET', 'POST']) # Corresponds to /patients/new
@login_required
def create_patient():
    form = PatientForm()
    if form.validate_on_submit():
        new_patient = Patient(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            date_of_birth=form.date_of_birth.data,
            contact_info=form.contact_info.data,
            anamnesis=form.anamnesis.data
        )
        db.session.add(new_patient)
        db.session.commit()
        flash('Patient created successfully!', 'success')
        return redirect(url_for('patients.list_patients'))
    return render_template('patients/patient_form.html', form=form, title='Create Patient', year=datetime.now().year)

@patients_bp.route('/<int:patient_id>') # Corresponds to /patients/<id>
@login_required
def view_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    patient_sessions = patient.sessions.order_by(Session.start_time.desc()).all()
    return render_template('patients/patient_detail.html', patient=patient, patient_sessions=patient_sessions, title='Patient Details', year=datetime.now().year)

@patients_bp.route('/<int:patient_id>/edit', methods=['GET', 'POST']) # Corresponds to /patients/<id>/edit
@login_required
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        form.populate_obj(patient)
        db.session.commit()
        flash('Patient profile updated successfully!', 'success')
        return redirect(url_for('patients.view_patient', patient_id=patient.id))
    return render_template('patients/patient_form.html', form=form, patient=patient, title='Edit Patient', year=datetime.now().year)

@patients_bp.route('/<int:patient_id>/documents/upload', methods=['GET', 'POST']) # Corresponds to /patients/<id>/documents/upload
@login_required
def upload_document(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = DocumentForm()
    if form.validate_on_submit():
        file_storage = form.file.data
        saved_filename = save_document(file_storage, patient_id) # save_document is from ..utils

        new_document = Document(
            patient_id=patient.id,
            title=form.title.data,
            document_type=form.document_type.data,
            description=form.description.data,
            filename=saved_filename
        )
        db.session.add(new_document)
        db.session.commit()
        flash('Document uploaded successfully!', 'success')
        return redirect(url_for('patients.view_patient', patient_id=patient.id))

    return render_template('patients/document_upload_form.html', title='Upload Document', form=form, patient=patient, year=datetime.now().year)

@patients_bp.route('/documents/<int:document_id>/download') # This route doesn't strictly need to be nested under /patients/
@login_required
def download_document(document_id):
    document = Document.query.get_or_404(document_id)
    # Assuming UPLOAD_FOLDER is configured on current_app correctly
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(
        directory=upload_folder,
        path=document.filename,
        as_attachment=True
    )
