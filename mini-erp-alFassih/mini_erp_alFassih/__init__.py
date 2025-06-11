"""
The flask application package.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alfassih.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from . import models
import mini_erp_alFassih.views
