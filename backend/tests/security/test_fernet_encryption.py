"""
Unit tests for Fernet token encryption module
"""

import pytest
import os
from app.core.security.fernet_encryption import (
    encrypt_token,
    decrypt_token,
    get_encryption_key,
    get_fernet,
    rotate_encryption_key
)

# Set test pepper for consistent testing
TEST_PEPPER = "test_pepper_" + "x" * 32

@pytest.fixture(autouse=True)
def set_test_pepper(monkeypatch):
    """Set test pepper for all tests"""
    monkeypatch.setenv("API_KEY_PEPPER", TEST_PEPPER)

class TestFernetEncryption:
    """Test suite for Fernet token encryption"""
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption work correctly"""
        token = "my_api_key_12345"
        
        encrypted = encrypt_token(token)
        decrypted = decrypt_token(encrypted)
        
        assert decrypted == token
    
    def test_encrypted_token_format(self):
        """Test that encrypted tokens have correct Fernet format"""
        token = "test_token"
        encrypted = encrypt_token(token)
        
        # Fernet tokens are base64-encoded and start with 'gAAAAA'
        assert isinstance(encrypted, str)
        assert len(encrypted) > 20
        # Fernet tokens typically start with 'gAAAAA' but this can vary
        assert encrypted.startswith('gAAAAA')
    
    def test_empty_token_handling(self):
        """Test that empty tokens are handled correctly"""
        assert encrypt_token("") == ""
        assert decrypt_token("") == ""
    
    def test_decrypt_invalid_token_returns_none(self):
        """Test that decrypting invalid token returns None"""
        invalid_token = "not_a_valid_fernet_token"
        
        result = decrypt_token(invalid_token)
        assert result is None
    
    def test_different_tokens_produce_different_ciphertexts(self):
        """Test that different tokens produce different ciphertexts"""
        token1 = "token_one"
        token2 = "token_two"
        
        encrypted1 = encrypt_token(token1)
        encrypted2 = encrypt_token(token2)
        
        assert encrypted1 != encrypted2
    
    def test_same_token_produces_different_ciphertexts(self):
        """Test that same token produces different ciphertexts (due to IV)"""
        token = "same_token"
        
        encrypted1 = encrypt_token(token)
        encrypted2 = encrypt_token(token)
        
        # Ciphertexts should be different due to random IV
        assert encrypted1 != encrypted2
        # But both should decrypt to the same value
        assert decrypt_token(encrypted1) == token
        assert decrypt_token(encrypted2) == token
    
    def test_get_fernet_returns_same_instance(self):
        """Test that get_fernet returns the same instance (singleton)"""
        fernet1 = get_fernet()
        fernet2 = get_fernet()
        
        assert fernet1 is fernet2
    
    def test_encryption_key_derivation_is_deterministic(self, monkeypatch):
        """Test that same pepper produces same encryption key"""
        monkeypatch.setenv("API_KEY_PEPPER", "test_pepper_" + "x" * 32)
        
        key1 = get_encryption_key()
        key2 = get_encryption_key()
        
        # Keys should be different instances but encrypt/decrypt the same
        token = "test_token"
        encrypted1 = key1.encrypt(token.encode()).decode()
        decrypted2 = key2.decrypt(encrypted1.encode()).decode()
        
        assert decrypted2 == token
    
    def test_different_peppers_produce_different_keys(self, monkeypatch):
        """Test that different peppers produce different encryption keys"""
        token = "test_token"
        
        # Encrypt with first pepper
        monkeypatch.setenv("API_KEY_PEPPER", "pepper1_" + "x" * 32)
        # Force re-initialization
        import app.core.security.fernet_encryption as fe
        fe._fernet_cipher = None
        encrypted = encrypt_token(token)
        
        # Try to decrypt with second pepper (should fail)
        monkeypatch.setenv("API_KEY_PEPPER", "pepper2_" + "x" * 32)
        fe._fernet_cipher = None
        decrypted = decrypt_token(encrypted)
        
        assert decrypted is None  # Decryption should fail
    
    def test_rotate_encryption_key(self, monkeypatch):
        """Test key rotation functionality"""
        token = "api_key_to_rotate"
        old_pepper = "old_pepper_" + "x" * 32
        new_pepper = "new_pepper_" + "x" * 32
        
        # Encrypt with old pepper
        monkeypatch.setenv("API_KEY_PEPPER", old_pepper)
        import app.core.security.fernet_encryption as fe
        fe._fernet_cipher = None
        encrypted_old = encrypt_token(token)
        
        # Rotate to new pepper
        re_encrypted = rotate_encryption_key(old_pepper, new_pepper, encrypted_old)
        
        # Verify with new pepper
        monkeypatch.setenv("API_KEY_PEPPER", new_pepper)
        fe._fernet_cipher = None
        decrypted = decrypt_token(re_encrypted)
        
        assert decrypted == token
    
    def test_long_token_encryption(self):
        """Test encryption of long tokens"""
        long_token = "x" * 1000
        
        encrypted = encrypt_token(long_token)
        decrypted = decrypt_token(encrypted)
        
        assert decrypted == long_token
    
    def test_special_characters_in_token(self):
        """Test encryption of tokens with special characters"""
        special_token = "api_key!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        
        encrypted = encrypt_token(special_token)
        decrypted = decrypt_token(encrypted)
        
        assert decrypted == special_token
