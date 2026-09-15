"""
Policy document retrieval module for RetailIQ Assistant.
Indexes internal policy documentation (policy_docs.txt) using TF-IDF and Cosine Similarity.
Provides grounded section citations for customer returns, markdowns, inventory, and SOPs.
"""
from pathlib import Path
import re
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class PolicyRetriever:
    """Document retrieval index for internal retail policies and SOPs."""

    _instance: Optional["PolicyRetriever"] = None

    def __init__(self, doc_path: Optional[Path] = None):
        if doc_path is None:
            base_dir = Path(__file__).resolve().parents[2]
            # Primary path
            p1 = base_dir / "data" / "knowledge_base" / "policy_docs.txt"
            p2 = base_dir / "reference" / "policy_docs.txt"
            self.doc_path = p1 if p1.exists() else p2
        else:
            self.doc_path = Path(doc_path)

        self.chunks: List[Dict[str, str]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self._load_and_index()

    @classmethod
    def get_instance(cls) -> "PolicyRetriever":
        """Singleton accessor for policy retrieval index."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_and_index(self):
        """Loads policy_docs.txt and splits into structured sections."""
        if not self.doc_path.exists():
            raise FileNotFoundError(f"Policy document not found at {self.doc_path}")

        with open(self.doc_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        # Split by numbered section headings e.g. "1. INVENTORY POLICY", "2. MARKDOWN RULES"
        raw_sections = re.split(r"\n(?=\d+\.\s+[A-Z\s\(\)]+)", raw_text)

        self.chunks = []
        for sec in raw_sections:
            sec = sec.strip()
            if not sec:
                continue
            lines = sec.split("\n")
            heading_match = re.match(r"^\d+\.\s+([A-Z\s\(\)]+)", lines[0])
            section_title = heading_match.group(0).strip() if heading_match else lines[0][:40].strip()
            body = "\n".join(lines[1:]).strip() if len(lines) > 1 else sec

            self.chunks.append({
                "source": "policy_docs.txt",
                "section": section_title,
                "text": sec,
                "body": body
            })

        # Build TF-IDF search index
        corpus = [f"{c['section']} {c['body']}" for c in self.chunks]
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Searches policy documents using cosine similarity over TF-IDF representation."""
        if not self.chunks or self.vectorizer is None:
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        ranked_indices = similarities.argsort()[::-1]
        results = []

        for idx in ranked_indices[:top_k]:
            score = float(similarities[idx])
            # Minimum threshold
            if score > 0.04:
                chunk = self.chunks[idx]
                results.append({
                    "source": chunk["source"],
                    "section": chunk["section"],
                    "text": chunk["text"],
                    "score": round(score, 3)
                })

        return results
