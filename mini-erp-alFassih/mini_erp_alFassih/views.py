"""
Routes and views for the flask application.
"""

from datetime import datetime, timedelta # Added timedelta
from flask import render_template, request, redirect, url_for, current_app, send_from_directory # flash can be added if used
from mini_erp_alFassih import app, db, models
from .forms import PatientForm, DocumentForm, SessionForm, TherapistForm
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
    # Query and sort sessions here to pass to template
    # This ensures the sorting logic is in the view, not template.
    # The relationship is lazy='dynamic', so patient.sessions is a query object.
    patient_sessions = patient.sessions.order_by(models.Session.start_time.desc()).all()
    return render_template('patient_detail.html', patient=patient, patient_sessions=patient_sessions, title='Patient Details', year=datetime.now().year)

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

# Admin Dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    total_patients = models.Patient.query.count()
    total_documents = models.Document.query.count()
    total_therapists = models.Therapist.query.count()
    total_sessions = models.Session.query.count()

    # Patients added in the last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    new_patients_last_7_days = models.Patient.query.filter(models.Patient.created_at >= seven_days_ago).count()

    # Sessions scheduled for today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    sessions_today = models.Session.query.filter(
        models.Session.start_time >= today_start,
        models.Session.start_time < today_end,
        models.Session.status == 'Scheduled'
    ).count()

    stats = {
        'total_patients': total_patients,
        'total_documents': total_documents,
        'total_therapists': total_therapists,
        'total_sessions': total_sessions,
        'new_patients_last_7_days': new_patients_last_7_days,
        'sessions_today': sessions_today
    }

    # Recent Patients (last 5)
    recent_patients = models.Patient.query.order_by(models.Patient.created_at.desc()).limit(5).all()

    # Upcoming Sessions (next 5, status Scheduled)
    now = datetime.utcnow() # Use now consistently for time comparisons
    upcoming_sessions = models.Session.query.filter(
        models.Session.start_time > now,
        models.Session.status == 'Scheduled'
    ).options(
        db.joinedload(models.Session.assigned_patient), # Eager load for template
        db.joinedload(models.Session.assigned_therapist)
    ).order_by(models.Session.start_time.asc()).limit(5).all()

    return render_template('admin/dashboard.html', title='Admin Dashboard',
                           stats=stats,
                           recent_patients=recent_patients,
                           upcoming_sessions=upcoming_sessions,
                           year=datetime.now().year)

# Admin-like section for Therapists
@app.route('/admin/therapists')
def list_therapists():
    therapists = models.Therapist.query.all()
    return render_template('admin/therapist_list.html', therapists=therapists, title='Manage Therapists', year=datetime.now().year)

@app.route('/admin/therapists/new', methods=['GET', 'POST'])
def create_therapist():
    form = TherapistForm()
    if form.validate_on_submit():
        new_therapist = models.Therapist(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            specialization=form.specialization.data
        )
        db.session.add(new_therapist)
        db.session.commit()
        # flash('Therapist added successfully!', 'success') # Optional
        return redirect(url_for('list_therapists'))
    return render_template('admin/therapist_form.html', form=form, title='Add New Therapist', year=datetime.now().year)

@app.route('/admin/therapists/<int:therapist_id>/edit', methods=['GET', 'POST'])
def edit_therapist(therapist_id):
    therapist = models.Therapist.query.get_or_404(therapist_id)
    form = TherapistForm(obj=therapist) # Pre-populate form
    if form.validate_on_submit():
        therapist.first_name = form.first_name.data
        therapist.last_name = form.last_name.data
        therapist.specialization = form.specialization.data
        db.session.commit()
        # flash('Therapist updated successfully!', 'success') # Optional
        return redirect(url_for('list_therapists'))
    return render_template('admin/therapist_form.html', form=form, title='Edit Therapist', therapist=therapist, year=datetime.now().year)

@app.route('/admin/therapists/<int:therapist_id>/delete', methods=['POST'])
def delete_therapist(therapist_id):
    therapist = models.Therapist.query.get_or_404(therapist_id)
    # Cascade delete for sessions is handled by model relationship configuration
    db.session.delete(therapist)
    db.session.commit()
    # flash('Therapist deleted successfully!', 'success') # Optional
    return redirect(url_for('list_therapists'))

# Session Management Views
@app.route('/sessions')
def list_sessions():
    # Eager load patient and therapist details to avoid N+1 queries in template
    sessions = models.Session.query.options(
        db.joinedload(models.Session.assigned_patient),
        db.joinedload(models.Session.assigned_therapist)
    ).order_by(models.Session.start_time.desc()).all()
    return render_template('sessions_list.html', sessions=sessions, title='All Sessions', year=datetime.now().year)

@app.route('/sessions/new', methods=['GET', 'POST'])
def create_session():
    form = SessionForm()
    if form.validate_on_submit():
        new_session = models.Session(
            patient_id=form.patient.data.id, # Corrected: Access id from the Patient object
            therapist_id=form.therapist.data.id, # Corrected: Access id from the Therapist object
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            session_type=form.session_type.data,
            status=form.status.data,
            notes=form.notes.data
        )
        db.session.add(new_session)
        db.session.commit()
        # flash('Session created successfully!', 'success') # Optional
        return redirect(url_for('list_sessions'))
    return render_template('session_form.html', form=form, title='Schedule New Session', year=datetime.now().year)

@app.route('/sessions/<int:session_id>')
def view_session(session_id):
    session = models.Session.query.options(
        db.joinedload(models.Session.assigned_patient),
        db.joinedload(models.Session.assigned_therapist)
    ).get_or_404(session_id)
    return render_template('session_detail.html', session=session, title='Session Details', year=datetime.now().year)

@app.route('/sessions/<int:session_id>/edit', methods=['GET', 'POST'])
def edit_session(session_id):
    session = models.Session.query.get_or_404(session_id)
    form = SessionForm(obj=session)

    if form.validate_on_submit():
        session.patient_id = form.patient.data.id
        session.therapist_id = form.therapist.data.id
        session.start_time = form.start_time.data
        session.end_time = form.end_time.data
        session.session_type = form.session_type.data
        session.status = form.status.data
        session.notes = form.notes.data
        db.session.commit()
        # flash('Session updated successfully!', 'success') # Optional
        return redirect(url_for('view_session', session_id=session.id))

    return render_template('session_form.html', form=form, title='Edit Session', session=session, year=datetime.now().year)

@app.route('/sessions/<int:session_id>/cancel', methods=['POST'])
def cancel_session(session_id):
    session = models.Session.query.get_or_404(session_id)
    session.status = 'Cancelled'
    db.session.commit()
    # flash('Session cancelled.', 'info') # Optional
    return redirect(request.referrer or url_for('list_sessions'))
