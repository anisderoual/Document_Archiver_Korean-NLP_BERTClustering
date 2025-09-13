import json
from typing import Dict, List
from ..config import Config
from ..processors.document_processor import DocumentProcessor
from ..nlp.semantic_analyzer import SemanticAnalyzer
from ..extraction.content_extractor import ContentExtractor
from ..storage.secure_storage import SecureStorage


class DocumentArchivingSystem:
    """Main orchestrator of the pipeline."""

    def __init__(self, config: Config, variable_mappings: Dict[str, List[str]]):
        self.config = config
        self.processor = DocumentProcessor()
        self.analyzer = SemanticAnalyzer(
            model_name=config.model_name,
            batch_size=config.batch_size,
            max_length=config.max_length,
            similarity_threshold=config.similarity_threshold
        )
        self.extractor = ContentExtractor(variable_mappings)
        self.storage = SecureStorage(config.db_path, config.encryption_key)

    def process_document(self, file_path: str) -> Dict:
        # 1) Extract & preprocess
        text = self.processor.extract_text(file_path)
        sentences = self.processor.preprocess(text)

        # 2) Key phrases (toy example: first N non-trivial sentences)
        key_phrases = self._extract_key_phrases(sentences)

        if not key_phrases:
            return {"file_path": file_path, "error": "No key phrases found"}

        # 3) Embeddings
        embeddings = self.analyzer.get_embeddings(key_phrases)

        # 4) Clustering
        clusters = self.analyzer.cluster_terms(key_phrases, embeddings)

        # 5) Variable extraction
        extracted_vars = self.extractor.extract_variables(text, clusters)

        result = {
            "file_path": file_path,
            "extracted_variables": extracted_vars,
            "clusters": {k: v for k, v in clusters.items()}
        }

        # 6) Persist
        self.storage.save(file_path, result)
        return result

    def process_batch(self, file_paths: List[str]) -> Dict:
        results = []
        success = 0
        for p in file_paths:
            try:
                r = self.process_document(p)
                results.append(r)
                if "error" not in r:
                    success += 1
            except Exception as e:
                results.append({"file_path": p, "error": str(e)})
        return {
            "total": len(file_paths),
            "success": success,
            "failed": len(file_paths) - success,
            "results": results
        }

    def _extract_key_phrases(self, sentences: List[str], limit: int = 50) -> List[str]:
        phrases = []
        for s in sentences[:limit]:
            if len(s) > 10:
                phrases.append(s)
        return phrases
