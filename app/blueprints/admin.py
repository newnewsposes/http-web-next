"""
Admin blueprint - dashboard, user management, and analytics.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.user import User
from app.models.file import File
from sqlalchemy import func, desc
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin access."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with system stats."""
    # User stats
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admin_users = User.query.filter_by(is_admin=True).count()
    
    # File stats
    total_files = File.query.count()
    total_storage = db.session.query(func.sum(File.size)).scalar() or 0
    public_files = File.query.filter_by(is_public=True).count()
    private_files = File.query.filter_by(is_public=False).count()
    total_downloads = db.session.query(func.sum(File.downloads)).scalar() or 0
    
    # Recent uploads (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_uploads = File.query.filter(File.uploaded_at >= week_ago).count()
    
    # Top uploaders
    top_uploaders = db.session.query(
        User.username,
        func.count(File.id).label('file_count'),
        func.sum(File.size).label('total_size')
    ).join(File, File.user_id == User.id).group_by(User.id).order_by(desc('file_count')).limit(10).all()
    
    # Recent files
    recent_files = File.query.order_by(File.uploaded_at.desc()).limit(10).all()
    
    # Most downloaded
    popular_files = File.query.order_by(File.downloads.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         admin_users=admin_users,
                         total_files=total_files,
                         total_storage=total_storage,
                         public_files=public_files,
                         private_files=private_files,
                         total_downloads=total_downloads,
                         recent_uploads=recent_uploads,
                         top_uploaders=top_uploaders,
                         recent_files=recent_files,
                         popular_files=popular_files)

@admin_bp.route('/users')
@admin_required
def users():
    """User management page."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    users_query = User.query.order_by(User.created_at.desc())
    users_paginated = users_query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Calculate storage for each user
    user_stats = []
    for user in users_paginated.items:
        storage_used = user.get_storage_used()
        file_count = user.files.count()
        user_stats.append({
            'user': user,
            'storage_used': storage_used,
            'file_count': file_count
        })
    
    return render_template('admin/users.html',
                         user_stats=user_stats,
                         pagination=users_paginated)

@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_user_active(user_id):
    """Toggle user active status."""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot deactivate your own account', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} has been {status}', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_user_admin(user_id):
    """Toggle user admin status."""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot change your own admin status', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = 'granted' if user.is_admin else 'revoked'
    flash(f'Admin privileges {status} for {user.username}', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/update-quota', methods=['POST'])
@admin_required
def update_user_quota(user_id):
    """Update user storage quota."""
    user = User.query.get_or_404(user_id)
    
    quota_gb = request.form.get('quota_gb', type=float)
    
    if quota_gb is None or quota_gb < 0:
        flash('Invalid quota value', 'error')
        return redirect(url_for('admin.users'))
    
    # Convert GB to bytes (None = unlimited)
    if quota_gb == 0:
        user.storage_quota = None
    else:
        user.storage_quota = int(quota_gb * 1024 * 1024 * 1024)
    
    db.session.commit()
    
    quota_str = 'unlimited' if user.storage_quota is None else f'{quota_gb} GB'
    flash(f'Storage quota for {user.username} updated to {quota_str}', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/files')
@admin_required
def files():
    """File management page."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    files_query = File.query.order_by(File.uploaded_at.desc())
    files_paginated = files_query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/files.html',
                         files=files_paginated.items,
                         pagination=files_paginated)

@admin_bp.route('/analytics')
@admin_required
def analytics():
    """Analytics page with charts and graphs."""
    # Upload trends (last 30 days)
    days = 30
    upload_trends = []
    
    for i in range(days):
        day = datetime.utcnow() - timedelta(days=days - i - 1)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        count = File.query.filter(
            File.uploaded_at >= day_start,
            File.uploaded_at < day_end
        ).count()
        
        upload_trends.append({
            'date': day_start.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # File type distribution
    file_types = db.session.query(
        func.substr(File.mimetype, 1, func.instr(File.mimetype, '/') - 1).label('type'),
        func.count(File.id).label('count')
    ).group_by('type').all()
    
    # Storage by user
    storage_by_user = db.session.query(
        User.username,
        func.sum(File.size).label('storage')
    ).join(File, File.user_id == User.id).group_by(User.id).order_by(desc('storage')).limit(10).all()

    # Prepare labels and values in MB for the template
    storage_labels = [row.username for row in storage_by_user]
    storage_values_mb = [int((row.storage or 0) / (1024 * 1024)) for row in storage_by_user]

    return render_template('admin/analytics.html',
                         upload_trends=upload_trends,
                         file_types=file_types,
                         storage_by_user=storage_by_user,
                         storage_labels=storage_labels,
                         storage_values_mb=storage_values_mb)
