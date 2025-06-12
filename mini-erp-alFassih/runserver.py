"""
This script runs the mini_erp_alFassih application using a development server.
"""

import os # Added os import
from os import environ
from mini_erp_alFassih.mini_erp_alFassih import create_app # Changed import

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    HOST = environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)
