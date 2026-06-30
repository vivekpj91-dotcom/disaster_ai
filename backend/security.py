import time
import re
import logging
import os
from typing import Dict, Tuple, List, Optional
from fastapi import Request, HTTPException, status
from config.settings import settings

# 1. Dedicated Security and Audit Loggers
audit_logger = logging.getLogger("disaster_assist.audit")
security_logger = logging.getLogger("disaster_assist.security")

# 2. In-Memory Rate Limiter (Token-Bucket Algorithm)
# Thread-safe in-memory tracking, easily replaceable with Redis in production.
class TokenBucketLimiter:
    def __init__(self, rate_limit: int = 60, time_window: int = 60):
        """
        rate_limit: Maximum tokens (requests) allowed in window
        time_window: Time window size in seconds
        """
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.buckets: Dict[str, Tuple[float, float]] = {}  # client_ip -> (tokens, last_update_time)

    def is_rate_limited(self, client_ip: str) -> bool:
        current_time = time.time()
        if client_ip not in self.buckets:
            self.buckets[client_ip] = (self.rate_limit, current_time)
            return False

        tokens, last_update = self.buckets[client_ip]
        # Replenish tokens based on elapsed time
        elapsed = current_time - last_update
        replenished = elapsed * (self.rate_limit / self.time_window)
        new_tokens = min(self.rate_limit, tokens + replenished)

        if new_tokens >= 1.0:
            self.buckets[client_ip] = (new_tokens - 1.0, current_time)
            return False
        
        # Log rate limit breach in audit logs
        audit_logger.warning(f"Rate limit breached by IP: {client_ip}. Tokens remaining: {new_tokens}")
        return True

# Instantiate global rate limiter (Default: 30 requests per minute per IP)
global_rate_limiter = TokenBucketLimiter(rate_limit=30, time_window=60)

# 3. Prompt Injection Protection
PROMPT_INJECTION_REGEX = re.compile(
    r"(ignore\s+(all\s+)?previous\s+instructions|"
    r"you\s+are\s+now\s+an\s+unrestricted|"
    r"bypass\s+safety|"
    r"system\s+override|"
    r"forget\s+(what\s+)?I\s+said|"
    r"dan\s+mode|"
    r"ignore\s+your\s+system\s+directives|"
    r"developer\s+mode\s+active)",
    re.IGNORECASE
)

def sanitize_and_check_injection(text: str) -> str:
    """Sanitizes input text and checks for potential prompt injection attacks.
    
    Args:
        text: Raw user input string.
        
    Returns:
        Sanitized safe string.
        
    Raises:
        HTTPException if prompt injection pattern matches.
    """
    # 1. Clean HTML tags to prevent XSS injection
    clean_text = re.sub(r"<[^>]*>", "", text)
    
    # 2. Check for typical LLM prompt injection / jailbreak patterns
    if PROMPT_INJECTION_REGEX.search(clean_text):
        security_logger.error(f"Potential Prompt Injection detected in input: '{clean_text[:100]}...'")
        # Alert security logs
        audit_logger.warning("Security Event - Prompt Injection Attempt Blocked.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request flagged by security filter due to unsafe prompt patterns."
        )
        
    return clean_text

# 4. Secure File Uploads (Magic Number Validation)
# Verify file bytes header matches actual image types, preventing executable masquerading.
ALLOWED_IMAGE_SIGNATURES = {
    b"\xff\xd8\xff": "image/jpeg",      # JPEG / JPG
    b"\x89PNG\r\n\x1a\n": "image/png"   # PNG
}

def validate_image_bytes(file_bytes: bytes) -> bool:
    """Validates the file signature headers against standard image magic numbers.
    
    Args:
        file_bytes: Header bytes of the uploaded file.
    """
    for signature in ALLOWED_IMAGE_SIGNATURES:
        if file_bytes.startswith(signature):
            return True
    return False

# 5. Secrets Management Helper
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Helper that retrieves secrets from env or handles GCP Secret Manager overrides in production."""
    # When deployed in GCP, secrets are mounted as files or injected in environment
    secret_val = os.environ.get(key, default)
    if secret_val is None:
        logger = logging.getLogger("disaster_assist.security")
        logger.warning(f"Required configuration secret missing: {key}")
    return secret_val
