from flask import jsonify, render_template, redirect, url_for, flash, request
from datetime import datetime, timedelta, timezone
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from app.models import User, TutorProfile, Session
from app.forms import LoginForm, RegisterForm, ForgotPasswordForm

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

@app.route('/profile/save', methods=['POST'])
@login_required
def profile_save():
    if current_user.role != 'tutor':
        return jsonify({'error': 'Unauthorized'}), 403
    about_me = request.json.get('about_me', '')
    profile = TutorProfile.query.filter_by(tutor_id=current_user.id).first()
    if not profile:
        profile = TutorProfile(tutor_id=current_user.id, about_me=about_me)
        db.session.add(profile)
    else:
        profile.about_me = about_me
    db.session.commit()
    return jsonify({'success': True})


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/api/me', methods=['GET'])
@login_required
def me():
    return jsonify(current_user.to_dict()), 200

@app.route('/schedule')
@login_required
def schedule():
    if current_user.role == 'tutor':
        sessions = Session.query.filter_by(tutor_id=current_user.id).order_by(Session.datetime).all()
    else:
        sessions = Session.query.filter_by(student_id=current_user.id).order_by(Session.datetime).all()

    return render_template('schedule.html', sessions=sessions)
