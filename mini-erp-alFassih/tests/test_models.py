import unittest
import sys
import os
from datetime import datetime, timedelta # Added for Session tests

# Add the project root to sys.path to allow direct import of mini_erp_alFassih
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from mini_erp_alFassih.mini_erp_alFassih import app, db, models
# models.Patient, models.Therapist, models.Session will be used

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

class TestDocumentModel(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

        # Create a dummy patient for use in document tests
        self.patient = models.Patient(first_name='Test', last_name='PatientForDoc')
        db.session.add(self.patient)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_document(self):
        # Create a Document instance
        doc = models.Document(
            patient_id=self.patient.id,
            title='Test Document',
            document_type='Test Type',
            filename='test_document.pdf'
        )
        db.session.add(doc)
        db.session.commit()

        # Assert that the document was created
        self.assertEqual(models.Document.query.count(), 1)

        # Retrieve the document and check details
        retrieved_document = models.Document.query.first()
        self.assertIsNotNone(retrieved_document)
        self.assertEqual(retrieved_document.title, 'Test Document')
        self.assertEqual(retrieved_document.patient_id, self.patient.id)

        # Assert relationship
        self.assertEqual(len(self.patient.documents), 1)
        self.assertEqual(self.patient.documents[0].title, 'Test Document')
        self.assertIn(retrieved_document, self.patient.documents)

class TestTherapistModel(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_therapist(self):
        therapist = models.Therapist(
            first_name='Dr. Jane',
            last_name='Doe',
            specialization='Psychology'
        )
        db.session.add(therapist)
        db.session.commit()

        self.assertEqual(models.Therapist.query.count(), 1)
        retrieved_therapist = models.Therapist.query.first()
        self.assertIsNotNone(retrieved_therapist)
        self.assertEqual(retrieved_therapist.first_name, 'Dr. Jane')
        self.assertEqual(retrieved_therapist.specialization, 'Psychology')

class TestSessionModel(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

        self.patient = models.Patient(first_name='Test', last_name='PatientForSession')
        self.therapist = models.Therapist(first_name='Dr.', last_name='TestTherapist', specialization='Counseling')
        db.session.add_all([self.patient, self.therapist])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_session(self):
        now = datetime.utcnow()
        start_time = now + timedelta(hours=1)
        end_time = now + timedelta(hours=2)

        session = models.Session(
            patient_id=self.patient.id,
            therapist_id=self.therapist.id,
            start_time=start_time,
            end_time=end_time,
            session_type='Initial Consultation',
            status='Scheduled',
            notes='Patient seems anxious.'
        )
        db.session.add(session)
        db.session.commit()

        self.assertEqual(models.Session.query.count(), 1)
        retrieved_session = models.Session.query.first()
        self.assertIsNotNone(retrieved_session)
        self.assertEqual(retrieved_session.patient_id, self.patient.id)
        self.assertEqual(retrieved_session.therapist_id, self.therapist.id)
        self.assertEqual(retrieved_session.status, 'Scheduled')
        self.assertEqual(retrieved_session.session_type, 'Initial Consultation')

        # Test relationships from Patient and Therapist sides
        self.assertEqual(self.patient.sessions.count(), 1)
        self.assertEqual(self.therapist.sessions.count(), 1)
        self.assertEqual(self.patient.sessions.first().id, retrieved_session.id)
        self.assertEqual(self.therapist.sessions.first().id, retrieved_session.id)

        # Test backrefs from Session side
        self.assertEqual(retrieved_session.assigned_patient, self.patient)
        self.assertEqual(retrieved_session.assigned_therapist, self.therapist)


if __name__ == '__main__':
    unittest.main()
