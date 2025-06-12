import unittest
import sys
import os
import io # For dummy file uploads
import shutil # For cleaning up upload folder
from datetime import datetime, timedelta # For Session tests
from flask import url_for # Added url_for

# Add the project root to sys.path to allow direct import of mini_erp_alFassih
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from mini_erp_alFassih.mini_erp_alFassih import app, db, models

class TestPatientViews(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = app.app_context()
        self.app_context.push()
        self.client = app.test_client()
        db.create_all()

        # Create a user for patient view tests
        self.test_user = models.User(email='patient_testuser@example.com', role='therapist') # Or a generic role
        self.test_user.set_password('testpass')
        db.session.add(self.test_user)
        db.session.commit()

        # Log in the user
        self.client.post(url_for('auth.login'), data=dict(
            email='patient_testuser@example.com',
            password='testpass'
        ), follow_redirects=True)

        self.sample_patient = models.Patient(first_name='Sample', last_name='User', contact_info='sample@example.com')
        db.session.add(self.sample_patient)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        upload_folder = app.config.get('UPLOAD_FOLDER')
        if upload_folder and os.path.exists(upload_folder):
            shutil.rmtree(upload_folder)
        self.app_context.pop()

    def test_list_patients_route(self):
        response = self.client.get(url_for('patients.list_patients'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Patients', response.data)
        self.assertIn(b'Sample', response.data)

    def test_create_patient_form_route(self):
        response = self.client.get(url_for('patients.create_patient'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create Patient', response.data)

    def test_create_patient_logic(self):
        initial_patient_count = models.Patient.query.count()
        response = self.client.post(url_for('patients.create_patient'), data=dict(
            first_name='New', last_name='Patient', date_of_birth='2000-01-01',
            contact_info='new@example.com', anamnesis='Test anamnesis'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(models.Patient.query.count(), initial_patient_count + 1)
        self.assertIn(b'New', response.data)

    def test_view_patient_route(self):
        response = self.client.get(url_for('patients.view_patient', patient_id=self.sample_patient.id))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Patient Details', response.data)
        self.assertIn(b'Sample', response.data)

    def test_edit_patient_form_route(self):
        response = self.client.get(url_for('patients.edit_patient', patient_id=self.sample_patient.id))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Edit Patient', response.data)

    def test_edit_patient_logic(self):
        response = self.client.post(url_for('patients.edit_patient', patient_id=self.sample_patient.id), data=dict(
            first_name='UpdatedSample', last_name='UserUpdated', contact_info='updated@example.com'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'UpdatedSample', response.data)
        updated_patient = db.session.get(models.Patient, self.sample_patient.id)
        self.assertEqual(updated_patient.first_name, 'UpdatedSample')

    def test_upload_document_form_route(self):
        response = self.client.get(url_for('patients.upload_document', patient_id=self.sample_patient.id))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Upload Document', response.data)

    def test_upload_document_logic(self):
        data = {'title': 'My Test Upload', 'file': (io.BytesIO(b"test content"), 'test.txt')}
        response = self.client.post(url_for('patients.upload_document', patient_id=self.sample_patient.id),
                                    data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'My Test Upload', response.data) # Check document title on patient page

    def test_download_document_route(self):
        dummy_filename = "download_test.txt"
        upload_folder = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder): os.makedirs(upload_folder)
        with open(os.path.join(upload_folder, dummy_filename), 'wb') as f: f.write(b"download content")
        doc = models.Document(patient_id=self.sample_patient.id, title="Downloadable", filename=dummy_filename)
        db.session.add(doc)
        db.session.commit()
        response = self.client.get(url_for('patients.download_document', document_id=doc.id))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"download content", response.data)

    def test_list_documents_on_patient_page(self):
        doc = models.Document(patient_id=self.sample_patient.id, title="Listed Doc", filename="listed.pdf")
        db.session.add(doc)
        db.session.commit()
        response = self.client.get(url_for('patients.view_patient', patient_id=self.sample_patient.id))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Listed Doc", response.data)

class TestAuthViews(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = app.app_context()
        self.app_context.push()
        self.client = app.test_client()
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
        return self.client.post(url_for('auth.login'), data=dict(email=email, password=password), follow_redirects=True)

    def logout(self):
        return self.client.get(url_for('auth.logout'), follow_redirects=True)

    def test_login_logout_successful(self):
        response = self.login(self.admin_user.email, 'adminpass')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged in successfully!', response.data)
        self.assertIn(url_for('main.home'), response.request.path)

        response_protected = self.client.get(url_for('patients.list_patients'))
        self.assertEqual(response_protected.status_code, 200)

        response_logout = self.logout()
        self.assertEqual(response_logout.status_code, 200)
        self.assertIn(b'You have been logged out.', response_logout.data)
        self.assertIn(url_for('auth.login'), response.request.path)

        response_protected_after_logout = self.client.get(url_for('patients.list_patients'), follow_redirects=False)
        self.assertEqual(response_protected_after_logout.status_code, 302)
        self.assertTrue(response_protected_after_logout.location.endswith(url_for('auth.login', next=url_for('patients.list_patients'))))

    def test_login_invalid_credentials(self):
        response = self.login(self.admin_user.email, 'wrongpassword')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid email or password', response.data)
        self.assertIn(url_for('auth.login'), response.request.path)

    def test_access_protected_route_unauthenticated(self):
        response = self.client.get(url_for('patients.list_patients'), follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith(url_for('auth.login', next=url_for('patients.list_patients'))))

    def test_access_protected_route_authenticated_therapist(self):
        self.login(self.therapist_user.email, 'therapass')
        response = self.client.get(url_for('patients.list_patients'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Patients", response.data)

class TestTherapistAdminViews(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = app.app_context()
        self.app_context.push()
        self.client = app.test_client()
        db.create_all()
        # Create an admin user to perform admin actions
        self.admin_user = models.User(email='adminfortheratest@example.com', role='admin')
        self.admin_user.set_password('adminpass')
        db.session.add(self.admin_user)
        db.session.commit()
        # Log in this admin user
        self.client.post(url_for('auth.login'), data={'email': 'adminfortheratest@example.com', 'password': 'adminpass'})


    def tearDown(self):
        db.session.remove()
        db.drop_all()
        upload_folder = app.config.get('UPLOAD_FOLDER')
        if upload_folder and os.path.exists(upload_folder):
            shutil.rmtree(upload_folder)
        self.app_context.pop()

    def test_list_therapists_route(self):
        response = self.client.get(url_for('admin.list_therapists'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Manage Therapists", response.data)

    def test_create_therapist_form_route(self):
        response = self.client.get(url_for('admin.create_therapist'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Add New Therapist", response.data)

    def test_create_therapist_with_user_logic(self):
        initial_user_count = models.User.query.count()
        initial_therapist_count = models.Therapist.query.count()
        response = self.client.post(url_for('admin.create_therapist'), data={
            'first_name': 'Dr. New', 'last_name': 'UserTherapist', 'specialization': 'Integration Testing',
            'email': 'newtherapist@example.com', 'password': 'newpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(models.User.query.count(), initial_user_count + 1)
        self.assertEqual(models.Therapist.query.count(), initial_therapist_count + 1)
        new_user = models.User.query.filter_by(email='newtherapist@example.com').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.role, 'therapist')
        new_therapist_profile = models.Therapist.query.filter_by(user_id=new_user.id).first()
        self.assertIsNotNone(new_therapist_profile)
        self.assertEqual(new_therapist_profile.last_name, 'UserTherapist')
        self.assertIn(b"New UserTherapist", response.data)

    def test_edit_therapist_form_route(self):
        therapist = models.Therapist(first_name="Edit", last_name="Me", specialization="Editing")
        db.session.add(therapist)
        db.session.commit()
        response = self.client.get(url_for('admin.edit_therapist', therapist_id=therapist.id))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Edit Me", response.data)

    def test_delete_therapist_logic(self):
        therapist = models.Therapist(first_name="Delete", last_name="Me", specialization="Deleting")
        db.session.add(therapist)
        db.session.commit()
        therapist_id = therapist.id
        response = self.client.post(url_for('admin.delete_therapist', therapist_id=therapist_id)) # No redirect for AJAX
        self.assertEqual(response.status_code, 200) # JSON success
        self.assertIsNone(models.Therapist.query.get(therapist_id))

class TestSessionViews(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = app.app_context()
        self.app_context.push()
        self.client = app.test_client()
        db.create_all()

        # Create a user for the therapist profile
        self.therapist_user_account = models.User(email='session_therapist_user@example.com', role='therapist', first_name='Dr. SessionUser', is_active=True)
        self.therapist_user_account.set_password('therapass')
        db.session.add(self.therapist_user_account)
        db.session.commit() # Commit user first to get ID

        self.patient = models.Patient(first_name='SessionPt', last_name='Patient')
        # Ensure therapist profile is linked to the user account
        self.therapist = models.Therapist(
            first_name='Dr. SessionView',
            last_name='Test',
            user_id=self.therapist_user_account.id # Link to the user
        )
        db.session.add_all([self.patient, self.therapist])
        db.session.commit()

        # Log in as the therapist user (or another general authenticated user)
        self.client.post(url_for('auth.login'), data=dict(
            email='session_therapist_user@example.com',
            password='therapass'
        ), follow_redirects=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        upload_folder = app.config.get('UPLOAD_FOLDER')
        if upload_folder and os.path.exists(upload_folder):
            shutil.rmtree(upload_folder)
        self.app_context.pop()

    def test_list_sessions_route(self):
        response = self.client.get(url_for('sessions.list_sessions'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"All Sessions", response.data)

    def test_create_session_form_route(self):
        response = self.client.get(url_for('sessions.create_session'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Schedule New Session", response.data)

    def test_create_session_logic(self):
        initial_session_count = models.Session.query.count()
        now = datetime.utcnow()
        start_time = now + timedelta(hours=1); end_time = now + timedelta(hours=2)
        response = self.client.post(url_for('sessions.create_session'), data={
            'patient': self.patient.id, 'therapist': self.therapist.id,
            'start_time': start_time.strftime('%Y-%m-%dT%H:%M'), 'end_time': end_time.strftime('%Y-%m-%dT%H:%M'),
            'session_type': 'Consultation', 'status': 'Scheduled', 'notes': 'Test notes.'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(models.Session.query.count(), initial_session_count + 1)
        self.assertIn(self.patient.first_name.encode('utf-8'), response.data)

    def test_cancel_session_logic(self):
        now = datetime.utcnow()
        start_time = now + timedelta(days=1); end_time = start_time + timedelta(hours=1)
        session = models.Session(patient_id=self.patient.id, therapist_id=self.therapist.id,
                                 start_time=start_time, end_time=end_time, status='Scheduled')
        db.session.add(session)
        db.session.commit()
        response = self.client.post(url_for('sessions.cancel_session', session_id=session.id))
        self.assertEqual(response.status_code, 200) # JSON success
        cancelled_session = db.session.get(models.Session, session.id)
        self.assertEqual(cancelled_session.status, 'Cancelled')

class TestAdminDashboardView(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        # Create users needed for dashboard tests
        self.admin_user = models.User(email='dashadmin@example.com', role='admin')
        self.admin_user.set_password('adminpass')
        self.therapist_user = models.User(email='dashtherapist@example.com', role='therapist')
        self.therapist_user.set_password('therapass')
        self.patient = models.Patient(first_name='DashPt', last_name='User', created_at=datetime.utcnow() - timedelta(days=3))
        # Therapist profile for the therapist user
        self.therapist_profile = models.Therapist(first_name='Dr. DashBoard', last_name='Test', user=self.therapist_user)
        db.session.add_all([self.admin_user, self.therapist_user, self.patient, self.therapist_profile])
        db.session.commit()
        # Upcoming session
        session_time = datetime.utcnow() + timedelta(hours=2)
        self.session = models.Session(patient_id=self.patient.id, therapist_id=self.therapist_profile.id,
                                     start_time=session_time, end_time=session_time + timedelta(hours=1), status='Scheduled')
        self.document = models.Document(patient_id=self.patient.id, title="Dash Doc", filename="dash.pdf")
        db.session.add_all([self.session, self.document])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        upload_folder = app.config.get('UPLOAD_FOLDER')
        if upload_folder and os.path.exists(upload_folder):
            shutil.rmtree(upload_folder)

    def _login(self, email, password): # Helper for this class
        return self.client.post(url_for('auth.login'), data={'email': email, 'password': password}, follow_redirects=True)

    def test_admin_dashboard_unauthenticated(self):
        response = self.client.get(url_for('admin.admin_dashboard'), follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith(url_for('auth.login', next=url_for('admin.admin_dashboard'))))

    def test_admin_dashboard_as_admin(self):
        self._login('dashadmin@example.com', 'adminpass')
        response = self.client.get(url_for('admin.admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Admin Dashboard", response.data)
        self.assertIn(b"Total Patients: 1", response.data)
        self.assertIn(b"DashPt User", response.data) # Recent patient
        self.assertIn(b"Dr. DashBoard Test", response.data) # Therapist in upcoming session

    def test_admin_dashboard_as_non_admin(self):
        self._login('dashtherapist@example.com', 'therapass')
        response = self.client.get(url_for('admin.admin_dashboard'), follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(url_for('main.home'), response.location)
        response_redirect = self.client.get(response.location)
        self.assertIn(b"You do not have permission", response_redirect.data)

if __name__ == '__main__':
    unittest.main()
