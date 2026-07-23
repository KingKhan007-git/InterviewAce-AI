from datetime import datetime, timezone
import json
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    interviews = db.relationship('Interview', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, username=None, email=None, password_hash=None, **kwargs):
        super().__init__(**kwargs)
        if username:
            self.username = username
        if email:
            self.email = email
        if password_hash:
            self.password_hash = password_hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Interview(db.Model):
    __tablename__ = 'interviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(64), nullable=False)
    difficulty = db.Column(db.String(32), default='Medium')
    interview_type = db.Column(db.String(32), default='role') # 'role' or 'resume'
    resume_filename = db.Column(db.String(256), nullable=True)
    overall_score = db.Column(db.Integer, nullable=True) # Score 0-100
    summary_feedback = db.Column(db.Text, nullable=True)
    strengths_json = db.Column(db.Text, nullable=True) # JSON list of strength strings
    weaknesses_json = db.Column(db.Text, nullable=True) # JSON list of weakness strings
    status = db.Column(db.String(32), default='in_progress') # 'in_progress', 'completed'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    questions = db.relationship('Question', backref='interview', lazy='joined', cascade='all, delete-orphan', order_by='Question.question_order')

    def __init__(self, user_id=None, title=None, role=None, difficulty='Medium', interview_type='role', resume_filename=None, status='in_progress', **kwargs):
        super().__init__(**kwargs)
        if user_id is not None:
            self.user_id = user_id
        if title is not None:
            self.title = title
        if role is not None:
            self.role = role
        self.difficulty = difficulty
        self.interview_type = interview_type
        if resume_filename is not None:
            self.resume_filename = resume_filename
        self.status = status

    @property
    def strengths(self):
        if not self.strengths_json:
            return []
        try:
            return json.loads(self.strengths_json)
        except Exception:
            return []

    @strengths.setter
    def strengths(self, value):
        self.strengths_json = json.dumps(value if isinstance(value, list) else [])

    @property
    def weaknesses(self):
        if not self.weaknesses_json:
            return []
        try:
            return json.loads(self.weaknesses_json)
        except Exception:
            return []

    @weaknesses.setter
    def weaknesses(self, value):
        self.weaknesses_json = json.dumps(value if isinstance(value, list) else [])

    def to_dict(self, include_questions=True):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'role': self.role,
            'difficulty': self.difficulty,
            'interview_type': self.interview_type,
            'resume_filename': self.resume_filename,
            'overall_score': self.overall_score,
            'summary_feedback': self.summary_feedback,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'status': self.status,
            'created_at': self.created_at.strftime('%B %d, %Y - %I:%M %p') if self.created_at else None
        }
        if include_questions:
            data['questions'] = [q.to_dict() for q in self.questions]
        return data

class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id'), nullable=False)
    question_order = db.Column(db.Integer, nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    model_answer = db.Column(db.Text, nullable=True)
    user_answer = db.Column(db.Text, nullable=True)
    score = db.Column(db.Integer, nullable=True) # 0-100 per question
    feedback = db.Column(db.Text, nullable=True)
    improvement_tips = db.Column(db.Text, nullable=True)

    def __init__(self, interview_id=None, question_order=None, question_text=None, model_answer=None, **kwargs):
        super().__init__(**kwargs)
        if interview_id is not None:
            self.interview_id = interview_id
        if question_order is not None:
            self.question_order = question_order
        if question_text is not None:
            self.question_text = question_text
        if model_answer is not None:
            self.model_answer = model_answer

    def to_dict(self):
        return {
            'id': self.id,
            'interview_id': self.interview_id,
            'question_order': self.question_order,
            'question_text': self.question_text,
            'model_answer': self.model_answer,
            'user_answer': self.user_answer,
            'score': self.score,
            'feedback': self.feedback,
            'improvement_tips': self.improvement_tips
        }
