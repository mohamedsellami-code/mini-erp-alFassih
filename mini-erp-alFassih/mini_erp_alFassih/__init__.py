"""
The flask application package.
"""

from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from .config import config_by_name # Import config

# Initialize extensions that don't need the app object immediately
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True) # instance_relative_config=True is good practice

    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')
    app.config.from_object(config_by_name[config_name])

    # Ensure instance path exists (used for SQLite DB, uploads, etc.)
    # Flask creates it if instance_relative_config=True and it's accessed,
    # but explicit creation doesn't hurt.
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Configure UPLOAD_FOLDER using instance_path and a setting from config
    upload_folder_name = app.config.get('UPLOAD_FOLDER_NAME', 'uploads')
    UPLOAD_FOLDER_ABS_PATH = os.path.join(app.instance_path, upload_folder_name)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER_ABS_PATH
    try:
        os.makedirs(UPLOAD_FOLDER_ABS_PATH)
    except OSError:
        pass

    # Initialize extensions with the app object
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Flask-Login settings (can be set after init_app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    from . import models # Import models after db is initialized and configured

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    # Register Blueprints
    from .main import main_bp
    app.register_blueprint(main_bp)

    from .auth import auth_bp
    app.register_blueprint(auth_bp)

    from .admin import admin_bp
    app.register_blueprint(admin_bp)

    from .patients import patients_bp
    app.register_blueprint(patients_bp, url_prefix='/patients')

    from .sessions import sessions_bp
    app.register_blueprint(sessions_bp, url_prefix='/sessions')

    from .errors import errors_bp # Import the errors blueprint
    app.register_blueprint(errors_bp)

    if not app.debug and not app.testing: # Configure logging for production-like environments
        import logging
        from logging.handlers import RotatingFileHandler
        # import os # os is already imported at the top

        # Ensure instance folder exists (it should from earlier UPLOAD_FOLDER setup, but double check)
        # This was already done earlier in create_app, so it's likely redundant here, but safe.
        if not os.path.exists(app.instance_path):
            try:
                os.makedirs(app.instance_path)
            except OSError:
                 # Handle potential race condition or permission issue if necessary
                pass


        # Log to a file in the instance folder
        file_handler = RotatingFileHandler(
            os.path.join(app.instance_path, 'alfassih.log'), # Log file path
            maxBytes=10240,  # Max 10KB per file before rotating
            backupCount=10   # Keep 10 backup files
        )

        # Set a specific format for the log messages
        log_format = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(log_format)

        # Set the logging level for the file handler
        file_handler.setLevel(logging.INFO) # Log INFO level and above (WARNING, ERROR, CRITICAL)

        # Add the file handler to the app's logger
        app.logger.addHandler(file_handler)

        # Also set the app's logger level (if not set, it might default to WARNING)
        app.logger.setLevel(logging.INFO)

        app.logger.info('Al-Fasih application startup') # Test log message

    return app

# The global 'app' instance is removed.
# Flask CLI and WSGI servers should now use the 'create_app' factory.
# For example, set FLASK_APP=mini_erp_alFassih:create_app() in .env or shell.
# runserver.py has been updated to call create_app().
