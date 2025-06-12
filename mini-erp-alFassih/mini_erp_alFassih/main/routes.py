# mini-erp-alFassih/mini_erp_alFassih/main/routes.py
from flask import render_template
from datetime import datetime
from . import main_bp # Import the blueprint instance

@main_bp.route('/')
@main_bp.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html', # These will be found in app/templates/
        title='Home Page',
        year=datetime.now().year,
    )

@main_bp.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Contact',
        year=datetime.now().year,
        message='Your contact page.'
    )

@main_bp.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        message='Your application description page.'
    )
