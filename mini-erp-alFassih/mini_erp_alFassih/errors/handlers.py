# mini_erp_alFassih/mini_erp_alFassih/errors/handlers.py
from flask import render_template, current_app # Added current_app
from . import errors_bp
from .. import db # Correct relative import from app package for db

@errors_bp.app_errorhandler(403) # Use app_errorhandler for app-wide errors
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@errors_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@errors_bp.app_errorhandler(500)
def internal_error(error):
    # It's good practice to rollback the session in case the error
    # was caused by a database issue that left the session in a bad state.
    try:
        db.session.rollback()
    except Exception as e:
        # Log this exception as it means rollback failed
        try:
            current_app.logger.error(f"Failed to rollback session in 500 error handler: {e}")
        except Exception: # Fallback if logger itself fails or current_app is not available
            print(f"ERROR: Failed to rollback session in 500 error handler (and logging failed): {e}")

    return render_template('errors/500.html'), 500
