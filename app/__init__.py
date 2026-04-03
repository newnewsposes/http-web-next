"""
Flask application factory for ThisIsCloud.
Initializes the app, database, and blueprints.
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///files.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'HostedFiles')
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max file size
    
    # Security headers
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600 * 24 * 7  # 7 days
    
    # WTF CSRF (exempt API endpoints)
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # We'll protect forms manually
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Security headers middleware
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # CSP header for inline scripts/styles (adjust for production)
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
        return response
    
    # User loader for Flask-Login
    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.blueprints.files import files_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.api import api_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.home import home_bp
    app.register_blueprint(files_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(home_bp)
    
    # Exempt API endpoints from CSRF
    csrf.exempt(api_bp)
    
    # Set root route handled by home blueprint
    # (home_bp defines @app.route('/'))
    
    # Also provide a convenience '/ThisIsCloud' redirect to home
    from flask import redirect, url_for
    @app.route('/ThisIsCloud')
    def thisiscloud():
        return redirect(url_for('home.landing'))

    return app
