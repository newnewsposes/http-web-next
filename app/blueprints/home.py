"""
Home blueprint - public landing page and user dashboard.
"""
from flask import Blueprint, render_template
from flask_login import current_user
from app.models.file import File
from app import db

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def landing():
    """Public landing / user dashboard depending on auth state."""
    if current_user.is_authenticated:
        # show user stats
        file_count = File.query.filter_by(user_id=current_user.id).count()
        storage_used = current_user.get_storage_used()
        recent_files = File.query.filter_by(user_id=current_user.id).order_by(File.uploaded_at.desc()).limit(6).all()
        return render_template('home/dashboard.html', file_count=file_count, storage_used=storage_used, recent_files=recent_files)
    
    # public landing info boxes
    features = [
        {'title': 'Fast uploads', 'desc': 'Chunked, resumable uploads for large files.'},
        {'title': 'Secure sharing', 'desc': 'Private and public files with share tokens.'},
        {'title': 'Privacy-first', 'desc': 'We don\'t scan your files — you control sharing and expiry.'},
    ]
    return render_template('home/landing.html', features=features)
