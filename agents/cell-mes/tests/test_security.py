"""Tests for security utilities (JWT, password hashing)."""

from datetime import timedelta
import time

from src.app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)


class TestPasswordHashing:
    """Test password hashing utilities."""

    def test_hash_password(self):
        """Password hashing produces different hash each time."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different (due to random salt)
        assert hash1 != hash2
        # Both should start with bcrypt identifier
        assert hash1.startswith("$2b$")
        assert hash2.startswith("$2b$")

    def test_verify_password_correct(self):
        """Correct password verifies successfully."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Incorrect password fails verification."""
        password = "correctpassword"
        hashed = get_password_hash(password)

        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty(self):
        """Empty password handling."""
        hashed = get_password_hash("somepassword")

        assert verify_password("", hashed) is False

    def test_hash_special_characters(self):
        """Password with special characters hashes correctly."""
        password = "p@ssw0rd!#$%^&*()"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_hash_unicode_password(self):
        """Unicode password hashes correctly."""
        password = "비밀번호123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_hash_long_password(self):
        """Long password (up to bcrypt's 72 byte limit) hashes correctly."""
        # bcrypt has a 72-byte limit for passwords
        password = "a" * 72
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Access token is created successfully."""
        token = create_access_token(subject="user123")

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT has 3 parts separated by dots
        assert len(token.split(".")) == 3

    def test_create_access_token_with_custom_expiry(self):
        """Access token with custom expiry."""
        token = create_access_token(
            subject="user123",
            expires_delta=timedelta(hours=24),
        )

        assert token is not None
        # Token should be decodable
        subject = decode_access_token(token)
        assert subject == "user123"

    def test_decode_access_token_valid(self):
        """Valid token decodes successfully."""
        original_subject = "user456"
        token = create_access_token(subject=original_subject)

        decoded_subject = decode_access_token(token)

        assert decoded_subject == original_subject

    def test_decode_access_token_invalid(self):
        """Invalid token returns None."""
        invalid_token = "invalid.token.here"

        result = decode_access_token(invalid_token)

        assert result is None

    def test_decode_access_token_tampered(self):
        """Tampered token returns None."""
        token = create_access_token(subject="user123")
        # Tamper with the token
        parts = token.split(".")
        parts[1] = parts[1][:-5] + "xxxxx"  # Modify payload
        tampered_token = ".".join(parts)

        result = decode_access_token(tampered_token)

        assert result is None

    def test_decode_access_token_expired(self):
        """Expired token returns None."""
        # Create token that expires immediately
        token = create_access_token(
            subject="user123",
            expires_delta=timedelta(seconds=-1),  # Already expired
        )

        result = decode_access_token(token)

        assert result is None

    def test_token_with_integer_subject(self):
        """Token works with integer subject (converted to string)."""
        token = create_access_token(subject=12345)

        decoded = decode_access_token(token)

        assert decoded == "12345"

    def test_decode_empty_token(self):
        """Empty token returns None."""
        result = decode_access_token("")

        assert result is None

    def test_decode_malformed_token(self):
        """Malformed token returns None."""
        malformed_tokens = [
            "not-a-jwt",
            "only.two.parts.extra",
            "...",
            " ",
        ]

        for token in malformed_tokens:
            result = decode_access_token(token)
            assert result is None, f"Token {token} should return None"


class TestTokenExpiration:
    """Test token expiration behavior."""

    def test_token_near_expiry(self):
        """Token near expiry still works."""
        # Create token expiring in 5 seconds
        token = create_access_token(
            subject="user123",
            expires_delta=timedelta(seconds=5),
        )

        # Should still be valid
        result = decode_access_token(token)
        assert result == "user123"

    def test_token_just_expired(self):
        """Token that just expired is rejected."""
        # Create token expiring in 1 second
        token = create_access_token(
            subject="user123",
            expires_delta=timedelta(seconds=1),
        )

        # Wait for expiration
        time.sleep(2)

        result = decode_access_token(token)
        assert result is None


class TestPasswordSecurityProperties:
    """Test security properties of password hashing."""

    def test_hash_is_not_reversible(self):
        """Hash doesn't contain the original password."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)

        # Password shouldn't appear in hash
        assert password not in hashed

    def test_similar_passwords_different_hashes(self):
        """Similar passwords produce completely different hashes."""
        hash1 = get_password_hash("password1")
        hash2 = get_password_hash("password2")

        # Even one character difference should produce very different hash
        assert hash1 != hash2
        # Hashes shouldn't share significant portions (beyond bcrypt prefix)
        assert hash1[7:] != hash2[7:]

    def test_case_sensitive_passwords(self):
        """Password verification is case sensitive."""
        password = "MyPassword"
        hashed = get_password_hash(password)

        assert verify_password("MyPassword", hashed) is True
        assert verify_password("mypassword", hashed) is False
        assert verify_password("MYPASSWORD", hashed) is False


class TestJWTSecurityProperties:
    """Test security properties of JWT tokens."""

    def test_different_subjects_different_tokens(self):
        """Different subjects produce different tokens."""
        token1 = create_access_token(subject="user1")
        token2 = create_access_token(subject="user2")

        assert token1 != token2

    def test_same_subject_different_tokens(self):
        """Same subject with different expiry produces different tokens."""
        from datetime import timedelta

        token1 = create_access_token(subject="user1", expires_delta=timedelta(minutes=30))
        token2 = create_access_token(subject="user1", expires_delta=timedelta(minutes=60))

        # Tokens will be different due to different expiry times
        assert token1 != token2

    def test_token_contains_subject_info(self):
        """Token can be decoded to retrieve subject."""
        subject = "unique_user_identifier_12345"
        token = create_access_token(subject=subject)

        decoded = decode_access_token(token)

        assert decoded == subject
