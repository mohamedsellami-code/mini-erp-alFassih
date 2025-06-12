from . import db
from datetime import datetime

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    contact_info = db.Column(db.Text, nullable=True)
    anamnesis = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    documents = db.relationship('Document', backref='patient', lazy=True, cascade="all, delete-orphan")
    sessions = db.relationship('Session', backref='assigned_patient', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Patient {self.id}: {self.first_name} {self.last_name}>'

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    document_type = db.Column(db.String(100), nullable=True) # Or False if always required
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Document {self.title}>'

class Therapist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(150), nullable=True)
    # Add a placeholder for sessions relationship, will be defined fully in next step
    sessions = db.relationship('Session', backref='assigned_therapist', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Therapist {self.first_name} {self.last_name}>'

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    therapist_id = db.Column(db.Integer, db.ForeignKey('therapist.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    session_type = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(50), default='Scheduled', nullable=False) # E.g., 'Scheduled', 'Completed', 'Cancelled', 'No Show'
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Session {self.id} Patient {self.patient_id} Therapist {self.therapist_id} on {self.start_time.strftime("%Y-%m-%d %H:%M")}>'
