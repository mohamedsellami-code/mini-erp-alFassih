from flask import Blueprint

sessions_bp = Blueprint('sessions', __name__, template_folder='templates')

from . import routes
