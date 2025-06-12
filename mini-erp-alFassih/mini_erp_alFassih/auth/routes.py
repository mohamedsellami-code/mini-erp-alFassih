from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user
from datetime import datetime

from . import auth_bp
from .forms import LoginForm
from ..models import User # Use .. to go up one level to import models
from .. import db # If db session operations are needed directly, though usually via models

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
