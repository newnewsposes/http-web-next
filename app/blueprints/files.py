"""
Files blueprint - handles file upload, listing, download, and sharing.
"""
from flask import Blueprint, render_template, request, send_from_directory, redirect, url_for, flash, current_app, abort
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app import db
from app.models.file import File
import os
import uuid

files_bp = Blueprint('files', __name__, url_prefix='/files')

@files_bp.route('/')
def index():
    """List all uploaded files."""
    # Show public files + user's private files if logged in
    if current_user.is_authenticated:
        files = File.query.filter(
            db.or_(File.is_public == True, File.user_id == current_user.id)
        ).order_by(File.uploaded_at.desc()).all()
    else:
        files = File.query.filter_by(is_public=True).order_by(File.uploaded_at.desc()).all()
    
    return render_template('files/index.html', files=files)

@files_bp.route('/upload', methods=['POST'])
def upload():
    """Handle file upload."""
    if 'file' not in request.files:
        flash('No file provided', 'error')
        return redirect(url_for('files.index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('files.index'))
    
    # Get file metadata
    file_size = 0
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    # Check storage quota if user is logged in
    if current_user.is_authenticated:
        if not current_user.has_storage_available(file_size):
            flash('Storage quota exceeded. Please delete some files or contact admin.', 'error')
            return redirect(url_for('files.index'))
    
    # Secure the filename and make it unique
    original_name = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{original_name}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
    
    # Save file
    file.save(filepath)
    file_size = os.path.getsize(filepath)
    
    # Get privacy setting
    is_public = request.form.get('is_public', 'true') == 'true'
    
    # Create database record
    new_file = File(
        filename=unique_filename,
        original_name=original_name,
        mimetype=file.mimetype,
        size=file_size,
        user_id=current_user.id if current_user.is_authenticated else None,
        is_public=is_public
    )
    db.session.add(new_file)
    db.session.commit()
    
    flash(f'File "{original_name}" uploaded successfully!', 'success')
    return redirect(url_for('files.index'))

@files_bp.route('/download/<int:file_id>')
def download(file_id):
    """Download a file by its ID."""
    file_record = File.query.get_or_404(file_id)
    
    # Check access permissions
    if not file_record.is_public:
        if not current_user.is_authenticated or (file_record.user_id != current_user.id and not current_user.is_admin):
            abort(403)
    
    file_record.downloads += 1
    db.session.commit()
    
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        file_record.filename,
        as_attachment=True,
        download_name=file_record.original_name
    )

@files_bp.route('/share/<share_token>')
def share(share_token):
    """Download a file via its share token."""
    file_record = File.query.filter_by(share_token=share_token).first_or_404()
    
    # Share links work for public files, or private files if you have the token
    file_record.downloads += 1
    db.session.commit()
    
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        file_record.filename,
        as_attachment=True,
        download_name=file_record.original_name
    )

@files_bp.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete(file_id):
    """Delete a file (owner or admin only)."""
    file_record = File.query.get_or_404(file_id)
    
    # Check ownership
    if file_record.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    # Delete physical file
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file_record.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Delete database record
    db.session.delete(file_record)
    db.session.commit()
    
    flash(f'File "{file_record.original_name}" deleted successfully', 'success')
    return redirect(url_for('files.index'))

@files_bp.route('/my-files')
@login_required
def my_files():
    """List current user's files only."""
    files = File.query.filter_by(user_id=current_user.id).order_by(File.uploaded_at.desc()).all()
    return render_template('files/my_files.html', files=files)
