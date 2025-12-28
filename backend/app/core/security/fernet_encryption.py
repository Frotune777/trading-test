"""
Fernet Token Encryption Module
Implements symmetric encryption for API keys and sensitive tokens.
Adopted from OpenAlgo's security implementation.
"""

import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

def get_pepper() -> str:
    """
    Get the API_KEY_PEPPER from environment.
    
    Returns:
        str: The pepper value
        
    Raises:
        RuntimeError: If pepper is not set or too short
    """
    pepper = os.getenv('API_KEY_PEPPER')
    if not pepper:
        raise RuntimeError(
            "CRITICAL: API_KEY_PEPPER environment variable is not set. "
            "This is required for token encryption. "
            "Generate one using: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    if len(pepper) < 32:
        raise RuntimeError(
            f"CRITICAL: API_KEY_PEPPER must be at least 32 characters (got {len(pepper)}). "
            "Generate a secure pepper using: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    return pepper

def get_encryption_key() -> Fernet:
    """
    Generate a Fernet encryption key from the pepper using PBKDF2.
    
    Uses PBKDF2 (Password-Based Key Derivation Function 2) with:
    - SHA256 hash algorithm
    - 100,000 iterations (OWASP recommended minimum)
    - Static salt (acceptable for application-level encryption)
    
    Returns:
        Fernet: Initialized Fernet cipher
    """
    pepper = get_pepper()
    
    # PBKDF2 key derivation
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # Fernet requires 32-byte key
        salt=b'openalgo_static_salt',  # Static salt for deterministic key
        iterations=100000,  # OWASP recommended minimum
    )
    
    # Derive key and encode for Fernet
    key = base64.urlsafe_b64encode(kdf.derive(pepper.encode()))
    return Fernet(key)

# Initialize global Fernet cipher
_fernet_cipher = None

def get_fernet() -> Fernet:
    """
    Get or initialize the global Fernet cipher.
    
    Returns:
        Fernet: The Fernet cipher instance
    """
    global _fernet_cipher
    if _fernet_cipher is None:
        _fernet_cipher = get_encryption_key()
    return _fernet_cipher

def encrypt_token(token: str) -> str:
    """
    Encrypt a token using Fernet symmetric encryption.
    
    Args:
        token: Plain text token to encrypt
        
    Returns:
        str: Base64-encoded encrypted token
        
    Example:
        >>> encrypted = encrypt_token("my_api_key_12345")
        >>> encrypted.startswith('gAAAAA')  # Fernet tokens start with this
        True
    """
    if not token:
        return ''
        
    try:
        fernet = get_fernet()
        encrypted = fernet.encrypt(token.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Error encrypting token: {e}")
        raise

def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a Fernet-encrypted token.
    
    Args:
        encrypted_token: Base64-encoded encrypted token
        
    Returns:
        str: Decrypted plain text token, or empty string on error
        
    Example:
        >>> encrypted = encrypt_token("my_api_key")
        >>> decrypt_token(encrypted)
        'my_api_key'
    """
    if not encrypted_token:
        return ''
        
    try:
        fernet = get_fernet()
        decrypted = fernet.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Error decrypting token: {e}")
        return None

def rotate_encryption_key(old_pepper: str, new_pepper: str, encrypted_token: str) -> str:
    """
    Rotate encryption key by decrypting with old pepper and re-encrypting with new pepper.
    
    Args:
        old_pepper: Previous pepper value
        new_pepper: New pepper value
        encrypted_token: Token encrypted with old pepper
        
    Returns:
        str: Token re-encrypted with new pepper
        
    Note:
        This is used during pepper rotation to avoid downtime.
    """
    try:
        # Temporarily set old pepper
        original_pepper = os.getenv('API_KEY_PEPPER')
        os.environ['API_KEY_PEPPER'] = old_pepper
        
        # Decrypt with old key
        global _fernet_cipher
        _fernet_cipher = None  # Force re-initialization
        decrypted = decrypt_token(encrypted_token)
        
        # Set new pepper
        os.environ['API_KEY_PEPPER'] = new_pepper
        _fernet_cipher = None  # Force re-initialization
        
        # Re-encrypt with new key
        re_encrypted = encrypt_token(decrypted)
        
        # Restore original pepper
        os.environ['API_KEY_PEPPER'] = original_pepper
        _fernet_cipher = None
        
        return re_encrypted
        
    except Exception as e:
        logger.error(f"Error rotating encryption key: {e}")
        raise
