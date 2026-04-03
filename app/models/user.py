"""
User model for authentication and authorization.
"""
from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    """User account with authentication and file ownership."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Storage quota (in bytes, None = unlimited)
    storage_quota = db.Column(db.BigInteger, default=5*1024*1024*1024)  # 5GB default
    
    # Relationship to files
    files = db.relationship('File', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify the password against the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def get_storage_used(self):
        """Calculate total storage used by this user's files."""
        return db.session.query(db.func.sum(File.size)).filter_by(user_id=self.id).scalar() or 0
    
    def has_storage_available(self, file_size):
        """Check if user has enough quota for a new file."""
        if self.storage_quota is None:
            return True
        return self.get_storage_used() + file_size <= self.storage_quota
    
    def __repr__(self):
        return f'<User {self.username}>'
