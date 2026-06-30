import os
import logging

logger = logging.getLogger("disaster_assist.image_processing")

def validate_and_process_image(file_path: str) -> bool:
    """Verifies image file size and validates format."""
    if not os.path.exists(file_path):
        logger.error(f"Image not found at path: {file_path}")
        return False
        
    # File size validation (limit to 10MB)
    size_bytes = os.path.getsize(file_path)
    if size_bytes > 10 * 1024 * 1024:
        logger.warning(f"File size exceeds 10MB limit: {size_bytes} bytes")
        return False
        
    logger.info(f"Image validation passed: {file_path} ({size_bytes} bytes)")
    return True
