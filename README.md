# agileweb
CITS3403 Agile Web Project

## Application Description

This project is a tutoring web application designed to connect students with tutors.  
Students can browse tutors, book tutoring sessions, leave reviews, and communicate through a messaging system. Tutors can create and manage tutoring sessions, manage availability, and provide feedback to students.

The application was developed using:
- Flask
- SQLAlchemy
- Flask-Login
- Flask-WTF
- Flask-Mail
- SQLite
- Selenium WebDriver

## Team Members

| UWA Student ID | Name | GitHub Username |
|---|---|---|
| 23869499 | Kaylah Hoang | kaylahhoang |
| 24271935 | Kennice Kennice Leong Jing Lin | kenniceleongg |
| 24696685 | Aarav Rana | aaravranaa |
| 24304672 | Terry Zhang | terrycheung02 |

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Required Packages

Install required dependencies using:

```bash
python3 -m pip install \
flask \
flask-sqlalchemy \
flask-login \
flask-migrate \
flask-mail \
flask-wtf \
python-dotenv \
email-validator \
werkzeug \
selenium \
webdriver-manager
```

## Environment Variables

Create an environment file:

```text
application-env/.env
```

Example `.env` contents:

```env
SECRET_KEY=your_secret_key_here
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
```

## Running the Application

Run the database seed script:

```bash
python3 seed.py
```

Run the Flask server:

```bash
python3 run.py
```

## Running Unit Tests

```bash
python3 -m unittest app.tests.test_models
```

## Running Selenium Tests

```bash
python3 -m unittest app.tests.test_selenium
```

The Selenium tests automatically:
- start the Flask server
- create temporary test users/sessions
- open Chrome using Selenium WebDriver
- clean up test data afterwards

The tests use Chrome WebDriver through `webdriver-manager`.