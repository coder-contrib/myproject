"""Unit tests for security/JWT utilities."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from jose import jwt


SECRET_KEY = "test-secret-key-for-testing-only"
ALGORITHM = "HS256"


@pytest.mark.unit
class TestJWTToken:
    def test_create_access_token(self):
        from app.core.security import create_access_token

        data = {"sub": "user@test.com", "tenant_id": 1}
        token = create_access_token(data)
        assert token is not None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "user@test.com"
        assert payload["tenant_id"] == 1
        assert "exp" in payload

    def test_access_token_expiration(self):
        from app.core.security import create_access_token

        data = {"sub": "user@test.com"}
        token = create_access_token(data, expires_delta=timedelta(minutes=30))
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = datetime.utcfromtimestamp(payload["exp"])
        assert exp > datetime.utcnow()
        assert exp < datetime.utcnow() + timedelta(minutes=31)

    def test_create_refresh_token(self):
        from app.core.security import create_refresh_token

        data = {"sub": "user@test.com"}
        token = create_refresh_token(data)
        assert token is not None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "user@test.com"
        assert payload["type"] == "refresh"

    def test_expired_token_raises(self):
        from app.core.security import create_access_token

        data = {"sub": "user@test.com"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        with pytest.raises(Exception):
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    def test_invalid_token_raises(self):
        with pytest.raises(Exception):
            jwt.decode("invalid.token.here", SECRET_KEY, algorithms=[ALGORITHM])

    def test_token_with_wrong_key_raises(self):
        from app.core.security import create_access_token

        token = create_access_token({"sub": "user@test.com"})
        with pytest.raises(Exception):
            jwt.decode(token, "wrong-key", algorithms=[ALGORITHM])


@pytest.mark.unit
class TestPasswordHashing:
    def test_hash_password(self):
        from app.core.security import hash_password

        hashed = hash_password("mypassword123")
        assert hashed != "mypassword123"
        assert len(hashed) > 50

    def test_verify_password_correct(self):
        from app.core.security import hash_password, verify_password

        hashed = hash_password("mypassword123")
        assert verify_password("mypassword123", hashed) is True

    def test_verify_password_incorrect(self):
        from app.core.security import hash_password, verify_password

        hashed = hash_password("mypassword123")
        assert verify_password("wrongpassword", hashed) is False

    def test_different_passwords_different_hashes(self):
        from app.core.security import hash_password

        hash1 = hash_password("password1")
        hash2 = hash_password("password2")
        assert hash1 != hash2

    def test_same_password_different_hashes(self):
        from app.core.security import hash_password

        hash1 = hash_password("same_password")
        hash2 = hash_password("same_password")
        assert hash1 != hash2  # bcrypt uses random salt
