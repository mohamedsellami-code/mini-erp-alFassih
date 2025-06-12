"""
The flask application package.
"""

from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

# Upload folder configuration
UPLOAD_FOLDER = os.path.join(app.instance_path, 'uploads')
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
import mini_erp_alFassih.views
