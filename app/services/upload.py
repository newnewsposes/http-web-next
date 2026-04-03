"""
Upload service - handles chunked file uploads and resumable transfers.
"""
import os
import hashlib
from werkzeug.utils import secure_filename
from flask import current_app
from app import db
from app.models.file import File
import uuid

class UploadService:
    """Service for handling chunked file uploads."""
    
    CHUNK_FOLDER = 'chunks'
    
    @staticmethod
    def get_chunks_dir():
        """Get or create the chunks directory."""
        chunks_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], UploadService.CHUNK_FOLDER)
        os.makedirs(chunks_dir, exist_ok=True)
        return chunks_dir
    
    @staticmethod
    def get_upload_dir(upload_id):
        """Get or create directory for a specific upload session."""
        upload_dir = os.path.join(UploadService.get_chunks_dir(), upload_id)
        os.makedirs(upload_dir, exist_ok=True)
        return upload_dir
    
    @staticmethod
    def save_chunk(upload_id, chunk_index, chunk_data):
        """Save a single chunk to disk."""
        upload_dir = UploadService.get_upload_dir(upload_id)
        chunk_path = os.path.join(upload_dir, f'chunk_{chunk_index}')
        
        with open(chunk_path, 'wb') as f:
            f.write(chunk_data)
        
        return chunk_path
    
    @staticmethod
    def get_uploaded_chunks(upload_id):
        """Get list of chunk indices that have been uploaded."""
        upload_dir = UploadService.get_upload_dir(upload_id)
        
        if not os.path.exists(upload_dir):
            return []
        
        chunks = []
        for filename in os.listdir(upload_dir):
            if filename.startswith('chunk_'):
                try:
                    chunk_index = int(filename.split('_')[1])
                    chunks.append(chunk_index)
                except (IndexError, ValueError):
                    continue
        
        return sorted(chunks)
    
    @staticmethod
    def merge_chunks(upload_id, total_chunks, original_filename, mimetype, user_id=None, is_public=True):
        """Merge all chunks into final file and create database record."""
        upload_dir = UploadService.get_upload_dir(upload_id)
        
        # Generate unique filename
        safe_filename = secure_filename(original_filename)
        unique_filename = f"{uuid.uuid4().hex}_{safe_filename}"
        final_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Merge chunks
        with open(final_path, 'wb') as outfile:
            for i in range(total_chunks):
                chunk_path = os.path.join(upload_dir, f'chunk_{i}')
                
                if not os.path.exists(chunk_path):
                    raise FileNotFoundError(f'Missing chunk {i}')
                
                with open(chunk_path, 'rb') as infile:
                    outfile.write(infile.read())
        
        # Get file size
        file_size = os.path.getsize(final_path)
        
        # Create database record
        new_file = File(
            filename=unique_filename,
            original_name=original_filename,
            mimetype=mimetype,
            size=file_size,
            user_id=user_id,
            is_public=is_public
        )
        db.session.add(new_file)
        db.session.commit()
        
        # Clean up chunks
        UploadService.cleanup_chunks(upload_id)
        
        return new_file
    
    @staticmethod
    def cleanup_chunks(upload_id):
        """Remove all chunks for an upload session."""
        upload_dir = UploadService.get_upload_dir(upload_id)
        
        if os.path.exists(upload_dir):
            for filename in os.listdir(upload_dir):
                file_path = os.path.join(upload_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(upload_dir)
    
    @staticmethod
    def calculate_file_hash(filepath):
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
