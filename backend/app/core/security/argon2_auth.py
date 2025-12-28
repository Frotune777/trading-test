"""
Argon2 Password Hashing Module
Implements enterprise-grade password hashing using Argon2id.
Adopted from OpenAlgo's security implementation.
"""

import os
import logging
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHash

logger = logging.getLogger(__name__)

# Initialize Argon2 hasher with production-grade parameters
# Argon2id is a hybrid of Argon2i (optimized against side-channel attacks)
# and Argon2d (optimized against GPU cracking attacks)
ph = PasswordHasher(
    time_cost=3,        # Number of iterations
    memory_cost=65536,  # Memory usage in KB (64 MB)
    parallelism=4,      # Number of parallel threads
    hash_len=32,        # Length of the hash in bytes
    salt_len=16         # Length of the salt in bytes
)

def get_pepper() -> str:
    """
    Get the API_KEY_PEPPER from environment.
    This adds an additional layer of security beyond the salt.
    
    Returns:
        str: The pepper value
        
    Raises:
        RuntimeError: If pepper is not set or too short
    """
    pepper = os.getenv('API_KEY_PEPPER')
    if not pepper:
        raise RuntimeError(
            "CRITICAL: API_KEY_PEPPER environment variable is not set. "
            "This is required for secure password hashing. "
            "Generate one using: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    if len(pepper) < 32:
        raise RuntimeError(
            f"CRITICAL: API_KEY_PEPPER must be at least 32 characters (got {len(pepper)}). "
            "Generate a secure pepper using: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    return pepper

def hash_password(password: str, use_pepper: bool = True) -> str:
    """
    Hash a password using Argon2id with optional pepper.
    
    Args:
        password: Plain text password to hash
        use_pepper: Whether to add pepper to the password (default: True)
        
    Returns:
        str: Argon2 hash string (starts with $argon2id$)
        
    Example:
        >>> hash_password("my_secure_password")
        '$argon2id$v=19$m=65536,t=3,p=4$...'
    """
    try:
        if use_pepper:
            pepper = get_pepper()
            peppered_password = password + pepper
        else:
            peppered_password = password
            
        hashed = ph.hash(peppered_password)
        logger.debug("Password hashed successfully")
        return hashed
        
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise

def verify_password(password: str, password_hash: str, use_pepper: bool = True) -> bool:
    """
    Verify a password against an Argon2 hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Argon2 hash to verify against
        use_pepper: Whether the hash was created with pepper (default: True)
        
    Returns:
        bool: True if password matches, False otherwise
        
    Example:
        >>> hash_val = hash_password("my_password")
        >>> verify_password("my_password", hash_val)
        True
        >>> verify_password("wrong_password", hash_val)
        False
    """
    try:
        if use_pepper:
            pepper = get_pepper()
            peppered_password = password + pepper
        else:
            peppered_password = password
            
        # This will raise VerifyMismatchError if verification fails
        ph.verify(password_hash, peppered_password)
        
        # Check if the hash needs to be rehashed (parameters changed)
        if ph.check_needs_rehash(password_hash):
            logger.info("Password hash needs rehashing with updated parameters")
            # Note: The caller should rehash and update the database
            
        return True
        
    except VerifyMismatchError:
        logger.debug("Password verification failed: incorrect password")
        return False
    except InvalidHash:
        logger.error(f"Invalid Argon2 hash format: {password_hash[:20]}...")
        return False
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False

def needs_rehash(password_hash: str) -> bool:
    """
    Check if a password hash needs to be rehashed with updated parameters.
    
    Args:
        password_hash: Argon2 hash to check
        
    Returns:
        bool: True if rehashing is recommended
    """
    try:
        return ph.check_needs_rehash(password_hash)
    except Exception as e:
        logger.error(f"Error checking rehash status: {e}")
        return False
