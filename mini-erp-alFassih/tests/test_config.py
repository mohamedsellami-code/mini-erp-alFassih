import unittest
import os
import sys

# Adjust path to import create_app from the correct location
# Assuming tests/ is at the same level as the main project folder mini-erp-alFassih/
# and the app package is mini_erp_alFassih/mini_erp_alFassih/
project_root_for_test = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# This adds mini-erp-alFassih/ (project root) to the path.
# The import will be from mini_erp_alFassih.mini_erp_alFassih import create_app
sys.path.insert(0, project_root_for_test)

from mini_erp_alFassih.mini_erp_alFassih import create_app
from mini_erp_alFassih.mini_erp_alFassih.config import ProductionConfig, DevelopmentConfig, Config

class TestConfig(unittest.TestCase):
    def test_development_config(self):
        app = create_app('development')
        self.assertTrue(app.config['DEBUG'])
        self.assertFalse(app.config['TESTING']) # TESTING is usually set explicitly in other test setups
        self.assertTrue('sqlite:///alfassih.db' in app.config['SQLALCHEMY_DATABASE_URI']) # Check default
        # Check default for a production cookie setting (should not be True in dev)
        self.assertNotEqual(app.config.get('SESSION_COOKIE_SECURE'), True)
        self.assertEqual(app.config.get('UPLOAD_FOLDER_NAME'), 'uploads') # Check default upload folder name


    def test_production_config(self):
        # Temporarily set env var for DATABASE_URL and SECRET_KEY to avoid print warnings from config.py
        # In a real test suite, you might mock os.environ or ensure it's set if ProdConfig demands it
        original_db_url = os.environ.get('DATABASE_URL')
        original_secret_key = os.environ.get('SECRET_KEY')

        os.environ['DATABASE_URL'] = 'sqlite:///prod_test_from_env.db' # Dummy value for test
        os.environ['SECRET_KEY'] = 'test_production_secret_key'

        app = create_app('production')

        # Restore original environment variables
        if original_db_url is None:
            del os.environ['DATABASE_URL']
        else:
            os.environ['DATABASE_URL'] = original_db_url

        if original_secret_key is None:
            del os.environ['SECRET_KEY']
        else:
            os.environ['SECRET_KEY'] = original_secret_key

        self.assertFalse(app.config['DEBUG'])
        self.assertTrue(app.config['SESSION_COOKIE_SECURE'])
        self.assertTrue(app.config['SESSION_COOKIE_HTTPONLY'])
        self.assertEqual(app.config['SESSION_COOKIE_SAMESITE'], 'Lax')
        self.assertTrue(app.config['REMEMBER_COOKIE_SECURE'])
        self.assertTrue(app.config['REMEMBER_COOKIE_HTTPONLY'])
        self.assertEqual(app.config['REMEMBER_COOKIE_SAMESITE'], 'Lax')
        self.assertEqual(app.config['SQLALCHEMY_DATABASE_URI'], 'sqlite:///prod_test_from_env.db')
        self.assertEqual(app.config['SECRET_KEY'], 'test_production_secret_key')

    def test_default_config_is_development(self):
        # Ensure if FLASK_CONFIG is not set, it defaults to development
        original_flask_config = os.environ.get('FLASK_CONFIG')
        if 'FLASK_CONFIG' in os.environ:
            del os.environ['FLASK_CONFIG']

        app = create_app() # Should use 'default' which maps to DevelopmentConfig

        if original_flask_config is not None:
            os.environ['FLASK_CONFIG'] = original_flask_config

        self.assertTrue(app.config['DEBUG']) # Characteristic of DevelopmentConfig
        self.assertEqual(app.config.get('UPLOAD_FOLDER_NAME'), 'uploads')


    def test_config_upload_folder_name(self):
        # Test if UPLOAD_FOLDER_NAME from config is used
        os.environ['FLASK_CONFIG'] = 'development' # Ensure a known config
        app = create_app()
        # Default is 'uploads' as set in Config class
        self.assertEqual(app.config.get('UPLOAD_FOLDER_NAME'), 'uploads')

        # Check if the UPLOAD_FOLDER absolute path is correctly constructed
        expected_upload_path = os.path.join(app.instance_path, 'uploads')
        self.assertEqual(app.config['UPLOAD_FOLDER'], expected_upload_path)


if __name__ == '__main__':
    unittest.main()
```
