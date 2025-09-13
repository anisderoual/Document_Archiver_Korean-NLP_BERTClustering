from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """System configuration."""
    model_name: str = "monologg/kobert"
    similarity_threshold: float = 0.8
    batch_size: int = 32
    max_length: int = 512
    db_path: str = "archive.db"
    encryption_key: Optional[bytes] = None
