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
    availability = db.Column(db.Text, nullable=True)  # JSON {"monday: {"start": "9:00", "end": "17:00"}"
    profile_picture = db.Column(db.String(256), nullable=True) # filename in uploads/tutor_photos/
    tutor = db.relationship('User', backref=db.backref('tutor_profile', uselist=False))





class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Float, nullable=False)  # e.g. 4.5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    tutor = db.relationship('User', foreign_keys=[tutor_id], backref='reviews_received')
    student = db.relationship('User', foreign_keys=[student_id], backref='reviews_given')

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

class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    participants = db.relationship("ConversationParticipant", back_populates="conversation")
    messages = db.relationship("Message", back_populates="conversation", order_by="Message.sent_at")


class ConversationParticipant(db.Model):
    __tablename__ = "conversation_participants"

    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

    conversation = db.relationship("Conversation", back_populates="participants")
    user = db.relationship("User", backref="conversation_participants")


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)  # NULL = unread

    conversation = db.relationship("Conversation", back_populates="messages")
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')