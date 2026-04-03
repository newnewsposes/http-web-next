"""
Authentication blueprint - handles user registration, login, and logout.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from urllib.parse import urlparse

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('files.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        # Validation
        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long')
        if not email or '@' not in email:
            errors.append('Valid email is required')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long')
        if password != password_confirm:
            errors.append('Passwords do not match')
        
        # Check for existing user
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('files.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False) == 'on'
        
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid username or password', 'error')
            return render_template('auth/login.html')
        
        if not user.is_active:
            flash('Your account has been disabled', 'error')
            return render_template('auth/login.html')
        
        login_user(user, remember=remember)
        
        # Redirect to next page or home
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('files.index')
        
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page with storage stats."""
    storage_used = current_user.get_storage_used()
    storage_quota = current_user.storage_quota
    
    # Calculate percentage
    if storage_quota:
        storage_percent = (storage_used / storage_quota) * 100
    else:
        storage_percent = 0
    
    file_count = current_user.files.count()
    
    return render_template('auth/profile.html',
                         storage_used=storage_used,
                         storage_quota=storage_quota,
                         storage_percent=storage_percent,
                         file_count=file_count)
