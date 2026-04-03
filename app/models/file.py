"""
File model for storing file metadata.
"""
from app import db
from datetime import datetime
import secrets

class File(db.Model):
    """Represents an uploaded file with metadata and sharing capabilities."""
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False, unique=True)  # Stored filename
    original_name = db.Column(db.String(256), nullable=False)  # Original upload name
    mimetype = db.Column(db.String(128))
    size = db.Column(db.Integer, nullable=False)  # Size in bytes
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    downloads = db.Column(db.Integer, default=0)
    share_token = db.Column(db.String(64), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(16))
    
    # User ownership (nullable for backwards compatibility with anonymous uploads)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    is_public = db.Column(db.Boolean, default=True, nullable=False)  # Public vs private file
    
    def __repr__(self):
        return f'<File {self.original_name}>'
    
    def format_size(self):
        """Return human-readable file size."""
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
