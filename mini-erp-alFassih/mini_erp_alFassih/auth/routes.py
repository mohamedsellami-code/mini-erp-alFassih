from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user, login_required # Added login_required
from datetime import datetime

from . import auth_bp
from .forms import LoginForm, ChangePasswordForm # Added ChangePasswordForm
from ..models import User
from .. import db

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect to 'main.home' as 'home' is now part of 'main' blueprint
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash('Logged in successfully!', 'success')
            # Redirect to 'main.home' for default login
            return redirect(next_page or url_for('main.home'))
        else:
            flash('Invalid email or password, or account inactive.', 'danger')
    return render_template('auth/login.html', title='Login', form=form, year=datetime.now().year)

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login')) # Redirect to auth.login after logout

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            # db.session.add(current_user) # Not strictly needed if current_user is already part of session
            db.session.commit()
            flash('Your password has been updated successfully!', 'success')
            return redirect(url_for('main.home')) # Or a profile page e.g. url_for('auth.profile')
        else:
            flash('Incorrect current password.', 'danger')
    return render_template('auth/change_password.html', title='Change Password', form=form, year=datetime.now().year)
