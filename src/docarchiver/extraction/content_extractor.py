import re
from typing import Dict, List, Optional


class ContentExtractor:
    """Map clustered terms to variable names and extract values from text."""

    def __init__(self, variable_mappings: Dict[str, List[str]]):
        # forward and reverse mappings
        self.variable_mappings = variable_mappings
        self.reverse_mapping = self._create_reverse_mapping(variable_mappings)

    def _create_reverse_mapping(self, mappings: Dict[str, List[str]]) -> Dict[str, str]:
        reverse = {}
        for var_name, keywords in mappings.items():
            for k in keywords:
                reverse[k] = var_name
        return reverse

    def extract_variables(self, text: str, clusters: Dict[int, List[str]]) -> Dict[str, object]:
        extracted = {}
        for _, terms in clusters.items():
            var_name = self._find_variable_name(terms)
            if var_name:
                value = self._extract_value(text, terms)
                if value is not None:
                    extracted[var_name] = value
        return extracted

    def _find_variable_name(self, terms: List[str]) -> Optional[str]:
        for t in terms:
            if t in self.reverse_mapping:
                return self.reverse_mapping[t]
        return None

    def _extract_value(self, text: str, terms: List[str]) -> Optional[object]:
        # simple regex-based numeric capture after any matching term
        for term in terms:
            if term in text:
                m = re.search(fr"{re.escape(term)}.*?(\d+)", text)
                if m:
                    try:
                        return int(m.group(1))
                    except Exception:
                        return m.group(1)
        return None
