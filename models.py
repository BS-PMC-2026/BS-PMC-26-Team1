from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'student' or 'lecturer'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    student_id = db.Column(db.String(50))
    department = db.Column(db.String(100))
    year_of_study = db.Column(db.Integer)
    progress_percent = db.Column(db.Integer, default=0)
    
    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))

class LecturerProfile(db.Model):
    __tablename__ = 'lecturer_profiles'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    lecturer_id = db.Column(db.String(50))
    department = db.Column(db.String(100))
    academic_title = db.Column(db.String(100))
    
    user = db.relationship('User', backref=db.backref('lecturer_profile', uselist=False))

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    question_type = db.Column(db.String(50))
    difficulty = db.Column(db.String(50))
    starter_code = db.Column(db.Text)
    expected_output = db.Column(db.Text)
    explanation = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)

class QuestionOption(db.Model):
    __tablename__ = 'question_options'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    option_text = db.Column(db.String(255))
    is_correct = db.Column(db.Boolean)

class QuestionTestCase(db.Model):
    __tablename__ = 'question_test_cases'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    input_data = db.Column(db.Text)
    expected_output = db.Column(db.Text)
    is_hidden = db.Column(db.Boolean, default=True)

class ExerciseAttempt(db.Model):
    __tablename__ = 'exercise_attempts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # nullable for guests
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=True)
    selected_option_id = db.Column(db.Integer, db.ForeignKey('question_options.id'), nullable=True)
    submitted_code = db.Column(db.Text)
    submitted_output = db.Column(db.Text)
    is_correct = db.Column(db.Boolean, default=False)
    feedback_text = db.Column(db.Text)
    score = db.Column(db.Integer, default=0)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Legacy compatibility alias for old progress.html template
    @property
    def timestamp(self):
        return self.submitted_at

    user = db.relationship('User', backref=db.backref('exercise_attempts', lazy=True))

class ProgressRecord(db.Model):
    __tablename__ = 'progress_records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    intro_completed = db.Column(db.Boolean, default=False)
    pipeline_viewed = db.Column(db.Boolean, default=False)
    exercise_completed = db.Column(db.Boolean, default=False)
    correct_answers_count = db.Column(db.Integer, default=0)
    total_attempts = db.Column(db.Integer, default=0)
    score = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
