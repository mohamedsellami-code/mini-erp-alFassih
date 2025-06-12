import os
from dotenv import load_dotenv

# Determine project root (one level up from this app package file) to load .env
# Assuming this config.py is inside the 'mini_erp_alFassih' app package,
# and the .env file is in the project root 'mini-erp-alFassih/'.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # Corrected path
dotenv_path = os.path.join(project_root, '.env')

if os.path.exists(dotenv_path):
    print(f"Loading .env file from {dotenv_path}")
    load_dotenv(dotenv_path)
else:
    print(f".env file not found at {dotenv_path}. Using defaults or environment variables.")

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key-for-dev-please-change'
    # If SQLALCHEMY_DATABASE_URI is a relative path like 'sqlite:///alfassih.db',
    # Flask prepends app.instance_path to it by default when using from_object.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///alfassih.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False # Default to False, overridden by DevelopmentConfig
    UPLOAD_FOLDER_NAME = 'uploads' # Keep upload folder name configurable


class DevelopmentConfig(Config):
    DEBUG = True
    # SQLALCHEMY_ECHO = True # Optional: to log SQL queries

class ProductionConfig(Config):
    DEBUG = False
    # Ensure SECRET_KEY is robust and definitely set from env in production.
    # Production database URI should be set via DATABASE_URL environment variable.
    # Example: Assert that critical keys are set
    if not Config.SECRET_KEY or Config.SECRET_KEY == 'a-very-secret-key-for-dev-please-change':
        # In a real production scenario, you might raise an error or log a critical warning.
        print("WARNING: SECRET_KEY is not set or is using the default weak key in ProductionConfig!")
    if not os.environ.get('DATABASE_URL'):
        print("WARNING: DATABASE_URL is not set in ProductionConfig!")

    # Secure Cookie Settings for Production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax' # Or 'Strict' if appropriate for your app's needs

    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax' # Or 'Strict'


config_by_name = dict(
    development=DevelopmentConfig,
    production=ProductionConfig,
    default=DevelopmentConfig # Default to development for safety if FLASK_CONFIG not set
)
