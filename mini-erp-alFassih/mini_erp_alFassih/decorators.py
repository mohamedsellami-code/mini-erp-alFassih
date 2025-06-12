from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if getattr(current_user, 'role', None) != 'admin':
            flash('You do not have permission to access this page. Admin access required.', 'danger')
            # Redirect to 'main.home' as 'home' is now in the 'main' blueprint
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function
