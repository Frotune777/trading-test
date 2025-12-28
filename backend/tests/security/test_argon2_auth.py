"""
Unit tests for Argon2 password hashing module
"""

import pytest
import os
from app.core.security.argon2_auth import (
    hash_password,
    verify_password,
    needs_rehash,
    get_pepper
)

# Set test pepper for consistent testing
TEST_PEPPER = "test_pepper_" + "x" * 32

@pytest.fixture(autouse=True)
def set_test_pepper(monkeypatch):
    """Set test pepper for all tests"""
    monkeypatch.setenv("API_KEY_PEPPER", TEST_PEPPER)

class TestArgon2Auth:
    """Test suite for Argon2 authentication"""
    
    def test_hash_password_produces_valid_format(self):
        """Test that hashed password starts with $argon2id$"""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed.startswith("$argon2id$")
        assert len(hashed) > 50  # Argon2 hashes are long
    
    def test_verify_password_succeeds_for_correct_password(self):
        """Test that verification succeeds for correct password"""
        password = "my_secure_password"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_fails_for_incorrect_password(self):
        """Test that verification fails for incorrect password"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_fails_for_invalid_hash(self):
        """Test that verification fails gracefully for invalid hash"""
        password = "test_password"
        invalid_hash = "not_a_valid_argon2_hash"
        
        assert verify_password(password, invalid_hash) is False
    
    def test_hash_without_pepper(self):
        """Test hashing without pepper"""
        password = "test_password"
        hashed = hash_password(password, use_pepper=False)
        
        assert hashed.startswith("$argon2id$")
        assert verify_password(password, hashed, use_pepper=False) is True
    
    def test_different_passwords_produce_different_hashes(self):
        """Test that different passwords produce different hashes"""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = hash_password(password1)
        hash2 = hash_password(password2)
        
        assert hash1 != hash2
    
    def test_same_password_produces_different_hashes(self):
        """Test that same password produces different hashes (due to salt)"""
        password = "same_password"
        
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different due to random salt
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    def test_needs_rehash_detection(self):
        """Test rehash detection (should be False for fresh hashes)"""
        password = "test_password"
        hashed = hash_password(password)
        
        # Fresh hash should not need rehashing
        assert needs_rehash(hashed) is False
    
    def test_get_pepper_raises_error_when_not_set(self, monkeypatch):
        """Test that get_pepper raises error when API_KEY_PEPPER not set"""
        monkeypatch.delenv("API_KEY_PEPPER", raising=False)
        
        with pytest.raises(RuntimeError, match="API_KEY_PEPPER environment variable is not set"):
            get_pepper()
    
    def test_get_pepper_raises_error_when_too_short(self, monkeypatch):
        """Test that get_pepper raises error when pepper is too short"""
        monkeypatch.setenv("API_KEY_PEPPER", "short")
        
        with pytest.raises(RuntimeError, match="must be at least 32 characters"):
            get_pepper()
    
    def test_pepper_affects_hash(self, monkeypatch):
        """Test that different peppers produce different hashes"""
        password = "test_password"
        
        # Hash with first pepper
        monkeypatch.setenv("API_KEY_PEPPER", "pepper1_" + "x" * 32)
        hash1 = hash_password(password)
        
        # Hash with second pepper
        monkeypatch.setenv("API_KEY_PEPPER", "pepper2_" + "x" * 32)
        hash2 = hash_password(password)
        
        # Hashes should be different
        assert hash1 != hash2
        
        # Verification should fail with wrong pepper
        assert verify_password(password, hash1) is False
        
        # Verification should succeed with correct pepper
        monkeypatch.setenv("API_KEY_PEPPER", "pepper1_" + "x" * 32)
        assert verify_password(password, hash1) is True
