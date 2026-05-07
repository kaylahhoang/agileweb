import os
import json
import uuid
from flask import jsonify, render_template, redirect, url_for, flash, request, abort, send_from_directory
from datetime import datetime, timedelta, timezone
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from app.models import User, TutorProfile, Session, Booking,  Review
from app.forms import LoginForm, RegisterForm, ForgotPasswordForm
import calendar
from datetime import datetime, timedelta, timezone

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads', 'tutor_photos')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload/tutor_photos/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


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
                    .filter(Session.datetime > now, Session.status == 'scheduled')
                    .order_by(Session.datetime)
                    .limit(3).all())
        return dict(tutor_profile=profile, sessions_run=sessions_run, upcoming_sessions=upcoming)
    else:
        student_bookings = Booking.query.filter_by(student_id=current_user.id).all()
        student_session_ids = [booking.session_id for booking in student_bookings]

        sessions_attended = (
            Session.query
            .filter(Session.id.in_(student_session_ids), Session.status == 'completed')
            .count()
        )

        three_months_ago = now - timedelta(days=90)

        recent_feedback_sessions = (
            Session.query
            .filter(Session.id.in_(student_session_ids))
            .filter(Session.status == 'completed')
            .filter(Session.feedback.isnot(None))
            .filter(Session.datetime >= three_months_ago)
            .order_by(Session.datetime.desc())
            .limit(10)
            .all()
        )

        upcoming = (
            Session.query
            .filter(Session.id.in_(student_session_ids))
            .filter(Session.datetime > now)
            .filter(Session.status == 'scheduled')
            .order_by(Session.datetime)
            .limit(3)
            .all()
        )
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
@login_required
def tutors():
    profiles = TutorProfile.query.all()
    my_profile = TutorProfile.query.filter_by(tutor_id=current_user.id).first() if current_user.role == 'tutor' else None
    avg_rows = db.session.query(Review.tutor_id, db.func.avg(Review.rating).label('avg')).group_by(Review.tutor_id).all()
    avg_ratings = {row.tutor_id: round(float(row.avg), 1) for row in avg_rows}
    return render_template('tutors.html', profiles=profiles, my_profile=my_profile, avg_ratings=avg_ratings)


@app.route('/tutor/list', methods=['POST'])
@login_required
def list_tutor():
    if current_user.role != 'tutor':
        abort(403)
    if TutorProfile.query.filter_by(tutor_id=current_user.id).first():
        flash('You already have a listing.', 'warning')
        return redirect(url_for('tutors'))
    profile = TutorProfile(tutor_id=current_user.id)
    db.session.add(profile)
    db.session.commit()
    flash('You are now listed! Fill in your profile below.', 'success')
    return redirect(url_for('tutor_detail', tutor_id=current_user.id))


@app.route('/tutor/unlist', methods=['POST'])
@login_required
def unlist_tutor():
    if current_user.role != 'tutor':
        abort(403)
    profile = TutorProfile.query.filter_by(tutor_id=current_user.id).first_or_404()
    db.session.delete(profile)
    db.session.commit()
    flash('Your listing has been removed.', 'success')
    return redirect(url_for('tutors'))


@app.route('/tutor/<int:tutor_id>/edit', methods=['POST'])
@login_required
def edit_tutor_profile(tutor_id):
    if current_user.role != 'tutor' or current_user.id != tutor_id:
        abort(403)
    profile = TutorProfile.query.filter_by(tutor_id=tutor_id).first_or_404()

    #photo upload 
    file = request.files.get('photo')
    if file and file.filename and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"tutor_{tutor_id}_{uuid.uuid4().hex[:8]}.{ext}"
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        profile.profile_picture = filename

    #availability - build JSON from day checkboxes and time inputs
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    availability = {}
    for day in days:
        if request.form.get(f'avail_{day}_enabled'):
            start = request.form.get(f'avail_{day}_start', '')
            end = request.form.get(f'avail_{day}_end', '')
            if start and end:
                availability[day] = {'start': start, 'end': end}
    profile.availability = json.dumps(availability) if availability else None
    
    profile.about_me = request.form.get('about_me', '').strip() or None
    profile.subjects = request.form.get('subjects', '').strip() or None
  
    db.session.commit()
    flash('Profile updated!', 'success')
    return redirect(url_for('tutor_detail', tutor_id=tutor_id))


