"""
Preview service - generates previews for images, videos, and documents.
"""
import os
from PIL import Image
import mimetypes

class PreviewService:
    """Service for generating file previews."""
    
    PREVIEW_FOLDER = 'previews'
    THUMBNAIL_SIZE = (300, 300)
    
    @staticmethod
    def get_previews_dir(upload_folder):
        """Get or create previews directory."""
        previews_dir = os.path.join(upload_folder, PreviewService.PREVIEW_FOLDER)
        os.makedirs(previews_dir, exist_ok=True)
        return previews_dir
    
    @staticmethod
    def can_preview(mimetype):
        """Check if file type can be previewed."""
        if not mimetype:
            return False
        
        previewable_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'video/mp4', 'video/webm',
            'application/pdf'
        ]
        
        return mimetype in previewable_types
    
    @staticmethod
    def generate_image_thumbnail(filepath, output_path):
        """Generate thumbnail for image files."""
        try:
            with Image.open(filepath) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = rgb_img
                
                # Generate thumbnail
                img.thumbnail(PreviewService.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                img.save(output_path, 'JPEG', quality=85)
                return True
        except Exception as e:
            print(f"Failed to generate thumbnail: {e}")
            return False
    
    @staticmethod
    def get_preview_path(upload_folder, filename):
        """Get path to preview file."""
        previews_dir = PreviewService.get_previews_dir(upload_folder)
        name_without_ext = os.path.splitext(filename)[0]
        return os.path.join(previews_dir, f"{name_without_ext}_thumb.jpg")
