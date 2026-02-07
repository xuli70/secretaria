import json

from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import GoogleToken


def _get_fernet() -> Fernet:
    key = settings.GOOGLE_TOKEN_ENCRYPTION_KEY
    if not key:
        raise ValueError("GOOGLE_TOKEN_ENCRYPTION_KEY not configured")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(token_data: dict) -> bytes:
    f = _get_fernet()
    return f.encrypt(json.dumps(token_data).encode())


def decrypt_token(encrypted: bytes) -> dict:
    f = _get_fernet()
    return json.loads(f.decrypt(encrypted).decode())


def get_stored_token(db: Session, user_id: int) -> dict | None:
    row = db.query(GoogleToken).filter(GoogleToken.user_id == user_id).first()
    if not row:
        return None
    return decrypt_token(row.encrypted_token)


def store_token(db: Session, user_id: int, token_data: dict, scopes: str):
    encrypted = encrypt_token(token_data)
    row = db.query(GoogleToken).filter(GoogleToken.user_id == user_id).first()
    if row:
        row.encrypted_token = encrypted
        row.scopes = scopes
    else:
        row = GoogleToken(
            user_id=user_id,
            encrypted_token=encrypted,
            scopes=scopes,
        )
        db.add(row)
    db.commit()


def delete_token(db: Session, user_id: int) -> bool:
    row = db.query(GoogleToken).filter(GoogleToken.user_id == user_id).first()
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True
