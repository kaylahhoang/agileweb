import unittest
from app import app, db
from app.models import User, TutorProfile, Session, Booking
from datetime import datetime, timedelta


class TutorWebsiteUnitTests(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

        self.client = app.test_client()

        with app.app_context():
            db.drop_all()
            db.create_all()

            student = User(
                username="alice",
                email="alice@example.com",
                role="student"
            )
            student.set_password("password123")

            tutor = User(
                username="carol",
                email="carol@example.com",
                role="tutor"
            )
            tutor.set_password("password123")

            db.session.add_all([student, tutor])
            db.session.commit()

            self.student_id = student.id
            self.tutor_id = tutor.id

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_password_hashing(self):
        with app.app_context():
            student = db.session.get(User, self.student_id)

            self.assertTrue(student.check_password("password123"))
            self.assertFalse(student.check_password("wrongpassword"))

    def test_user_role_saved_correctly(self):
        with app.app_context():
            student = db.session.get(User, self.student_id)
            tutor = db.session.get(User, self.tutor_id)

            self.assertEqual(student.role, "student")
            self.assertEqual(tutor.role, "tutor")

    def test_create_tutor_profile(self):
        with app.app_context():
            profile = TutorProfile(
                tutor_id=self.tutor_id,
                about_me="Experienced maths tutor.",
                subjects="Mathematics, Physics",
                availability='{"monday": {"start": "09:00", "end": "17:00"}}',
                profile_picture="default-profile.png"
            )

            db.session.add(profile)
            db.session.commit()

            saved_profile = TutorProfile.query.filter_by(tutor_id=self.tutor_id).first()

            self.assertIsNotNone(saved_profile)
            self.assertEqual(saved_profile.about_me, "Experienced maths tutor.")
            self.assertEqual(saved_profile.subjects, "Mathematics, Physics")

    def test_student_can_book_session(self):
        with app.app_context():
            session = Session(
                tutor_id=self.tutor_id,
                subject="Mathematics",
                datetime=datetime.now() + timedelta(days=3),
                duration=60,
                location="Library Room 4",
                max_students=5,
                status="scheduled"
            )

            db.session.add(session)
            db.session.commit()

            booking = Booking(
                session_id=session.id,
                student_id=self.student_id
            )

            db.session.add(booking)
            db.session.commit()

            saved_booking = Booking.query.filter_by(
                session_id=session.id,
                student_id=self.student_id
            ).first()

            self.assertIsNotNone(saved_booking)
            self.assertEqual(saved_booking.student_id, self.student_id)


if __name__ == "__main__":
    unittest.main()