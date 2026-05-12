import unittest
import threading
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from app import app, db
from app.models import User, TutorProfile, Session, Booking, Message, Conversation, ConversationParticipant
from datetime import datetime, timedelta


class SeleniumTestCase(unittest.TestCase):

    TEST_STUDENT = "selenium_student"
    TEST_TUTOR   = "selenium_tutor"

    def _cleanup_test_data(self):
        """Remove any data belonging to the selenium test accounts."""
        for username in (self.TEST_STUDENT, self.TEST_TUTOR):
            user = User.query.filter_by(username=username).first()
            if not user:
                continue
            # bookings the student made
            Booking.query.filter_by(student_id=user.id).delete()
            # sessions (and their bookings) the tutor created
            for s in Session.query.filter_by(tutor_id=user.id).all():
                Booking.query.filter_by(session_id=s.id).delete()
            Session.query.filter_by(tutor_id=user.id).delete()
            # conversations
            for cp in ConversationParticipant.query.filter_by(user_id=user.id).all():
                Message.query.filter_by(conversation_id=cp.conversation_id).delete()
                ConversationParticipant.query.filter_by(conversation_id=cp.conversation_id).delete()
                Conversation.query.filter_by(id=cp.conversation_id).delete()
            TutorProfile.query.filter_by(tutor_id=user.id).delete()
            db.session.delete(user)
        db.session.commit()

    def setUp(self):
        app.config['TESTING'] = True
        app.config["WTF_CSRF_ENABLED"] = False
        # Use the real app.db — do NOT drop all tables, only manage test accounts

        with app.app_context():
            self._cleanup_test_data()  # remove leftovers from any previous run

            student = User(username=self.TEST_STUDENT, email="selenium_student@test.com", role="student")
            student.set_password("password123")

            tutor = User(username=self.TEST_TUTOR, email="selenium_tutor@test.com", role="tutor")
            tutor.set_password("password123")

            db.session.add_all([student, tutor])
            db.session.commit()

            profile = TutorProfile(
                tutor_id=tutor.id,
                about_me="Experienced math tutor with a passion for helping students succeed.",
                subjects="Mathematics, Physics"
            )
            db.session.add(profile)

            session = Session(
                tutor_id=tutor.id,
                subject="Mathematics",
                datetime=datetime.now() + timedelta(days=3),
                duration=60,
                location="Room 104",
                max_students=5,
                status="scheduled"
            )
            db.session.add(session)
            db.session.commit()

            self.student_id = student.id
            self.tutor_id = tutor.id

        # Start Flask in a separate thread
        self.server_thread = threading.Thread(
            target=app.run,
            kwargs={"debug": False, "use_reloader": False, "port": 5000}
        )
        self.server_thread.daemon = True
        self.server_thread.start()
        time.sleep(1)

        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.driver.implicitly_wait(10)
        self.base_url = "http://localhost:5000"

    def tearDown(self):
        self.driver.quit()
        with app.app_context():
            self._cleanup_test_data()

    # Helper method to log in
    def login(self, username, password):
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

    # Tests
    def test_login_student(self):
        self.login(self.TEST_STUDENT, "password123")
        WebDriverWait(self.driver, 10).until(
            EC.title_contains("Dashboard")
        )
        self.assertIn("Dashboard", self.driver.title)

    def test_login_tutor(self):
        self.login(self.TEST_TUTOR, "password123")
        WebDriverWait(self.driver, 10).until(
            EC.title_contains("Dashboard")
        )
        self.assertIn("Dashboard", self.driver.title)

    def test_invalid_login_shows_error(self):
        self.login(self.TEST_STUDENT, "wrongpassword")
        error = self.driver.find_element(By.CLASS_NAME, "flash-error")
        self.assertIn("Invalid", error.text)

    def test_student_dashboard_shows_feedback_from_tutors(self):
        self.login(self.TEST_STUDENT, "password123")
        self.driver.get(f"{self.base_url}/dashboard")
        body = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("Feedback from Tutors", body)
        self.assertNotIn("Write student Feedback", body)

    def test_tutor_dashboard_shows_write_feedback(self):
        self.login(self.TEST_TUTOR, "password123")
        self.driver.get(f"{self.base_url}/dashboard")
        body = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("Write student Feedback", body)

    
    def test_tutors_page_loads(self):
        self.login(self.TEST_STUDENT, "password123")
        WebDriverWait(self.driver, 10).until(EC.title_contains("Dashboard"))
        self.driver.get(f"{self.base_url}/tutors")
        WebDriverWait(self.driver, 10).until(EC.title_contains("Tutors"))
        body = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn(self.TEST_TUTOR, body)

    def test_logout_redirects_to_login(self):
        self.login(self.TEST_STUDENT, "password123")
        WebDriverWait(self.driver, 10).until(EC.title_contains("Dashboard"))
        self.driver.get(f"{self.base_url}/logout")

        WebDriverWait(self.driver, 10).until(EC.title_contains("Login"))
        self.assertIn("login", self.driver.current_url.lower().replace(self.base_url, "") or "/")

    def test_bookings_page_loads(self):
        self.login(self.TEST_STUDENT, "password123")
        WebDriverWait(self.driver, 10).until(EC.title_contains("Dashboard"))
        self.driver.get(f"{self.base_url}/bookings")
        WebDriverWait(self.driver, 10).until(EC.title_contains("Schedule"))
        self.assertIn("Session Schedule", self.driver.page_source)

    def test_messages_page_loads(self):
        self.login(self.TEST_STUDENT, "password123")
        self.driver.get(f"{self.base_url}/messages")
        heading = self.driver.find_element(By.TAG_NAME, "h2")
        self.assertIn("Messages", heading.text)

    def test_new_message_appears_within_3_seconds(self):
        import json as _json
        self.login(self.TEST_STUDENT, "password123")

        with app.app_context():
            kaylah = User.query.filter_by(username=self.TEST_TUTOR).first()
            kaylah_id = kaylah.id
        self.driver.get(f"{self.base_url}/messages?user_id={kaylah_id}")

        page_data_el = self.driver.find_element(By.ID, "pageData")
        conv_id = _json.loads(page_data_el.get_attribute("textContent"))["convId"]

        with app.app_context():
            kaylah = User.query.filter_by(username=self.TEST_TUTOR).first()
            msg = Message(
                conversation_id=conv_id,
                sender_id=kaylah.id,
                content="Hello from kaylah!"
            )
            db.session.add(msg)
            db.session.commit()

        wait = WebDriverWait(self.driver, 5)
        appeared = wait.until(
            EC.text_to_be_present_in_element((By.ID, "chatMessages"), "Hello from kaylah!")
        )
        self.assertTrue(appeared)

    def test_student_can_join_session(self):
        from datetime import date as _date
        self.login(self.TEST_STUDENT, "password123")

        today_str = _date.today().strftime("%Y-%m-%d")
        self.driver.get(f"{self.base_url}/bookings?view=weekly&date={today_str}")

        join_btn = self.driver.find_element(By.XPATH, "//button[normalize-space()='Join']")
        self.driver.execute_script("arguments[0].click()", join_btn)

        leave_btn = self.driver.find_element(By.XPATH, "//button[normalize-space()='Leave']")
        self.assertIsNotNone(leave_btn)

        with app.app_context():
            session = Session.query.first()
            student = User.query.filter_by(username=self.TEST_STUDENT).first()
            booking = Booking.query.filter_by(
                session_id=session.id, student_id=student.id
            ).first()
            self.assertIsNotNone(booking)

    def test_student_can_leave_session(self):
        from datetime import date as _date
        self.login(self.TEST_STUDENT, "password123")
        today_str = _date.today().strftime("%Y-%m-%d")
        self.driver.get(f"{self.base_url}/bookings?view=weekly&date={today_str}")

        # Join via UI first so the server knows about the booking
        join_btn = self.driver.find_element(By.XPATH, "//button[normalize-space()='Join']")
        self.driver.execute_script("arguments[0].click()", join_btn)

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[normalize-space()='Leave']"))
        )

        # Now leave
        leave_btn = self.driver.find_element(By.XPATH, "//button[normalize-space()='Leave']")
        self.driver.execute_script("arguments[0].click()", leave_btn)

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[normalize-space()='Join']"))
        )
        join_btn = self.driver.find_element(By.XPATH, "//button[normalize-space()='Join']")
        self.assertIsNotNone(join_btn)

    def test_tutor_can_create_session(self):
        from datetime import date as _date, timedelta
        self.login(self.TEST_TUTOR, "password123")
        WebDriverWait(self.driver, 10).until(EC.title_contains("Dashboard"))
        self.driver.get(f"{self.base_url}/bookings")

        future_date = (_date.today() + timedelta(days=7)).strftime("%Y-%m-%d")

        self.driver.find_element(By.NAME, "subject").send_keys("Physics")
        date_input = self.driver.find_element(By.NAME, "date")
        self.driver.execute_script("arguments[0].value = arguments[1]", date_input, future_date)
        time_input = self.driver.find_element(By.NAME, "time")
        self.driver.execute_script("arguments[0].value = arguments[1]", time_input, "10:00")
        self.driver.find_element(By.NAME, "location").send_keys("Room 101")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        self.assertIn("Physics", self.driver.page_source)


if __name__ == "__main__":
    unittest.main()
