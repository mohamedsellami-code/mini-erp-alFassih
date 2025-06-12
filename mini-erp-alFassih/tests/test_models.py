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

if __name__ == '__main__':
    unittest.main()
