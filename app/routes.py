from flask import jsonify, render_template, redirect, url_for, flash, request
from datetime import datetime, timedelta, timezone
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from app.models import User, TutorProfile, Session
from app.forms import LoginForm, RegisterForm, ForgotPasswordForm
import calendar
from datetime import datetime, timedelta, timezone

@app.context_processor
def inject_profile_data():
    if not current_user.is_authenticated:
        return {}
    now = datetime.utcnow()
    if current_user.role == 'tutor':
        profile = TutorProfile.query.filter_by(tutor_id=current_user.id).first()
        sessions_run = Session.query.filter_by(tutor_id=current_user.id, status='completed').count()
        upcoming = (Session.query
                    .filter_by(tutor_id=current_user.id)
                    .filter(Session.datetime > now, Session.status.in_(['pending', 'confirmed']))
                    .order_by(Session.datetime)
                    .limit(3).all())
        return dict(tutor_profile=profile, sessions_run=sessions_run, upcoming_sessions=upcoming)
    else:
        sessions_attended = Session.query.filter_by(student_id=current_user.id, status='completed').count()
        three_months_ago = now - timedelta(days=90)
        recent_feedback_sessions = (Session.query
                                    .filter_by(student_id=current_user.id, status='completed')
                                    .filter(Session.feedback.isnot(None))
                                    .filter(Session.datetime >= three_months_ago)
                                    .order_by(Session.datetime.desc())
                                    .limit(10).all())
        upcoming = (Session.query
                    .filter_by(student_id=current_user.id)
                    .filter(Session.datetime > now, Session.status.in_(['pending', 'confirmed']))
                    .order_by(Session.datetime)
                    .limit(3).all())
        return dict(
            sessions_attended=sessions_attended,
            recent_feedback_sessions=recent_feedback_sessions,
            upcoming_sessions=upcoming
        )




@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    register_form = RegisterForm()

    if login_form.validate_on_submit():
        user = User.query.filter_by(username=login_form.username.data).first()
        if user and user.check_password(login_form.password.data):
            login_user(user)
            return redirect(url_for('tutors'))  # replace with dashboard route later
        flash('Invalid username or password', 'login_error')

    return render_template('login.html', login_form=login_form, register_form=register_form)


