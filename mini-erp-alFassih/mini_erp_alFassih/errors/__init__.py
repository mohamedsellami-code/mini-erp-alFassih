# mini_erp_alFassih/mini_erp_alFassih/errors/__init__.py
from flask import Blueprint

errors_bp = Blueprint('errors', __name__)

from . import handlers # Import handlers after blueprint creation