@app.route('/tutor/<int:tutor_id>')
def tutor_detail(tutor_id):
    tutor = User.query.get_or_404(tutor_id)
    if tutor.role != 'tutor':
        abort(404)
    profile = TutorProfile.query.filter_by(tutor_id=tutor_id).first()
    reviews = Review.query.filter_by(tutor_id=tutor_id).order_by(Review.created_at.desc()).all()
    raw = db.session.query(db.func.avg(Review.rating)).filter_by(tutor_id=tutor_id).scalar()
    avg_rating = round(float(raw), 1) if raw is not None else None
    subjects = [s.strip() for s in profile.subjects.split(',')] if profile and profile.subjects else []

    availability_data = {}
    if profile and profile.availability:
        try:
            availability_data = json.loads(profile.availability)
        except (json.JSONDecodeError, TypeError):
            availability_data = {}

    return render_template('Tutor_detail_page.html',
                           tutor=tutor,
                           profile=profile,
                           reviews=reviews,
                           avg_rating=avg_rating,
                           subjects=subjects,
                           availability_data=availability_data)

@app.route('/tutor/<int:tutor_id>/review', methods=['POST'])
@login_required
def submit_review(tutor_id):
    rating = request.form.get('rating', type=float)
    comment = request.form.get('comment', '').strip()

    review = Review(
        tutor_id=tutor_id,
        student_id=current_user.id,
        rating=rating,
        comment=comment
    )

    db.session.add(review)
    db.session.commit()

    flash('Review submitted successfully!', 'success')
    return redirect(url_for('tutor_detail', tutor_id=tutor_id))

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

    joined_session_ids = []

    if current_user.role == 'student':
        joined_session_ids = [
            booking.session_id
            for booking in Booking.query.filter_by(student_id=current_user.id).all()
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
        joined_session_ids=joined_session_ids,

        week_sessions=week_sessions,
        day_sessions=day_sessions,
    )

@app.route('/create-session', methods=['POST'])
@login_required
def create_session():
    if current_user.role != 'tutor':
        flash('Only tutors can create sessions.', 'error')
        return redirect(url_for('schedule'))

    subject = request.form.get('subject')
    date = request.form.get('date')
    time = request.form.get('time')
    duration = request.form.get('duration')
    location = request.form.get('location')
    max_students = request.form.get('max_students', 5)

    if not subject or not date or not time or not duration:
        flash('Please fill in all required session fields.', 'error')
        return redirect(url_for('schedule'))

    session_datetime = datetime.strptime(f'{date} {time}', '%Y-%m-%d %H:%M')

    new_session = Session(
        tutor_id=current_user.id,
        subject=subject,
        datetime=session_datetime,
        duration=int(duration),
        location=location,
        max_students=int(max_students),
        status='scheduled'
    )

    db.session.add(new_session)
    db.session.commit()

    flash('Session created successfully.', 'success')
    return redirect(url_for('schedule'))

@app.route('/join-session/<int:session_id>', methods=['POST'])
@login_required
def join_session(session_id):
    if current_user.role != 'student':
        flash('Only students can join sessions.', 'error')
        return redirect(url_for('schedule'))

    session = Session.query.get_or_404(session_id)

    existing_booking = Booking.query.filter_by(
        session_id=session.id,
        student_id=current_user.id
    ).first()

    if existing_booking:
        flash('You have already joined this session.', 'error')
        return redirect(url_for('schedule'))

    if len(session.bookings) >= session.max_students:
        flash('This session is full.', 'error')
        return redirect(url_for('schedule'))

    booking = Booking(
        session_id=session.id,
        student_id=current_user.id
    )

    db.session.add(booking)
    db.session.commit()

    flash('You joined the session successfully.', 'success')
    return redirect(url_for('schedule'))

@app.route('/cancel-booking/<int:session_id>', methods=['POST'])
@login_required
def cancel_booking(session_id):
    session = Session.query.get_or_404(session_id)

    if current_user.role == 'tutor':
        if current_user.id != session.tutor_id:
            flash('You are not allowed to cancel this session.', 'error')
            return redirect(url_for('schedule'))

        session.status = 'cancelled'
        db.session.commit()
        flash('Session cancelled successfully.', 'success')
        return redirect(url_for('schedule'))

    booking = Booking.query.filter_by(
        session_id=session.id,
        student_id=current_user.id
    ).first()

    if not booking:
        flash('You are not booked into this session.', 'error')
        return redirect(url_for('schedule'))

    db.session.delete(booking)
    db.session.commit()

    flash('You left the session successfully.', 'success')
    return redirect(url_for('schedule'))