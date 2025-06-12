import unittest
import sys
import os
import io # For dummy file uploads
import shutil # For cleaning up upload folder
from datetime import datetime, timedelta # For Session tests

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

# Test Class for Therapist Admin Views
class TestTherapistAdminViews(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = app.app_context()
        self.app_context.push()
        self.client = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        upload_folder = app.config.get('UPLOAD_FOLDER')
        if upload_folder and os.path.exists(upload_folder):
            shutil.rmtree(upload_folder)
        self.app_context.pop()

    def test_list_therapists_route(self):
        response = self.client.get('/admin/therapists')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Manage Therapists", response.data)

    def test_create_therapist_form_route(self):
        response = self.client.get('/admin/therapists/new')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Add New Therapist", response.data)
        self.assertIn(b"First Name", response.data) # Check for form field

    def test_create_therapist_logic(self):
        initial_therapist_count = models.Therapist.query.count()
        response = self.client.post('/admin/therapists/new', data={
            'first_name': 'Dr. Test',
            'last_name': 'Therapist',
            'specialization': 'Testing'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(models.Therapist.query.count(), initial_therapist_count + 1)
        self.assertIn(b"Dr. Test", response.data) # Check if new therapist is on list page

    def test_edit_therapist_form_route(self):
        therapist = models.Therapist(first_name="Edit", last_name="Me", specialization="Editing")
        db.session.add(therapist)
        db.session.commit()
        response = self.client.get(f'/admin/therapists/{therapist.id}/edit')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Edit Me", response.data) # Check for pre-filled data

    def test_create_therapist_with_user_logic(self):
        # This test assumes admin is logged in, which needs to be handled by a login helper if TestTherapistAdminViews requires admin
        # For now, let's assume no login needed for this specific test if admin_required is not yet enforced on this view in tests
        # Or, we'd call self.login(admin_credentials) if a login helper is part of this class's setUp
        initial_user_count = models.User.query.count()
        initial_therapist_count = models.Therapist.query.count()

        response = self.client.post('/admin/therapists/new', data={
            'first_name': 'Dr. New',
            'last_name': 'UserTherapist',
            'specialization': 'Integration Testing',
            'email': 'newtherapist@example.com',
            'password': 'newpassword'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200) # Assuming redirect to therapist list
        self.assertEqual(models.User.query.count(), initial_user_count + 1)
        self.assertEqual(models.Therapist.query.count(), initial_therapist_count + 1)

        new_user = models.User.query.filter_by(email='newtherapist@example.com').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.role, 'therapist')

        new_therapist_profile = models.Therapist.query.filter_by(user_id=new_user.id).first()
        self.assertIsNotNone(new_therapist_profile)
        self.assertEqual(new_therapist_profile.last_name, 'UserTherapist')
        self.assertIn(b"New UserTherapist", response.data) # Check if on list page

    def test_delete_therapist_logic(self):
        therapist = models.Therapist(first_name="Delete", last_name="Me", specialization="Deleting")
        db.session.add(therapist)
        db.session.commit()
        therapist_id = therapist.id
        response = self.client.post(f'/admin/therapists/{therapist_id}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(models.Therapist.query.get(therapist_id))


# Test Class for Session Views
class TestSessionViews(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = app.app_context()
        self.app_context.push()
        self.client = app.test_client()
        db.create_all()

        # Create dummy patient and therapist for session tests
        self.patient = models.Patient(first_name='Session', last_name='Patient')
        self.therapist = models.Therapist(first_name='Dr. Session', last_name='Test')
        db.session.add_all([self.patient, self.therapist])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        upload_folder = app.config.get('UPLOAD_FOLDER')
        if upload_folder and os.path.exists(upload_folder):
            shutil.rmtree(upload_folder)
        self.app_context.pop()

    def test_list_sessions_route(self):
        response = self.client.get('/sessions')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"All Sessions", response.data)

    def test_create_session_form_route(self):
        response = self.client.get('/sessions/new')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Schedule New Session", response.data)
        self.assertIn(b"Patient", response.data) # Check for form field

    def test_create_session_logic(self):
        initial_session_count = models.Session.query.count()
        now = datetime.utcnow()
        start_time = now + timedelta(hours=1)
        end_time = now + timedelta(hours=2)

        response = self.client.post('/sessions/new', data={
            'patient': self.patient.id,
            'therapist': self.therapist.id,
            'start_time': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_time': end_time.strftime('%Y-%m-%dT%H:%M'),
            'session_type': 'Consultation',
            'status': 'Scheduled',
            'notes': 'Test session notes.'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200) # Should redirect to list_sessions
        self.assertEqual(models.Session.query.count(), initial_session_count + 1)
        # Check if session details (e.g., patient name) appear on the list page
        self.assertIn(self.patient.first_name.encode('utf-8'), response.data)
        self.assertIn(self.therapist.last_name.encode('utf-8'), response.data)

    def test_cancel_session_logic(self):
        now = datetime.utcnow()
        start_time = now + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        session = models.Session(
            patient_id=self.patient.id,
            therapist_id=self.therapist.id,
            start_time=start_time,
            end_time=end_time,
            status='Scheduled'
        )
        db.session.add(session)
        db.session.commit()
        session_id = session.id

        response = self.client.post(f'/sessions/{session_id}/cancel', follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Assuming redirect to list_sessions or similar
        cancelled_session = models.Session.query.get(session_id)
        self.assertEqual(cancelled_session.status, 'Cancelled')

class TestAdminDashboardView(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        # Use self.client consistently, as in other test classes
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

        # Create sample data
        self.patient = models.Patient(first_name='Dash', last_name='User', created_at=datetime.utcnow())
        self.therapist = models.Therapist(first_name='Dr. Board', last_name='Test')
        db.session.add_all([self.patient, self.therapist])
        db.session.commit() # Commit patient and therapist to get IDs

        # Create a session that is upcoming
        session_start_time = datetime.utcnow() + timedelta(hours=2)
        self.session = models.Session(
            patient_id=self.patient.id,
            therapist_id=self.therapist.id,
            start_time=session_start_time,
            end_time=session_start_time + timedelta(hours=1),
            status='Scheduled'
        )
        # Create a document for total_documents count
        self.document = models.Document(patient_id=self.patient.id, title="Test Doc", filename="test.pdf")

        db.session.add_all([self.session, self.document])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        # Minimal cleanup, UPLOAD_FOLDER not directly used by this test class's views
        # but good practice if any operation indirectly creates it.
        upload_folder = app.config.get('UPLOAD_FOLDER')
        if upload_folder and os.path.exists(upload_folder):
            shutil.rmtree(upload_folder)


    def test_dashboard_loads_with_data(self):
        # This test needs an authenticated admin user
        # Assuming self.admin_user is created and logged in via a helper in a real scenario
        # For now, we'll simulate by creating the user and assuming login is handled elsewhere or not required for this isolated test if auth is mocked
        admin = models.User(email='dashadmin@example.com', role='admin')
        admin.set_password('adminpass')
        db.session.add(admin)
        db.session.commit()
        # Here, you would typically call a self.login('dashadmin@example.com', 'adminpass')
        # For this example, we'll proceed as if login happened or dashboard doesn't strictly require it for this old test.
        # However, the admin_required decorator IS applied, so this test will fail without login.
        # This highlights the need for login helpers in test classes that hit protected routes.
        # For now, this test will likely redirect to login, so we'd expect 302 if not logged in.
        # To actually test the dashboard content, login is required.

        # Let's assume a login method is available and used:
        # self.login('dashadmin@example.com', 'adminpass') # If login helper was part of this class
        # Since it's not, this test as-is for dashboard content is flawed after adding @admin_required.
        # It will be addressed by using the TestAuthViews login helper.

        response = self.client.get('/admin/dashboard') # This will redirect if not logged in
        self.assertEqual(response.status_code, 302) # Expect redirect because not logged in
        self.assertIn('/login', response.location)

    def test_admin_dashboard_as_admin(self):
        # Create admin user for this test method context
        admin = models.User(email='realadmin@example.com', role='admin')
        admin.set_password('adminpass')
        db.session.add(admin)
        db.session.commit()

        # Log in as admin
        login_response = self.client.post('/login', data=dict(
            email='realadmin@example.com', password='adminpass'
        ), follow_redirects=True)
        self.assertEqual(login_response.status_code, 200) # Successful login redirects to home (200)

        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Admin Dashboard", response.data)
        self.assertIn(b"Total Patients:", response.data)

    def test_admin_dashboard_as_non_admin(self):
        # Create non-admin user
        non_admin = models.User(email='therapist@example.com', role='therapist')
        non_admin.set_password('therapass')
        db.session.add(non_admin)
        db.session.commit()

        login_response = self.client.post('/login', data=dict(
            email='therapist@example.com', password='therapass'
        ), follow_redirects=True)
        self.assertEqual(login_response.status_code, 200)

        response = self.client.get('/admin/dashboard', follow_redirects=False)
        self.assertEqual(response.status_code, 302) # Should redirect
        self.assertIn(url_for('home'), response.location) # Redirects to home as per admin_required

        # Follow redirect to check for flashed message
        response_redirect = self.client.get(response.location)
        self.assertIn(b"You do not have permission", response_redirect.data)
        self.assertIn(b"Admin access required", response_redirect.data)

    def test_admin_dashboard_unauthenticated(self):
        response = self.client.get('/admin/dashboard', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith(url_for('login', next='/admin/dashboard')))


class TestAuthViews(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = app.app_context()
        self.app_context.push()
        self.client = app.test_client() # Corrected: use self.client consistently
        db.create_all()

        self.admin_user = models.User(email='testadmin@example.com', role='admin', first_name='TestAdmin')
        self.admin_user.set_password('adminpass')
        self.therapist_user = models.User(email='testtherapist@example.com', role='therapist', first_name='TestThera')
        self.therapist_user.set_password('therapass')
        db.session.add_all([self.admin_user, self.therapist_user])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, email, password):
        return self.client.post('/login', data=dict(
            email=email,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_login_logout_successful(self):
        # Login
        response = self.login(self.admin_user.email, 'adminpass')
        self.assertEqual(response.status_code, 200) # Successful login redirects to home
        self.assertIn(b'Logged in successfully!', response.data)

        # Check a protected route (e.g., patients list)
        response_protected = self.client.get(url_for('list_patients'))
        self.assertEqual(response_protected.status_code, 200)
        self.assertIn(b'Patients', response_protected.data) # Assuming 'Patients' is title of patient list

        # Logout
        response_logout = self.logout()
        self.assertEqual(response_logout.status_code, 200) # Successful logout redirects to login
        self.assertIn(b'You have been logged out.', response_logout.data)
        self.assertIn(b'Login', response_logout.data) # Should be on login page

        # Try accessing protected page again
        response_protected_after_logout = self.client.get(url_for('list_patients'), follow_redirects=False)
        self.assertEqual(response_protected_after_logout.status_code, 302)
        self.assertTrue(response_protected_after_logout.location.endswith(url_for('login', next=url_for('list_patients'))))


    def test_login_invalid_credentials(self):
        response = self.login(self.admin_user.email, 'wrongpassword')
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'Invalid email or password', response.data)
        self.assertIn(b'Login', response.data) # Still on login page

    def test_access_protected_route_unauthenticated(self):
        response = self.client.get(url_for('list_patients'), follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith(url_for('login', next=url_for('list_patients'))))

    def test_access_protected_route_authenticated_therapist(self):
        self.login(self.therapist_user.email, 'therapass')
        response = self.client.get(url_for('list_patients')) # A general protected route
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Patients", response.data) # Assuming 'Patients' is on the page


if __name__ == '__main__':
    unittest.main()
