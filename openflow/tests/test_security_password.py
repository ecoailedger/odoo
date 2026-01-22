"""
Tests for password hashing and verification
"""
import pytest
from openflow.server.core.security import (
    hash_password,
    verify_password,
    needs_update,
    verify_and_update,
)


class TestPasswordHashing:
    """Test password hashing functions"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "my_secure_password_123"
        hashed = hash_password(password)

        # Hash should be different from plain password
        assert hashed != password

        # Hash should start with argon2id
        assert hashed.startswith("$argon2id$")

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "correct_password"
        hashed = hash_password(password)

        # Should verify successfully
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        # Should fail verification
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_invalid_hash(self):
        """Test password verification with invalid hash"""
        password = "some_password"
        invalid_hash = "not_a_valid_hash"

        # Should return False for invalid hash
        assert verify_password(password, invalid_hash) is False

    def test_needs_update_new_hash(self):
        """Test needs_update with current algorithm"""
        password = "test_password"
        hashed = hash_password(password)

        # New argon2 hash should not need update
        assert needs_update(hashed) is False

    def test_verify_and_update_correct(self):
        """Test verify_and_update with correct password"""
        password = "test_password_123"
        hashed = hash_password(password)

        verified, new_hash = verify_and_update(password, hashed)

        # Should verify successfully
        assert verified is True

        # Should not need update if using current algorithm
        assert new_hash is None

    def test_verify_and_update_incorrect(self):
        """Test verify_and_update with incorrect password"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        verified, new_hash = verify_and_update(wrong_password, hashed)

        # Should fail verification
        assert verified is False
        assert new_hash is None

    def test_different_passwords_different_hashes(self):
        """Test that same password generates different hashes (salt)"""
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different due to random salt
        assert hash1 != hash2

        # But both should verify successfully
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_empty_password(self):
        """Test hashing empty password"""
        password = ""
        hashed = hash_password(password)

        # Should still hash and verify
        assert verify_password(password, hashed) is True

    def test_unicode_password(self):
        """Test hashing unicode password"""
        password = "пароль密码🔐"
        hashed = hash_password(password)

        # Should hash and verify unicode passwords
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_long_password(self):
        """Test hashing very long password"""
        password = "a" * 1000  # 1000 character password
        hashed = hash_password(password)

        # Should handle long passwords
        assert verify_password(password, hashed) is True
