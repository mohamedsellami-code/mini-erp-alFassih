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

    return app

# This part is for when __init__.py was directly runnable or imported by runserver.py as 'app'
# With app factory, runserver.py will call create_app().
# For simplicity, if runserver.py still expects 'app', we can create a default app here.
# However, it's better to modify runserver.py to use create_app().
# For now, let's assume runserver.py will be updated.
# If not, a default app instance would be:
# app = create_app(os.getenv('FLASK_CONFIG', 'default'))

# The old direct 'app' instantiation and config will be removed or refactored into create_app.
# The following lines from the old structure will be effectively replaced by the factory.
# app = Flask(__name__)
# UPLOAD_FOLDER = os.path.join(app.instance_path, 'uploads')
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# ... os.makedirs ...
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alfassih.db'
# db = SQLAlchemy(app)
# migrate = Migrate(app, db)
# from . import models
# app.register_blueprint(main_bp)
# ... etc. for other blueprints and login_manager setup ...
# @login_manager.user_loader ...
# To make 'app' available if runserver.py still imports it directly:
# This is a common pattern if you're transitioning to app factory.
# The FLASK_APP environment variable in .env should point to this file (e.g., mini_erp_alFassih:app)
# or to runserver.py which then calls create_app.
# If FLASK_APP points here, Flask CLI needs an 'app' variable or a 'create_app' factory.
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
