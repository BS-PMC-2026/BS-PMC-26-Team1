import json
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student / lecturer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)


class StudentProfile(db.Model):
    __tablename__ = "student_profiles"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    student_id = db.Column(db.String(50))
    department = db.Column(db.String(100))
    year_of_study = db.Column(db.Integer)
    progress_percent = db.Column(db.Integer, default=0)

    user = db.relationship("User", backref=db.backref("student_profile", uselist=False))


class LecturerProfile(db.Model):
    __tablename__ = "lecturer_profiles"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    lecturer_id = db.Column(db.String(50))
    department = db.Column(db.String(100))
    academic_title = db.Column(db.String(100))

    user = db.relationship("User", backref=db.backref("lecturer_profile", uselist=False))


class Module(db.Model):
    __tablename__ = "modules"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    display_order = db.Column(db.Integer, nullable=False, default=1)
    route = db.Column(db.String(120), nullable=False, default="/")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # mcq / code / open
    options_json = db.Column(db.Text)  # JSON array for MCQ
    correct_answer = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(50), nullable=False, default="medium")
    module_id = db.Column(db.Integer, db.ForeignKey("modules.id"), nullable=False)
    starter_code = db.Column(db.Text)
    test_cases_json = db.Column(db.Text)  # JSON list for code tasks
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    module = db.relationship("Module", backref=db.backref("questions", lazy=True))
    author = db.relationship("User", backref=db.backref("created_questions", lazy=True))

    # Backward compatibility for existing templates/tests
    @property
    def title(self):
        return self.question_text[:120]

    @property
    def description(self):
        return self.question_text

    @property
    def type(self):
        return self.question_type

    @property
    def content(self):
        return self.question_text

    @property
    def expected_answer(self):
        return self.correct_answer

    @property
    def options(self):
        if not self.options_json:
            return []
        try:
            parsed = json.loads(self.options_json)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    @property
    def code_test_cases(self):
        if not self.test_cases_json:
            return []
        try:
            parsed = json.loads(self.test_cases_json)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []


class QuestionOption(db.Model):
    __tablename__ = "question_options"
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"))
    option_text = db.Column(db.String(255))
    is_correct = db.Column(db.Boolean)


class QuestionTestCase(db.Model):
    __tablename__ = "question_test_cases"
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"))
    input_data = db.Column(db.Text)
    expected_output = db.Column(db.Text)
    is_hidden = db.Column(db.Boolean, default=True)


class ExerciseAttempt(db.Model):
    __tablename__ = "exercise_attempts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=True)
    answer = db.Column(db.Text)
    submitted_output = db.Column(db.Text)
    is_correct = db.Column(db.Boolean, default=False)
    feedback_text = db.Column(db.Text)
    score = db.Column(db.Integer, default=0)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("exercise_attempts", lazy=True))
    question = db.relationship("Question", backref=db.backref("attempts", lazy=True))

    @property
    def timestamp(self):
        return self.submitted_at

    # Backward compatibility alias
    @property
    def submitted_code(self):
        return self.answer


class ProgressRecord(db.Model):
    __tablename__ = "progress_records"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True)
    intro_completed = db.Column(db.Boolean, default=False)
    pipeline_viewed = db.Column(db.Boolean, default=False)
    exercise_completed = db.Column(db.Boolean, default=False)
    correct_answers_count = db.Column(db.Integer, default=0)
    total_attempts = db.Column(db.Integer, default=0)
    score = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModuleProgress(db.Model):
    __tablename__ = "module_progress"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey("modules.id"), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    progress_percentage = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("module_progress", lazy=True))
    module = db.relationship("Module", backref=db.backref("module_progress_rows", lazy=True))
    __table_args__ = (db.UniqueConstraint("user_id", "module_id", name="uq_module_progress_user_module"),)


class AnalyticsRecord(db.Model):
    __tablename__ = "analytics_records"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey("modules.id"), nullable=False)
    avg_score = db.Column(db.Float, default=0.0)
    attempts_count = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float, default=0.0)
    last_refreshed = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("analytics_records", lazy=True))
    module = db.relationship("Module", backref=db.backref("analytics_records", lazy=True))
    __table_args__ = (db.UniqueConstraint("user_id", "module_id", name="uq_analytics_user_module"),)
