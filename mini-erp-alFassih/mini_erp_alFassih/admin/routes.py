from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from . import admin_bp
from .forms import TherapistForm, EditTherapistProfileForm
from ..models import User, Therapist, Patient, Document, Session # Use .. for parent package
from .. import db # Use .. for parent package
from ..decorators import admin_required # Use .. for parent package

@admin_bp.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    total_patients = Patient.query.count()
    total_documents = Document.query.count()
    total_therapists = Therapist.query.count()
    total_sessions = Session.query.count()

    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    new_patients_last_7_days = Patient.query.filter(Patient.created_at >= seven_days_ago).count()

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    sessions_today = Session.query.filter(
        Session.start_time >= today_start,
        Session.start_time < today_end,
        Session.status == 'Scheduled'
    ).count()

    stats = {
        'total_patients': total_patients,
        'total_documents': total_documents,
        'total_therapists': total_therapists,
        'total_sessions': total_sessions,
        'new_patients_last_7_days': new_patients_last_7_days,
        'sessions_today': sessions_today
    }

    recent_patients = Patient.query.order_by(Patient.created_at.desc()).limit(5).all()
    now = datetime.utcnow()
    upcoming_sessions = Session.query.filter(
        Session.start_time > now,
        Session.status == 'Scheduled'
    ).options(
        db.joinedload(Session.assigned_patient),
        db.joinedload(Session.assigned_therapist)
    ).order_by(Session.start_time.asc()).limit(5).all()

    return render_template('admin/dashboard.html', title='Admin Dashboard',
                           stats=stats,
                           recent_patients=recent_patients,
                           upcoming_sessions=upcoming_sessions,
                           year=datetime.now().year)

@admin_bp.route('/therapists')
@login_required
@admin_required
def list_therapists():
    therapists = Therapist.query.all()
    return render_template('admin/therapist_list.html', therapists=therapists, title='Manage Therapists', year=datetime.now().year)

@admin_bp.route('/therapists/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_therapist():
    form = TherapistForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email address already in use. Please use a different email.', 'danger')
            return render_template('admin/therapist_form.html', form=form, title='Add New Therapist', year=datetime.now().year, form_type='create')

        new_user = User(
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role='therapist',
            is_active=True
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)

        new_therapist_profile = Therapist(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            specialization=form.specialization.data,
            user=new_user
        )
        db.session.add(new_therapist_profile)

        try:
            db.session.commit()
            flash('Therapist and linked user account created successfully!', 'success')
            return redirect(url_for('admin.list_therapists')) # Corrected url_for
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating therapist or user: {e}', 'danger')

    return render_template('admin/therapist_form.html', form=form, title='Add New Therapist', year=datetime.now().year, form_type='create')

@admin_bp.route('/therapists/<int:therapist_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_therapist(therapist_id):
    therapist = Therapist.query.get_or_404(therapist_id)
    form = EditTherapistProfileForm(obj=therapist)

    if form.validate_on_submit():
        therapist.first_name = form.first_name.data
        therapist.last_name = form.last_name.data
        therapist.specialization = form.specialization.data
        try:
            db.session.commit()
            flash('Therapist profile updated successfully!', 'success')
            return redirect(url_for('admin.list_therapists')) # Corrected url_for
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating therapist profile: {e}', 'danger')

    user_email = therapist.user.email if therapist.user else "Not linked"
    user_is_active = therapist.user.is_active if therapist.user else "N/A"

    return render_template('admin/therapist_form.html', form=form, title='Edit Therapist Profile',
                           therapist=therapist, user_email=user_email, user_is_active=user_is_active,
                           year=datetime.now().year, form_type='edit')

@admin_bp.route('/therapists/<int:therapist_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_therapist(therapist_id):
    therapist = Therapist.query.get_or_404(therapist_id)
    db.session.delete(therapist)
    db.session.commit()
    return jsonify(success=True, message='Therapist deleted successfully.', therapist_id=therapist_id), 200

# User Management (Admin)
@admin_bp.route('/users')
@login_required
@admin_required
def list_users():
    users = User.query.order_by(User.email).all()
    return render_template('admin/user_list.html', users=users, title='Manage Users', year=datetime.now().year)

@admin_bp.route('/users/<int:user_id>/activate', methods=['GET']) # Changed to GET for simplicity now
@login_required
@admin_required
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id: # Prevent admin from activating themselves if already active (though UI prevents this)
        flash('You cannot change the status of your own account this way.', 'danger')
    else:
        user.is_active = True
        db.session.commit()
        flash(f'User {user.email} has been activated.', 'success')
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/users/<int:user_id>/deactivate', methods=['GET']) # Changed to GET for simplicity now
@login_required
@admin_required
def deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id: # Prevent admin from deactivating themselves
        flash('You cannot deactivate your own account.', 'danger')
    else:
        user.is_active = False
        db.session.commit()
        flash(f'User {user.email} has been deactivated.', 'warning')
    return redirect(url_for('admin.list_users'))
