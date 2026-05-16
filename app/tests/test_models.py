import unittest
from app import app, db
from app.models import User, TutorProfile, Session, Booking, Review
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError


class TutorWebsiteUnitTests(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SECRET_KEY"] = "testsecretkey"

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
    
    def test_session_saved_correctly(self):
        with app.app_context():
            session = Session(
                tutor_id=self.tutor_id,
                subject="Python",
                datetime=datetime.now() + timedelta(days=5),
                duration=90,
                location="Online",
                max_students=5,
                status="scheduled"
            )

            db.session.add(session)
            db.session.commit()

            saved_session = Session.query.filter_by(subject="Python").first()

            self.assertIsNotNone(saved_session)
            self.assertEqual(saved_session.duration, 90)
            self.assertEqual(saved_session.location, "Online")
            self.assertEqual(saved_session.status, "scheduled")


    def test_booking_can_be_deleted(self):
        with app.app_context():
            session = Session(
                tutor_id=self.tutor_id,
                subject="Physics",
                datetime=datetime.now() + timedelta(days=2),
                duration=60,
                location="Library",
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

            db.session.delete(booking)
            db.session.commit()

            saved_booking = Booking.query.filter_by(
                session_id=session.id,
                student_id=self.student_id
            ).first()

            self.assertIsNone(saved_booking)

    def test_create_review(self):
        with app.app_context():
            review = Review(
                tutor_id=self.tutor_id,
                student_id=self.student_id,
                rating=5.0,
                comment="Very helpful tutor."
            )

            db.session.add(review)
            db.session.commit()

            saved_review = Review.query.filter_by(tutor_id=self.tutor_id).first()

            self.assertIsNotNone(saved_review)
            self.assertEqual(saved_review.rating, 5.0)
            self.assertEqual(saved_review.comment, "Very helpful tutor.")
    
    def login(self, username, password):
        return self.client.post("/login", data={
            "username": username,
            "password": password
        }, follow_redirects=True)


    def test_login_fails_with_wrong_password(self):
        response = self.login("alice", "wrongpassword")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid username or password", response.data)


    def test_duplicate_username_or_email_not_allowed(self):
        with app.app_context():
            duplicate_user = User(
                username="alice",
                email="alice2@example.com",
                role="student"
            )
            duplicate_user.set_password("password123")

            db.session.add(duplicate_user)

            with self.assertRaises(IntegrityError):
                db.session.commit()

            db.session.rollback()


    def test_valid_tutor_page_returns_200(self):
        with app.app_context():
            profile = TutorProfile(
                tutor_id=self.tutor_id,
                about_me="Maths tutor",
                subjects="Mathematics"
            )
            db.session.add(profile)
            db.session.commit()

        response = self.client.get(f"/tutor/{self.tutor_id}")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"carol", response.data)


    def test_invalid_tutor_page_returns_404(self):
        response = self.client.get("/tutor/9999")

        self.assertEqual(response.status_code, 404)


    def test_posting_review_updates_database(self):
        self.login("alice", "password123")

        response = self.client.post(
            f"/tutor/{self.tutor_id}/review",
            data={
                "rating": "5.0",
                "comment": "Great tutor!"
            },
            follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)

        with app.app_context():
            review = Review.query.filter_by(
                tutor_id=self.tutor_id,
                student_id=self.student_id
            ).first()

            self.assertIsNotNone(review)
            self.assertEqual(review.rating, 5.0)
            self.assertEqual(review.comment, "Great tutor!")


    def test_student_cannot_double_book_session(self):
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
            session_id = session.id

        self.login("alice", "password123")

        self.client.post(f"/join-session/{session_id}", follow_redirects=True)
        self.client.post(f"/join-session/{session_id}", follow_redirects=True)

        with app.app_context():
            booking_count = Booking.query.filter_by(
                session_id=session_id,
                student_id=self.student_id
            ).count()

            self.assertEqual(booking_count, 1)


    def test_booking_cancellation_works(self):
        with app.app_context():
            session = Session(
                tutor_id=self.tutor_id,
                subject="Physics",
                datetime=datetime.now() + timedelta(days=2),
                duration=60,
                location="Library",
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
            session_id = session.id

        self.login("alice", "password123")

        self.client.post(f"/cancel-booking/{session_id}", follow_redirects=True)

        with app.app_context():
            booking = Booking.query.filter_by(
                session_id=session_id,
                student_id=self.student_id
            ).first()

            self.assertIsNone(booking)


    def test_user_cannot_cancel_another_students_booking(self):
        with app.app_context():
            student2 = User(
                username="bob",
                email="bob@example.com",
                role="student"
            )
            student2.set_password("password123")
            db.session.add(student2)
            db.session.commit()

            session = Session(
                tutor_id=self.tutor_id,
                subject="Chemistry",
                datetime=datetime.now() + timedelta(days=4),
                duration=60,
                location="Online",
                max_students=5,
                status="scheduled"
            )

            db.session.add(session)
            db.session.commit()

            booking = Booking(
                session_id=session.id,
                student_id=student2.id
            )

            db.session.add(booking)
            db.session.commit()

            session_id = session.id
            student2_id = student2.id

        self.login("alice", "password123")

        self.client.post(f"/cancel-booking/{session_id}", follow_redirects=True)

        with app.app_context():
            booking = Booking.query.filter_by(
                session_id=session_id,
                student_id=student2_id
            ).first()

            self.assertIsNotNone(booking)


if __name__ == "__main__":
    unittest.main()