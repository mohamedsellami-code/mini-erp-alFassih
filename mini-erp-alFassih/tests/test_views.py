import unittest
import sys
import os
import io # For dummy file uploads
import shutil # For cleaning up upload folder

# Add the project root to sys.path to allow direct import of mini_erp_alFassih
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from mini_erp_alFassih.mini_erp_alFassih import app, db, models
# Explicitly import Patient and Document if needed, though models.Patient and models.Document also work
# from mini_erp_alFassih.mini_erp_alFassih.models import Patient, Document

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

        # Clean up the upload folder after tests
        upload_folder = app.config['UPLOAD_FOLDER']
        if os.path.exists(upload_folder):
            shutil.rmtree(upload_folder) # Recursively delete the folder and its contents

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

    # Document related view tests
    def test_upload_document_form_route(self):
        response = self.client.get(f'/patients/{self.sample_patient.id}/documents/upload')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Upload Document', response.data)
        self.assertIn(b'Document Title', response.data) # Check for a form field label
        self.assertIn(b'Document File', response.data)  # Check for file input field label

    def test_upload_document_logic(self):
        initial_doc_count = models.Document.query.count()
        upload_folder = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        data = {
            'title': 'My Test Upload',
            'document_type': 'Report',
            'description': 'A test file for upload.',
            'file': (io.BytesIO(b"this is a test file content"), 'test_upload.txt')
        }

        response = self.client.post(
            f'/patients/{self.sample_patient.id}/documents/upload',
            data=data,
            content_type='multipart/form-data',
            follow_redirects=True
        )

        self.assertEqual(response.status_code, 200) # Should redirect to patient detail page
        self.assertEqual(models.Document.query.count(), initial_doc_count + 1, "Document count should increment")

        doc = models.Document.query.filter_by(title='My Test Upload').first()
        self.assertIsNotNone(doc, "Document was not created in DB")
        self.assertEqual(doc.patient_id, self.sample_patient.id)
        self.assertTrue(os.path.exists(os.path.join(upload_folder, doc.filename)), "Uploaded file not found in UPLOAD_FOLDER")
        self.assertTrue(doc.filename.endswith('.txt'), "Uploaded file should have .txt extension")

        # Check if document title or filename appears on the patient detail page (after redirect)
        self.assertIn(b'My Test Upload', response.data)

    def test_download_document_route(self):
        # 1. Create a document record and a dummy file for it
        dummy_filename = "test_for_download.txt"
        upload_folder = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        file_path = os.path.join(upload_folder, dummy_filename)
        with open(file_path, 'wb') as f:
            f.write(b"dummy download content")

        doc = models.Document(
            patient_id=self.sample_patient.id,
            title="Downloadable Test File",
            filename=dummy_filename, # Filename as it's stored on server
            document_type="Test Download"
        )
        db.session.add(doc)
        db.session.commit()

        # 2. Test the download route
        response = self.client.get(f'/documents/{doc.id}/download')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/plain') # Flask infers this for .txt
        self.assertIn(b"dummy download content", response.data)
        self.assertIn(f'attachment; filename={dummy_filename}', response.headers['Content-Disposition'])

    def test_list_documents_on_patient_page(self):
        # 1. Create a document associated with the sample patient
        doc_title = "Listed Document Test"
        doc = models.Document(
            patient_id=self.sample_patient.id,
            title=doc_title,
            filename="listed_doc.pdf",
            document_type="List Test"
        )
        db.session.add(doc)
        db.session.commit()

        # 2. Access the patient detail page
        response = self.client.get(f'/patients/{self.sample_patient.id}')
        self.assertEqual(response.status_code, 200)

        # 3. Check if the document's title or filename is on the page
        self.assertIn(doc_title.encode('utf-8'), response.data)
        self.assertIn(b"listed_doc.pdf", response.data)


if __name__ == '__main__':
    unittest.main()
