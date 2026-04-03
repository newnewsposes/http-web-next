"""
Files blueprint - handles file upload, listing, download, and sharing.
"""
from flask import Blueprint, render_template, request, send_from_directory, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models.file import File
import os
import uuid

files_bp = Blueprint('files', __name__, url_prefix='/files')

@files_bp.route('/')
def index():
    """List all uploaded files."""
    files = File.query.order_by(File.uploaded_at.desc()).all()
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
    
    # Secure the filename and make it unique
    original_name = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{original_name}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
    
    # Save file
    file.save(filepath)
    file_size = os.path.getsize(filepath)
    
    # Create database record
    new_file = File(
        filename=unique_filename,
        original_name=original_name,
        mimetype=file.mimetype,
        size=file_size
    )
    db.session.add(new_file)
    db.session.commit()
    
    flash(f'File "{original_name}" uploaded successfully!', 'success')
    return redirect(url_for('files.index'))

@files_bp.route('/download/<int:file_id>')
def download(file_id):
    """Download a file by its ID."""
    file_record = File.query.get_or_404(file_id)
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
    file_record.downloads += 1
    db.session.commit()
    
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        file_record.filename,
        as_attachment=True,
        download_name=file_record.original_name
    )
