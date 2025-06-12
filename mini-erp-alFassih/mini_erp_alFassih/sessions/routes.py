from flask import render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required
from datetime import datetime

from . import sessions_bp
from .forms import SessionForm
from ..models import Session, Patient, Therapist # Use .. for parent package models
from .. import db # Use .. for parent package db

@sessions_bp.route('/') # Corresponds to /sessions/
@login_required
def list_sessions():
    sessions = Session.query.options(
        db.joinedload(Session.assigned_patient),
        db.joinedload(Session.assigned_therapist)
    ).order_by(Session.start_time.desc()).all()
    return render_template('sessions/sessions_list.html', sessions=sessions, title='All Sessions', year=datetime.now().year)

@sessions_bp.route('/new', methods=['GET', 'POST']) # Corresponds to /sessions/new
@login_required
def create_session():
    form = SessionForm()
    # Pre-fill patient if patient_id is in query args (e.g., from patient_detail page)
    patient_id_arg = request.args.get('patient_id')
    if patient_id_arg and request.method == 'GET':
        patient = Patient.query.get(patient_id_arg)
        if patient:
            form.patient.data = patient

    if form.validate_on_submit():
        new_session = Session(
            patient_id=form.patient.data.id,
            therapist_id=form.therapist.data.id,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            session_type=form.session_type.data,
            status=form.status.data,
            notes=form.notes.data
        )
        db.session.add(new_session)
        db.session.commit()
        flash('Session created successfully!', 'success')
        return redirect(url_for('sessions.list_sessions'))
    return render_template('sessions/session_form.html', form=form, title='Schedule New Session', year=datetime.now().year)

@sessions_bp.route('/<int:session_id>') # Corresponds to /sessions/<id>
@login_required
def view_session(session_id):
    session = Session.query.options(
        db.joinedload(Session.assigned_patient),
        db.joinedload(Session.assigned_therapist)
    ).get_or_404(session_id)
    return render_template('sessions/session_detail.html', session=session, title='Session Details', year=datetime.now().year)

@sessions_bp.route('/<int:session_id>/edit', methods=['GET', 'POST']) # Corresponds to /sessions/<id>/edit
@login_required
def edit_session(session_id):
    session = Session.query.get_or_404(session_id)
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
        flash('Session updated successfully!', 'success')
        return redirect(url_for('sessions.view_session', session_id=session.id))

    return render_template('sessions/session_form.html', form=form, title='Edit Session', session=session, year=datetime.now().year)

@sessions_bp.route('/<int:session_id>/cancel', methods=['POST']) # Corresponds to /sessions/<id>/cancel
@login_required
def cancel_session(session_id):
    session = Session.query.get_or_404(session_id)
    session.status = 'Cancelled'
    db.session.commit()
    return jsonify(success=True, message='Session cancelled successfully.', new_status='Cancelled', session_id=session_id), 200
