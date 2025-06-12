"""
This script runs the mini_erp_alFassih application using a development server.
"""

from os import environ
from mini_erp_alFassih.mini_erp_alFassih import app # Corrected import path

if __name__ == '__main__':
    HOST = environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)
