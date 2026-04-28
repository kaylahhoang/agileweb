from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(16), nullable=False, default="student")  # "student" or "tutor"
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
        }
    
class TutorProfile(db.Model):
    __tablename__ = "tutor_profiles"

    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    about_me = db.Column(db.Text, nullable=True)
    subjects = db.Column(db.String(256), nullable=True)  # comma-separated list of subjects

    tutor = db.relationship('User', backref=db.backref('tutor_profile', uselist=False))
    

class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(128), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # duration in minutes
    location = db.Column(db.String(128), nullable=True)
    status = db.Column(db.String(16), nullable=False, default="scheduled")  # "scheduled", "completed", "cancelled"
    feedback = db.Column(db.Text, nullable=True)

    student = db.relationship('User', foreign_keys=[student_id], backref='student_sessions')
    tutor = db.relationship('User', foreign_keys=[tutor_id], backref='tutor_sessions')
