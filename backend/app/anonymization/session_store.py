"""
Encrypted Session Pseudonym Lookup Store
Implements AES-authenticated Fernet encryption with TTL expiration (PIIShield_Spec_v2.md §6).
Key is kept separated from persisted lookup records.
"""

import os
from typing import Optional, Dict
from datetime import datetime, timezone
from cryptography.fernet import Fernet


class EncryptedSessionRecord:
    def __init__(self, token: str, entity_type: str, encrypted_value: bytes, expires_at: datetime):
        self.token = token
        self.entity_type = entity_type
        self.encrypted_value = encrypted_value
        self.expires_at = expires_at


class EncryptedSessionStore:
    """
    Isolated vault managing encrypted raw PII values for active sessions.
    Strictly zero unencrypted PII at rest.
    """

    def __init__(self, encryption_key: Optional[bytes] = None):
        if encryption_key is None:
            key_str = os.getenv("PIISHIELD_VAULT_KEY")
            if key_str:
                self.encryption_key = key_str.encode()
            else:
                self.encryption_key = Fernet.generate_key()
        else:
            self.encryption_key = encryption_key

        self.cipher = Fernet(self.encryption_key)
        # In-memory session store (keyed by (session_id, token))
        self._store: Dict[str, Dict[str, EncryptedSessionRecord]] = {}

    def store_mapping(
        self,
        session_id: str,
        token: str,
        entity_type: str,
        raw_value: str,
        expires_at: datetime,
    ) -> None:
        """
        Encrypts raw PII and stores in session lookup.
        Follows PIIShield_Spec_v2.md §6.
        """
        if not session_id or not token or not raw_value:
            raise ValueError("Invalid parameters for session store mapping.")

        # Authenticated encryption (Fernet AES-CBC + HMAC)
        encrypted_val = self.cipher.encrypt(raw_value.encode("utf-8"))

        record = EncryptedSessionRecord(
            token=token,
            entity_type=entity_type,
            encrypted_value=encrypted_val,
            expires_at=expires_at,
        )

        if session_id not in self._store:
            self._store[session_id] = {}

        self._store[session_id][token] = record

    def retrieve_raw_value(self, session_id: str, token: str) -> Optional[str]:
        """
        Retrieves and decrypts raw PII value if token exists and session is active.
        Fails closed (returns None) if expired or lookup fails (PIIShield_Spec_v2.md §2, §26.3).
        """
        session_records = self._store.get(session_id)
        if not session_records:
            return None

        record = session_records.get(token)
        if not record:
            return None

        # Check TTL expiration
        now = datetime.now(timezone.utc)
        record_exp = record.expires_at
        if record_exp.tzinfo is None:
            record_exp = record_exp.replace(tzinfo=timezone.utc)

        if now > record_exp:
            # Expired: delete and fail closed
            del session_records[token]
            return None

        try:
            decrypted_bytes = self.cipher.decrypt(record.encrypted_value)
            return decrypted_bytes.decode("utf-8")
        except Exception:
            # Fail closed on decryption failure
            return None

    def purge_expired_sessions(self) -> int:
        """Purges all expired sessions from memory."""
        now = datetime.now(timezone.utc)
        purged_count = 0
        for session_id in list(self._store.keys()):
            tokens = self._store[session_id]
            for token in list(tokens.keys()):
                exp = tokens[token].expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if now > exp:
                    del tokens[token]
                    purged_count += 1
            if not tokens:
                del self._store[session_id]
        return purged_count
