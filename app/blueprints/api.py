"""
API blueprint - handles chunked upload endpoints and file operations.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user, login_required
from app.services.upload import UploadService
from app.models.user import User
from app.utils.security import rate_limit
import uuid

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/upload/init', methods=['POST'])
@rate_limit(max_requests=20, window_seconds=60)  # 20 upload sessions per minute
def init_upload():
    """Initialize a chunked upload session."""
    data = request.get_json()
    
    if not data or 'filename' not in data or 'fileSize' not in data:
        return jsonify({'error': 'Missing filename or fileSize'}), 400
    
    filename = data['filename']
    file_size = data['fileSize']
    
    # Check storage quota if user is logged in
    if current_user.is_authenticated:
        if not current_user.has_storage_available(file_size):
            return jsonify({'error': 'Storage quota exceeded'}), 403
    
    # Generate upload ID
    upload_id = str(uuid.uuid4())
    
    return jsonify({
        'uploadId': upload_id,
        'chunkSize': 1024 * 1024,  # 1MB chunks
        'message': 'Upload session initialized'
    }), 200

@api_bp.route('/upload/chunk', methods=['POST'])
@rate_limit(max_requests=100, window_seconds=60)  # 100 chunks per minute
def upload_chunk():
    """Upload a single chunk."""
    upload_id = request.form.get('uploadId')
    chunk_index = request.form.get('chunkIndex')
    
    if not upload_id or chunk_index is None:
        return jsonify({'error': 'Missing uploadId or chunkIndex'}), 400
    
    try:
        chunk_index = int(chunk_index)
    except ValueError:
        return jsonify({'error': 'Invalid chunkIndex'}), 400
    
    if 'chunk' not in request.files:
        return jsonify({'error': 'No chunk data'}), 400
    
    chunk = request.files['chunk']
    chunk_data = chunk.read()
    
    # Save chunk
    try:
        UploadService.save_chunk(upload_id, chunk_index, chunk_data)
    except Exception as e:
        return jsonify({'error': f'Failed to save chunk: {str(e)}'}), 500
    
    return jsonify({
        'message': f'Chunk {chunk_index} uploaded',
        'chunkIndex': chunk_index
    }), 200

@api_bp.route('/upload/status/<upload_id>', methods=['GET'])
def upload_status(upload_id):
    """Get status of an upload (which chunks are uploaded)."""
    try:
        uploaded_chunks = UploadService.get_uploaded_chunks(upload_id)
        return jsonify({
            'uploadId': upload_id,
            'uploadedChunks': uploaded_chunks
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/upload/complete', methods=['POST'])
def complete_upload():
    """Merge chunks and finalize upload."""
    data = request.get_json()
    
    if not data or 'uploadId' not in data or 'totalChunks' not in data or 'filename' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    upload_id = data['uploadId']
    total_chunks = data['totalChunks']
    filename = data['filename']
    mimetype = data.get('mimeType', 'application/octet-stream')
    is_public = data.get('isPublic', True)
    
    # Verify all chunks are uploaded
    uploaded_chunks = UploadService.get_uploaded_chunks(upload_id)
    if len(uploaded_chunks) != total_chunks:
        missing = set(range(total_chunks)) - set(uploaded_chunks)
        return jsonify({
            'error': 'Not all chunks uploaded',
            'missing': list(missing)
        }), 400
    
    try:
        # Merge chunks
        user_id = current_user.id if current_user.is_authenticated else None
        new_file = UploadService.merge_chunks(
            upload_id, 
            total_chunks, 
            filename, 
            mimetype,
            user_id=user_id,
            is_public=is_public
        )
        
        return jsonify({
            'message': 'Upload complete',
            'fileId': new_file.id,
            'filename': new_file.original_name,
            'shareToken': new_file.share_token
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Failed to merge chunks: {str(e)}'}), 500

@api_bp.route('/upload/cancel/<upload_id>', methods=['DELETE'])
def cancel_upload(upload_id):
    """Cancel an upload and clean up chunks."""
    try:
        UploadService.cleanup_chunks(upload_id)
        return jsonify({'message': 'Upload cancelled'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/files/validate', methods=['POST'])
def validate_file():
    """Validate file before upload (size, type, etc)."""
    data = request.get_json()
    
    if not data or 'fileSize' not in data:
        return jsonify({'error': 'Missing fileSize'}), 400
    
    file_size = data['fileSize']
    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024)
    
    if file_size > max_size:
        return jsonify({
            'valid': False,
            'error': f'File size exceeds maximum allowed ({max_size / 1024 / 1024:.0f} MB)'
        }), 200
    
    # Check quota for logged-in users
    if current_user.is_authenticated:
        if not current_user.has_storage_available(file_size):
            storage_used = current_user.get_storage_used()
            storage_quota = current_user.storage_quota
            return jsonify({
                'valid': False,
                'error': f'Storage quota exceeded ({storage_used / 1024 / 1024 / 1024:.2f} GB / {storage_quota / 1024 / 1024 / 1024:.2f} GB used)'
            }), 200
    
    return jsonify({'valid': True}), 200
