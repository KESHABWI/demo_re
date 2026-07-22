"""Very basic token check."""

import hashlib

SECRET = "changeme"


def hash_password(password):
    return hashlib.sha256((password + SECRET).encode()).hexdigest()


def verify_user(username, password, stored_hash):
    return hash_password(password) == stored_hash
