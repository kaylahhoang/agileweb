from flask import jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from app.models import User
from app.forms import LoginForm, RegisterForm


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    register_form = RegisterForm()

    if login_form.validate_on_submit():
        user = User.query.filter_by(username=login_form.username.data).first()
        if user and user.check_password(login_form.password.data):
            login_user(user)
            return redirect(url_for('login'))  # replace with dashboard route later
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


@app.route('/tutors')
def tutors():
    return render_template('tutors.html')


@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out'}), 200


@app.route('/api/me', methods=['GET'])
@login_required
def me():
    return jsonify(current_user.to_dict()), 200
