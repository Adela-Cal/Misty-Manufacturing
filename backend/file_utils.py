import os
import uuid
from typing import Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
import shutil
from pathlib import Path

# File upload configuration
UPLOAD_DIR = "/app/uploads"
LOGO_DIR = f"{UPLOAD_DIR}/logos"
DOCUMENT_DIR = f"{UPLOAD_DIR}/documents"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}

def ensure_upload_dirs():
    """Create upload directories if they don't exist"""
    os.makedirs(LOGO_DIR, exist_ok=True)
    os.makedirs(DOCUMENT_DIR, exist_ok=True)

def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return Path(filename).suffix.lower()

def generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename while preserving extension"""
    extension = get_file_extension(original_filename)
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{extension}"

def validate_image_file(file: UploadFile) -> bool:
    """Validate if uploaded file is a valid image"""
    if not file.filename:
        return False
    
    extension = get_file_extension(file.filename)
    return extension in ALLOWED_IMAGE_EXTENSIONS

def validate_document_file(file: UploadFile) -> bool:
    """Validate if uploaded file is a valid document"""
    if not file.filename:
        return False
    
    extension = get_file_extension(file.filename)
    return extension in ALLOWED_DOCUMENT_EXTENSIONS

def validate_file_size(file: UploadFile) -> bool:
    """Validate file size"""
    # Read file to check size
    file_content = file.file.read()
    file.file.seek(0)  # Reset file pointer
    return len(file_content) <= MAX_FILE_SIZE

async def save_logo_file(file: UploadFile, client_id: str) -> str:
    """Save uploaded logo file and return file path"""
    ensure_upload_dirs()
    
    # Validate file
    if not validate_image_file(file):
        raise HTTPException(status_code=400, detail="Invalid image file type")
    
    if not validate_file_size(file):
        raise HTTPException(status_code=400, detail="File size too large (max 5MB)")
    
    # Generate unique filename
    unique_filename = f"{client_id}_{generate_unique_filename(file.filename)}"
    file_path = os.path.join(LOGO_DIR, unique_filename)
    
    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate and potentially resize image
        try:
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Resize if too large (max 800x600 for logos)
                max_size = (800, 600)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    img.save(file_path, "JPEG", quality=85)
        
        except Exception as e:
            # If image processing fails, remove the file
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        return file_path
    
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Failed to save file")

async def save_document_file(file: UploadFile, document_type: str) -> str:
    """Save uploaded document file and return file path"""
    ensure_upload_dirs()
    
    # Validate file
    if not validate_document_file(file):
        raise HTTPException(status_code=400, detail="Invalid document file type")
    
    if not validate_file_size(file):
        raise HTTPException(status_code=400, detail="File size too large (max 5MB)")
    
    # Generate unique filename
    unique_filename = f"{document_type}_{generate_unique_filename(file.filename)}"
    file_path = os.path.join(DOCUMENT_DIR, unique_filename)
    
    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return file_path
    
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Failed to save document")

def delete_file(file_path: str) -> bool:
    """Delete file from filesystem"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False

def get_file_url(file_path: str) -> Optional[str]:
    """Generate URL for accessing uploaded file"""
    if not file_path or not os.path.exists(file_path):
        return None
    
    # Convert absolute path to relative URL
    relative_path = file_path.replace("/app/uploads/", "")
    return f"/api/uploads/{relative_path}"

def cleanup_old_files(days: int = 30):
    """Clean up old uploaded files (for maintenance)"""
    import time
    
    ensure_upload_dirs()
    current_time = time.time()
    cutoff_time = current_time - (days * 24 * 60 * 60)
    
    for directory in [LOGO_DIR, DOCUMENT_DIR]:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                file_time = os.path.getmtime(file_path)
                if file_time < cutoff_time:
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass  # Ignore errors during cleanup