from typing import List, Dict
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN


class SemanticAnalyzer:
    """BERT-based semantic embedding + clustering."""

    def __init__(self, model_name: str, batch_size: int = 32, max_length: int = 512, similarity_threshold: float = 0.8):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()
        self.batch_size = batch_size
        self.max_length = max_length
        self.similarity_threshold = similarity_threshold

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Encode texts to embeddings using the [CLS] token."""
        all_vecs = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            all_vecs.extend(self._encode_batch(batch))
        return np.array(all_vecs)

    def _encode_batch(self, texts: List[str]):
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        )
        with torch.no_grad():
            encoded = {k: v.to(self.device) for k, v in encoded.items()}
            outputs = self.model(**encoded)
            # CLS token embedding
            cls = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        return cls.tolist()

    def cluster_terms(self, terms: List[str], embeddings: np.ndarray) -> Dict[int, List[str]]:
        """Cluster terms by cosine similarity using DBSCAN."""
        sim = cosine_similarity(embeddings)
        clustering = DBSCAN(
            eps=1 - self.similarity_threshold,
            min_samples=1,
            metric="precomputed"
        ).fit(1 - sim)
        clusters = {}
        for idx, label in enumerate(clustering.labels_):
            clusters.setdefault(label, []).append(terms[idx])
        return clusters
