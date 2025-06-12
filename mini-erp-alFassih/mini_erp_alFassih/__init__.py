"""
The flask application package.
"""

from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager # Added LoginManager

app = Flask(__name__) # Define app object here

# Upload folder configuration
UPLOAD_FOLDER = os.path.join(app.instance_path, 'uploads') # Now app.instance_path can be used
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the instance path and upload folder exist
try:
    os.makedirs(app.instance_path)
except OSError:
    pass # Already exists or other error (less critical for instance_path)
try:
    os.makedirs(UPLOAD_FOLDER)
except OSError:
    pass # Already exists or other error

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alfassih.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from . import models
# import mini_erp_alFassih.views # This line is no longer needed as views are in blueprints

# Register Blueprints
from .main import main_bp # Import the main blueprint
app.register_blueprint(main_bp)

from .auth import auth_bp # Import the auth blueprint
app.register_blueprint(auth_bp)

from .admin import admin_bp # Import the admin blueprint
app.register_blueprint(admin_bp)

from .patients import patients_bp # Import the patients blueprint
app.register_blueprint(patients_bp, url_prefix='/patients') # Add url_prefix for patients routes

from .sessions import sessions_bp # Import the sessions blueprint
app.register_blueprint(sessions_bp, url_prefix='/sessions')


# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login' # Updated to blueprint name
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info' # For styling flash messages

@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))
