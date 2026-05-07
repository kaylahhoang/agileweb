from app import app, db
from app.models import User, TutorProfile, Review, Session, Booking
from datetime import datetime, timezone, timedelta

def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

     #Users
        student1 = User(username="alice", email="alice@example.com", role="student")
        student1.set_password("password123")

        student2 = User(username="bob", email="bob@example.com", role="student")
        student2.set_password("password123")

        tutor1 = User(username="carol", email="carol@example.com", role="tutor")
        tutor1.set_password("password123")

        tutor2 = User(username="dan", email="dan@example.com", role="tutor")
        tutor2.set_password("password123")

        db.session.add_all([student1, student2, tutor1, tutor2])
        db.session.commit()

    #Tutor Profiles
        profile1 = TutorProfile(
            tutor_id=tutor1.id,
            about_me="Experienced maths and physics tutor.",
            subjects="Mathematics, Physics",
            availability="Mon 2-4pm, Wed 10am-12pm",
        )
        profile2 = TutorProfile(
            tutor_id=tutor2.id,
            about_me="Computer science grad specialising in Python and algorithms.",
            subjects="Python, Data Structures, Algorithms",
            availability="Tue 1-3pm, Thu 3-5pm",
        )
        db.session.add_all([profile1, profile2])
        db.session.commit()

     #Sessions
        now = datetime.now(timezone.utc)

        session1 = Session(
            tutor_id=tutor1.id,
            subject="Mathematics",
            datetime=now + timedelta(days=3),
            duration=60,
            location="Library Room 4",
            max_students=5,
            status="scheduled",
        )
        session2 = Session(
            tutor_id=tutor2.id,
            subject="Python",
            datetime=now - timedelta(days=7),
            duration=90,
            location="Online",
            status="completed",
            max_students=5,
            feedback="Great session, very helpful!",
        )
        session3 = Session(
            tutor_id=tutor2.id,
            subject="Algorithms",
            datetime=now + timedelta(days=10),
            duration=60,
            location="Online",
            status="scheduled",
            max_students=5,
        )

        db.session.add_all([session1, session2, session3])
        db.session.commit()

        # Bookings: students join sessions
        booking1 = Booking(
            session_id=session1.id,
            student_id=student1.id,
        )

        booking2 = Booking(
            session_id=session2.id,
            student_id=student2.id,
        )

        booking3 = Booking(
            session_id=session3.id,
            student_id=student1.id,
        )

        db.session.add_all([booking1, booking2, booking3])
        db.session.commit()

        # --- Reviews ---
        review1 = Review(
            tutor_id=tutor2.id,
            student_id=student2.id,
            rating=5.0,
            comment="Incredibly patient and clear explanations.",
        )
        review2 = Review(
            tutor_id=tutor1.id,
            student_id=student1.id,
            rating=4.0,
            comment="Good session, covered a lot of ground.",
        )
        db.session.add_all([review1, review2])
        db.session.commit()

        print("Database seeded successfully.")
        print("Accounts (all password: password123):")
        print("  Students: alice@example.com, bob@example.com")
        print("  Tutors:   carol@example.com, dan@example.com")

if __name__ == "__main__":
    seed()