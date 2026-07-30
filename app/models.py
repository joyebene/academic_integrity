# app/models.py - SIMPLIFIED VERSION

from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), default='student')
    department = db.Column(db.String(100))
    faculty = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    student_profile = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    lecturer_profile = db.relationship('Lecturer', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"<User {self.username}>"


class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    matric_number = db.Column(db.String(20), unique=True, nullable=False)
    level = db.Column(db.Integer)
    program = db.Column(db.String(100))
    advisor_id = db.Column(db.Integer, db.ForeignKey('lecturers.id'))
    
    def __repr__(self):
        return f"<Student {self.matric_number}>"


class Lecturer(db.Model):
    __tablename__ = 'lecturers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    staff_id = db.Column(db.String(20), unique=True, nullable=False)
    specialization = db.Column(db.String(100))
    courses = db.relationship('Course', backref='lecturer', lazy=True)
    
    def __repr__(self):
        return f"<Lecturer {self.staff_id}>"


class SystemLog(db.Model):
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemLog {self.id} - {self.action}>"


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturers.id'))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assignments = db.relationship(
        'Assignment',
        backref='course',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<Course {self.code}>"


class Assignment(db.Model):
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    due_date = db.Column(db.DateTime)

    is_active = db.Column(db.Boolean, default=True)

    course_id = db.Column(
        db.Integer,
        db.ForeignKey('courses.id'),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    submissions = db.relationship(
        'Submission',
        backref='assignment',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<Assignment {self.title}>"


class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)

    assignment_id = db.Column(
        db.Integer,
        db.ForeignKey('assignments.id'),
        nullable=False
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey('students.id'),
        nullable=False
    )

    file_path = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(255))

    comments = db.Column(db.Text)

    status = db.Column(
        db.String(30),
        default='processing'
    )

    submitted_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    student = db.relationship(
        'Student',
        backref=db.backref('submissions', lazy=True)
    )

    analysis = db.relationship(
        'AIAnalysis',
        backref='submission',
        uselist=False,
        cascade='all, delete-orphan'
    )

    suspicious = db.relationship(
        'SuspiciousSubmission',
        backref='submission',
        uselist=False,
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<Submission {self.id}>"


class AIAnalysis(db.Model):
    __tablename__ = 'ai_analysis'

    id = db.Column(db.Integer, primary_key=True)

    submission_id = db.Column(
        db.Integer,
        db.ForeignKey('submissions.id'),
        nullable=False,
        unique=True
    )

    plagiarism_score = db.Column(db.Float, default=0)

    ai_generated_score = db.Column(db.Float, default=0)

    analysis_details = db.Column(db.Text)

    model_version = db.Column(db.String(50))

    analyzed_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<AIAnalysis {self.id}>"


class SuspiciousSubmission(db.Model):
    __tablename__ = 'suspicious_submissions'

    id = db.Column(db.Integer, primary_key=True)

    submission_id = db.Column(
        db.Integer,
        db.ForeignKey('submissions.id'),
        nullable=False,
        unique=True
    )

    reason = db.Column(db.Text)

    severity = db.Column(db.String(20))

    reviewed = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<SuspiciousSubmission {self.id}>"

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    title = db.Column(db.String(200), nullable=False)

    message = db.Column(db.Text)

    type = db.Column(db.String(30), default='info')

    link = db.Column(db.String(255))

    is_read = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        'User',
        backref=db.backref('notifications', lazy=True)
    )

    def __repr__(self):
        return f"<Notification {self.id}>"

class Report(db.Model):

    __tablename__ = 'reports'

    id = db.Column(
        db.Integer,
        primary_key=True
    )


    submission_id = db.Column(
        db.Integer,
        db.ForeignKey('submissions.id'),
        nullable=False
    )


    generated_by = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )


    report_type = db.Column(
        db.String(100),
        default="AI Analysis Report"
    )


    plagiarism_score = db.Column(
        db.Float
    )


    ai_score = db.Column(
        db.Float
    )


    report_path = db.Column(
        db.String(500)
    )


    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


    submission = db.relationship(
        'Submission',
        backref='reports'
    )


    creator = db.relationship(
        'User',
        backref='generated_reports'
    )

    def __repr__(self):
        return f"<Report {self.id}>"