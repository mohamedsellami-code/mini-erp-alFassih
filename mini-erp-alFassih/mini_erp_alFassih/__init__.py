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
import mini_erp_alFassih.views # views might define routes, including login_view

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # The name of the login view function (will be created in views.py)
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info' # For styling flash messages

@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))
