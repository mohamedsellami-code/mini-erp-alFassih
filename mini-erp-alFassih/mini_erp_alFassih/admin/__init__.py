from flask import Blueprint

admin_bp = Blueprint('admin', __name__, template_folder='templates', url_prefix='/admin')
# url_prefix automatically adds '/admin' to all routes in this blueprint.

from . import routes # Import routes after blueprint creation
