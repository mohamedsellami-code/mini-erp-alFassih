from . import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model): # Inherit from UserMixin
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256)) # Increased length for future hash algorithms
    role = db.Column(db.String(80), default='therapist', nullable=False) # Default role, e.g. 'therapist', 'admin', 'staff'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    # created_at = db.Column(db.DateTime, default=datetime.utcnow) # Optional: track user creation

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False, index=True)
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
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False, index=True)
    document_type = db.Column(db.String(100), nullable=True) # Or False if always required
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Document {self.title}>'

class Therapist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, unique=True, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False, index=True)
    specialization = db.Column(db.String(150), nullable=True)
    sessions = db.relationship('Session', backref='assigned_therapist', lazy='dynamic', cascade="all, delete-orphan")
    user = db.relationship('User', backref=db.backref('therapist_profile', uselist=False))

    def __repr__(self):
        return f'<Therapist {self.first_name} {self.last_name}>'

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False, index=True)
    therapist_id = db.Column(db.Integer, db.ForeignKey('therapist.id'), nullable=False, index=True)
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    end_time = db.Column(db.DateTime, nullable=False)
    session_type = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(50), default='Scheduled', nullable=False, index=True) # E.g., 'Scheduled', 'Completed', 'Cancelled', 'No Show'
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Session {self.id} Patient {self.patient_id} Therapist {self.therapist_id} on {self.start_time.strftime("%Y-%m-%d %H:%M")}>'
