import unittest
import sys
import os

# Add the project root to sys.path to allow direct import of mini_erp_alFassih
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from mini_erp_alFassih.mini_erp_alFassih import app, db, models

class TestPatientViews(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for easier form testing
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        self.app_context = app.app_context()
        self.app_context.push()
        self.client = app.test_client() # Use self.client consistently

        db.create_all()

        # Optional: Create a sample patient for tests that need an existing patient
        self.sample_patient = models.Patient(first_name='Sample', last_name='User', contact_info='sample@example.com')
        db.session.add(self.sample_patient)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_list_patients_route(self):
        response = self.client.get('/patients')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Patients', response.data) # Title
        self.assertIn(b'Sample', response.data) # Sample patient first name

    def test_create_patient_form_route(self):
        response = self.client.get('/patients/new')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create Patient', response.data) # Title
        self.assertIn(b'First Name', response.data) # A form field label

    def test_create_patient_logic(self):
        initial_patient_count = models.Patient.query.count()
        response = self.client.post('/patients/new', data=dict(
            first_name='New',
            last_name='Patient',
            date_of_birth='2000-01-01', # Ensure all required fields are present if any
            contact_info='new@example.com',
            anamnesis='Test anamnesis'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200) # Should redirect to list_patients
        self.assertIn(b'New', response.data)
        self.assertIn(b'Patient', response.data)
        self.assertEqual(models.Patient.query.count(), initial_patient_count + 1)

        newly_created_patient = models.Patient.query.filter_by(first_name='New').first()
        self.assertIsNotNone(newly_created_patient)
        self.assertEqual(newly_created_patient.last_name, 'Patient')

    def test_view_patient_route(self):
        patient = models.Patient.query.filter_by(first_name='Sample').first()
        self.assertIsNotNone(patient, "Sample patient not found for view test")
        response = self.client.get(f'/patients/{patient.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Patient Details', response.data)
        self.assertIn(b'Sample', response.data) # Patient's first name
        self.assertIn(b'User', response.data) # Patient's last name

    def test_edit_patient_form_route(self):
        patient = models.Patient.query.filter_by(first_name='Sample').first()
        self.assertIsNotNone(patient, "Sample patient not found for edit form test")
        response = self.client.get(f'/patients/{patient.id}/edit')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Edit Patient', response.data)
        self.assertIn(b'Sample', response.data) # Form should be pre-populated

    def test_edit_patient_logic(self):
        patient = models.Patient.query.filter_by(first_name='Sample').first()
        self.assertIsNotNone(patient, "Sample patient not found for edit logic test")

        response = self.client.post(f'/patients/{patient.id}/edit', data=dict(
            first_name='UpdatedSample',
            last_name='UserUpdated',
            date_of_birth=patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else '',
            contact_info='updated@example.com',
            anamnesis='Updated anamnesis'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200) # Should redirect to view_patient
        self.assertIn(b'UpdatedSample', response.data) # Check if updated data is on the detail page

        updated_patient = db.session.get(models.Patient, patient.id) # Re-fetch from DB
        self.assertEqual(updated_patient.first_name, 'UpdatedSample')
        self.assertEqual(updated_patient.contact_info, 'updated@example.com')

if __name__ == '__main__':
    unittest.main()
