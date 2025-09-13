import json
import sqlite3
import hashlib
from typing import Optional, Dict
from cryptography.fernet import Fernet


class SecureStorage:
    """Encrypted SQLite storage using Fernet (AES)."""

    def __init__(self, db_path: str, encryption_key: Optional[bytes] = None):
        self.db_path = db_path
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS archives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_hash TEXT UNIQUE,
                encrypted_data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.commit()
        conn.close()

    def save(self, document_id: str, data: Dict) -> bool:
        try:
            payload = json.dumps(data, ensure_ascii=False)
            encrypted = self.cipher.encrypt(payload.encode("utf-8"))

            doc_hash = hashlib.sha256(document_id.encode()).hexdigest()

            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO archives (document_hash, encrypted_data) VALUES (?, ?)",
                (doc_hash, encrypted.decode("utf-8")),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[SecureStorage] Save error: {e}")
            return False

    def load(self, document_id: str) -> Optional[Dict]:
        try:
            doc_hash = hashlib.sha256(document_id.encode()).hexdigest()
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute(
                "SELECT encrypted_data FROM archives WHERE document_hash = ?",
                (doc_hash,),
            )
            row = cur.fetchone()
            conn.close()
            if not row:
                return None
            decrypted = self.cipher.decrypt(row[0].encode("utf-8"))
            return json.loads(decrypted.decode("utf-8"))
        except Exception as e:
            print(f"[SecureStorage] Load error: {e}")
            return None
