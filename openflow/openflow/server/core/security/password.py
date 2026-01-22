"""Password hashing and verification using argon2 or bcrypt.

This module provides secure password hashing using the Argon2 algorithm
(winner of the Password Hashing Competition) with bcrypt as a fallback.
"""

from passlib.context import CryptContext
from typing import Optional


# Password hashing context with multiple schemes
# Argon2 is the primary scheme (most secure)
# Bcrypt is deprecated but supported for migration
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",

    # Argon2 configuration (Argon2id variant)
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,         # 3 iterations
    argon2__parallelism=4,       # 4 threads

    # Bcrypt configuration
    bcrypt__rounds=12,
)


def hash_password(password: str) -> str:
    """Hash a password using argon2.

    Args:
        password: The plain text password to hash

    Returns:
        The hashed password string

    Example:
        >>> hashed = hash_password("my_secure_password")
        >>> print(hashed)
        $argon2id$v=19$m=65536,t=3,p=4$...
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to verify against

    Returns:
        True if the password matches, False otherwise

    Example:
        >>> hashed = hash_password("my_password")
        >>> verify_password("my_password", hashed)
        True
        >>> verify_password("wrong_password", hashed)
        False
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Invalid hash format or other error
        return False


def needs_update(hashed_password: str) -> bool:
    """Check if a password hash needs to be updated.

    This returns True if the password was hashed with a deprecated
    scheme (e.g., bcrypt) or with outdated parameters.

    Args:
        hashed_password: The hashed password to check

    Returns:
        True if the hash should be updated, False otherwise

    Example:
        >>> # If password was hashed with bcrypt
        >>> old_hash = "$2b$12$..."
        >>> needs_update(old_hash)
        True

        >>> # If password was hashed with current argon2
        >>> new_hash = "$argon2id$..."
        >>> needs_update(new_hash)
        False
    """
    return pwd_context.needs_update(hashed_password)


def verify_and_update(
    plain_password: str,
    hashed_password: str
) -> tuple[bool, Optional[str]]:
    """Verify a password and return updated hash if needed.

    This is a convenience method that combines verify_password and
    needs_update. If the password is correct but the hash needs
    updating (e.g., old algorithm), it returns the new hash.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The current hashed password

    Returns:
        A tuple of (verified, new_hash) where:
        - verified: True if password is correct
        - new_hash: New hash if update needed, None otherwise

    Example:
        >>> old_hash = hash_password("password")  # Imagine this was bcrypt
        >>> verified, new_hash = verify_and_update("password", old_hash)
        >>> if verified and new_hash:
        ...     # Update the hash in database
        ...     user.password = new_hash
    """
    try:
        verified, new_hash = pwd_context.verify_and_update(
            plain_password,
            hashed_password
        )
        return verified, new_hash
    except Exception:
        return False, None
