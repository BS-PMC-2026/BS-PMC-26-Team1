from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User, StudentProfile, LecturerProfile

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.register'))
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return redirect(url_for('auth.register'))
            
        if role not in ['student', 'lecturer']:
            flash('Role must be either student or lecturer.', 'error')
            return redirect(url_for('auth.register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already exists.', 'error')
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password)
        new_user = User(full_name=full_name, email=email, password_hash=hashed_password, role=role)
        
        db.session.add(new_user)
        db.session.flush() # To get the new_user.id

        if role == 'student':
            student_profile = StudentProfile(user_id=new_user.id)
            db.session.add(student_profile)
        elif role == 'lecturer':
            lecturer_profile = LecturerProfile(user_id=new_user.id)
            db.session.add(lecturer_profile)

        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            # Session setup
            session['user_id'] = user.id
            session['role'] = user.role
            session['user_name'] = user.full_name
            return redirect(url_for('main.home'))
        else:
            flash('Login failed. Check your email and password.', 'error')
            return redirect(url_for('auth.login'))

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.home'))