@app.route('/register', methods=['POST'])
def register():
    login_form = LoginForm()
    register_form = RegisterForm()

    if register_form.validate_on_submit():
        if User.query.filter_by(username=register_form.username.data).first():
            flash('Username already taken', 'register_error')
        elif User.query.filter_by(email=register_form.email.data).first():
            flash('Email already registered', 'register_error')
        else:
            user = User(
                username=register_form.username.data,
                email=register_form.email.data,
                role=register_form.role.data
            )
            user.set_password(register_form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template('login.html', login_form=login_form, register_form=register_form, show_register=True)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        flash('If that email is registered, you will receive reset instructions shortly.', 'success')
        return redirect(url_for('forgot_password'))
    return render_template('forgotpassword.html', form=form)


@app.route('/tutors')
def tutors():
    return render_template('tutors.html')


@app.route('/tutor/<int:tutor_id>')
def tutor_detail(tutor_id):

    tutors_data = [
        {
            "id": 1,
            "name": "John Doe",
            "subject": "Mathematics",
            "rating": 4.8,
            "availability": "Mon - Fri, 9am - 5pm",
            "about": "I am an experienced mathematics tutor...",
            "subjects": ["Mathematics", "Algebra", "Calculus", "Statistics"],
            "reviews": [
                {"name": "Alice", "rating": 5, "comment": "Great tutor", "time": "2 weeks ago"},
                {"name": "Bob", "rating": 4, "comment": "Helpful", "time": "1 month ago"}
            ]
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "subject": "English",
            "rating": 4.6,
            "availability": "Weekends",
            "about": "I teach English...",
            "subjects": ["English", "Writing"],
            "reviews": [
                {"name": "Tom", "rating": 5, "comment": "Excellent!", "time": "3 weeks ago"}
            ]
        }
    ]

    tutor = None

    for t in tutors_data:
        if t["id"] == tutor_id:
            tutor = t
            break
    if tutor is None:
        return "Tutor not found", 404

    return render_template('tutor_detail_page.html', tutor=tutor)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/api/me', methods=['GET'])
@login_required
def me():
    return jsonify(current_user.to_dict()), 200

@app.route('/bookings')
@login_required
def schedule():
    today = datetime.today()

    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)

    if current_user.role == 'tutor':
        sessions = (
            Session.query
            .filter_by(tutor_id=current_user.id)
            .filter(Session.status != 'cancelled')
            .order_by(Session.datetime)
            .all()
        )
    else:
        sessions = (
            Session.query
            .filter_by(student_id=current_user.id)
            .filter(Session.status != 'cancelled')
            .order_by(Session.datetime)
            .all()
        )

    month_sessions = [
        session for session in sessions
        if session.datetime.year == year and session.datetime.month == month
    ]

    sessions_by_day = {}
    for session in month_sessions:
        day = session.datetime.day
        if day not in sessions_by_day:
            sessions_by_day[day] = []
        sessions_by_day[day].append(session)

    cal = calendar.Calendar(firstweekday=6)  # Sunday start
    calendar_weeks = cal.monthdayscalendar(year, month)

    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    next_month = month + 1
    next_year = year
    if next_month == 13:
        next_month = 1
        next_year += 1

    month_name = calendar.month_name[month]

    today_day = today.day
    today_month = today.month
    today_year = today.year

    week_sessions = [
        s for s in sessions
        if s.datetime.isocalendar()[1] == today.isocalendar()[1]
        and s.datetime.year == today.year
    ]

    day_sessions = [
        s for s in sessions
        if s.datetime.date() == today.date()
    ]

    return render_template(
        'schedule.html',
        sessions=sessions,
        sessions_by_day=sessions_by_day,
        calendar_weeks=calendar_weeks,
        month_name=month_name,
        month=month,
        year=year,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
        today_day=today_day,
        today_month=today_month,
        today_year=today_year,

        week_sessions=week_sessions,
        day_sessions=day_sessions,
    )

@app.route('/book-session', methods=['POST'])
@login_required
def book_session():
    if current_user.role != 'student':
        flash('Only students can create bookings.', 'error')
        return redirect(url_for('schedule'))

    tutor_id = request.form.get('tutor_id')
    subject = request.form.get('subject')
    date = request.form.get('date')
    time = request.form.get('time')
    duration = request.form.get('duration')
    location = request.form.get('location')

    if not tutor_id or not subject or not date or not time or not duration:
        flash('Please fill in all required booking fields.', 'error')
        return redirect(url_for('schedule'))

    session_datetime = datetime.strptime(f'{date} {time}', '%Y-%m-%d %H:%M')
    duration = int(duration)
    session_end = session_datetime + timedelta(minutes=duration)

    existing_sessions = Session.query.filter(
        Session.status != 'cancelled',
        db.or_(
            Session.tutor_id == int(tutor_id),
            Session.student_id == current_user.id
        )
    ).all()

    for existing in existing_sessions:
        existing_start = existing.datetime
        existing_end = existing.datetime + timedelta(minutes=existing.duration)

        if session_datetime < existing_end and session_end > existing_start:
            flash('This time conflicts with an existing booking.', 'error')
            return redirect(url_for('schedule'))

    new_session = Session(
        student_id=current_user.id,
        tutor_id=int(tutor_id),
        subject=subject,
        datetime=session_datetime,
        duration=duration,
        location=location,
        status='scheduled'
    )

    db.session.add(new_session)
    db.session.commit()

    flash('Booking created successfully.', 'success')
    return redirect(url_for('schedule'))

@app.route('/cancel-booking/<int:session_id>', methods=['POST'])
@login_required
def cancel_booking(session_id):
    session = Session.query.get_or_404(session_id)

    if current_user.id != session.student_id and current_user.id != session.tutor_id:
        flash('You are not allowed to cancel this booking.', 'error')
        return redirect(url_for('schedule'))

    session.status = 'cancelled'
    db.session.commit()

    flash('Booking cancelled successfully.', 'success')
    return redirect(url_for('schedule'))