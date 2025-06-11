import unittest
import sys
import os

# Add the project root to sys.path to allow direct import of mini_erp_alFassih
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from mini_erp_alFassih.mini_erp_alFassih import app, db, models

class TestPatientModel(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        # Bind the app to the current context
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_patient(self):
        # Create a Patient instance
        p = models.Patient(first_name='Test', last_name='User')
        db.session.add(p)
        db.session.commit()

        # Assert that the patient was created
        self.assertEqual(models.Patient.query.count(), 1)

        # Retrieve the patient and check details
        retrieved_patient = models.Patient.query.first()
        self.assertIsNotNone(retrieved_patient)
        self.assertEqual(retrieved_patient.first_name, 'Test')
        self.assertEqual(retrieved_patient.last_name, 'User')

if __name__ == '__main__':
    unittest.main()
