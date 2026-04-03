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
    """List uploaded files.

    - Admins see all files.
    - Authenticated users see their own files plus public files marked as browsable.
    - Anonymous users see no files.
    """
    if current_user.is_authenticated:
        if current_user.is_admin:
            # Admins can see everything
            files = File.query.order_by(File.uploaded_at.desc()).all()
        else:
            # Regular users see their own files plus public files that are marked browsable
            files = File.query.filter(
                db.or_(
                    db.and_(File.is_public == True, File.is_browsable == True),
                    File.user_id == current_user.id
                )
            ).order_by(File.uploaded_at.desc()).all()
    else:
        # Anonymous users are not allowed to browse in this deployment
        files = []

    return render_template('files/index.html', files=files)

from flask_login import login_required

@files_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    """Handle file upload. Only authenticated users may upload."""
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
    # Browsable is an admin-only flag; default False for non-admins
    is_browsable = False
    if current_user.is_admin:
        is_browsable = request.form.get('is_browsable', 'false') == 'true'
    
    # Create database record
    new_file = File(
        filename=unique_filename,
        original_name=original_name,
        mimetype=file.mimetype,
        size=file_size,
        user_id=current_user.id if current_user.is_authenticated else None,
        is_public=is_public,
        is_browsable=is_browsable
    )
    db.session.add(new_file)
    db.session.commit()
    
    flash(f'File "{original_name}" uploaded successfully!', 'success')
    return redirect(url_for('files.index'))

@files_bp.route('/download/<int:file_id>')
@login_required
def download(file_id):
    """Download a file by its ID. Login required.

    Policy:
    - If the file is public (is_public=True), any authenticated user may download it.
    - Otherwise, only the owner or admins may download.
    """
    file_record = File.query.get_or_404(file_id)

    # Allow download if file is public and user is authenticated
    if file_record.is_public:
        # authenticated check is enforced by @login_required
        pass
    else:
        # Otherwise only owner or admin can download
        if file_record.user_id != current_user.id and not current_user.is_admin:
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
@login_required
def share(share_token):
    """Download a file via its share token. Login required to prevent unauthenticated sharing."""
    file_record = File.query.filter_by(share_token=share_token).first_or_404()

    # Only allow owners or admins to use share links, or authenticated users that have access
    if file_record.user_id != current_user.id and not current_user.is_admin:
        abort(403)

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

    # If this is an AJAX request, return JSON for smoother frontend handling
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return ({'status': 'ok', 'message': f'File "{file_record.original_name}" deleted'}), 200

    flash(f'File "{file_record.original_name}" deleted successfully', 'success')
    return redirect(url_for('files.index'))

@files_bp.route('/my-files')
@login_required
def my_files():
    """List current user's files only."""
    files = File.query.filter_by(user_id=current_user.id).order_by(File.uploaded_at.desc()).all()
    return render_template('files/my_files.html', files=files)
