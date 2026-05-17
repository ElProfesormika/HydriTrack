import os
import secrets

from fastapi import Header, HTTPException

ADMIN_KEY = os.environ.get("HYDROTRACK_ADMIN_KEY", "hydrotrack-admin-dev")
ADMIN_USERNAME = os.environ.get("HYDROTRACK_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("HYDROTRACK_ADMIN_PASSWORD", "hydrotrack-admin-dev")


def verify_admin_credentials(username: str, password: str) -> bool:
    user_ok = secrets.compare_digest(username.strip(), ADMIN_USERNAME)
    pass_ok = secrets.compare_digest(password, ADMIN_PASSWORD)
    return user_ok and pass_ok


def verify_admin_key(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")) -> str:
    if not x_admin_key or not secrets.compare_digest(x_admin_key, ADMIN_KEY):
        raise HTTPException(status_code=401, detail="Session invalide — reconnectez-vous")
    return x_admin_key
