"""
Hybrid Document Retriever Module
Combines Semantic Search (TF-IDF + Latent Semantic Dense Vectors)
and Keyword Search (BM25Okapi) with Reciprocal Rank Fusion (RRF).
"""

import math
import re
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi


def tokenize(text: str) -> List[str]:
    """Clean and tokenize text for BM25 keyword matching."""
    text = text.lower()
    # Normalize punctuation but keep numbers, hyphens, percentages, and alphanumeric codes (e.g. CS101, 80%, 2024-2025)
    tokens = re.findall(r"\b[a-z0-9_%-]+\b", text)
    stopwords = {
        "a", "an", "the", "and", "or", "of", "to", "in", "for", "on", "with",
        "at", "by", "from", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "this", "that", "these", "those"
    }
    return [t for t in tokens if t not in stopwords and len(t) > 1]


class HybridRetriever:
    """Hybrid Retriever combining dense semantic vector similarity and sparse BM25 keyword matching."""

    def __init__(self, semantic_weight: float = 0.55, top_k: int = 5):
        self.semantic_weight = semantic_weight
        self.top_k = top_k
        self.chunks: List[Dict[str, Any]] = []
        self.bm25: Optional[BM25Okapi] = None
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.svd: Optional[TruncatedSVD] = None
        self.dense_embeddings: Optional[np.ndarray] = None
        self.is_indexed: bool = False

    def index_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """Build BM25 index and semantic embeddings for the given chunks."""
        self.chunks = chunks
        if not chunks:
            self.bm25 = None
            self.tfidf_vectorizer = None
            self.svd = None
            self.dense_embeddings = None
            self.is_indexed = False
            return

        corpus_texts = [f"{c.get('section_title', '')} {c.get('text', '')}" for c in chunks]

        # 1. Build BM25 Index
        tokenized_corpus = [tokenize(text) for text in corpus_texts]
        self.bm25 = BM25Okapi(tokenized_corpus)

        # 2. Build Semantic Embeddings via TF-IDF + Latent Semantic Analysis (Dense LSA)
        # Using sublinear tf and character n-grams allows matching typos & academic acronyms
        self.tfidf_vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            sublinear_tf=True,
            min_df=1,
            max_features=5000
        )
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus_texts)

        # If we have enough chunks, apply SVD for dense semantic embeddings (captures concept synonyms)
        n_features = tfidf_matrix.shape[1]
        n_samples = len(chunks)
        target_components = min(64, n_features - 1, n_samples - 1)

        if target_components > 2:
            self.svd = TruncatedSVD(n_components=target_components, random_state=42)
            self.dense_embeddings = self.svd.fit_transform(tfidf_matrix)
            # Normalize embeddings to unit vectors for cosine similarity
            norms = np.linalg.norm(self.dense_embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self.dense_embeddings = self.dense_embeddings / norms
        else:
            self.svd = None
            # Normalize raw tf-idf as dense matrix
            dense = tfidf_matrix.toarray()
            norms = np.linalg.norm(dense, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self.dense_embeddings = dense / norms

        self.is_indexed = True

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        doc_type_filter: Optional[str] = None,
        academic_year_filter: Optional[str] = None,
        threshold: float = 0.05
    ) -> List[Dict[str, Any]]:
        """Retrieve most relevant chunks using hybrid scoring (Semantic + BM25 + Reciprocal Rank Fusion)."""
        if not self.is_indexed or not self.chunks:
            return []

        k = top_k if top_k is not None else self.top_k
        n = len(self.chunks)

        # 1. Keyword Retrieval (BM25)
        query_tokens = tokenize(query)
        bm25_scores = np.zeros(n)
        if self.bm25 and query_tokens:
            raw_bm25 = self.bm25.get_scores(query_tokens)
            max_bm25 = np.max(raw_bm25) if len(raw_bm25) > 0 and np.max(raw_bm25) > 0 else 1.0
            bm25_scores = np.array(raw_bm25) / max_bm25

        # 2. Semantic Vector Retrieval (Cosine Similarity in LSA/TF-IDF space)
        semantic_scores = np.zeros(n)
        if self.tfidf_vectorizer is not None and self.dense_embeddings is not None:
            try:
                query_tfidf = self.tfidf_vectorizer.transform([query])
                if self.svd is not None:
                    query_dense = self.svd.transform(query_tfidf)
                else:
                    query_dense = query_tfidf.toarray()

                q_norm = np.linalg.norm(query_dense)
                if q_norm > 0:
                    query_dense = query_dense / q_norm
                    sims = cosine_similarity(query_dense, self.dense_embeddings)[0]
                    # Rescale [-1, 1] cosine similarity to [0, 1]
                    semantic_scores = np.clip((sims + 1.0) / 2.0, 0.0, 1.0)
            except Exception:
                semantic_scores = np.zeros(n)

        # 3. Reciprocal Rank Fusion (RRF) & Weighted Hybrid Combining
        # RRF formula: RRF_score = 1 / (60 + rank_bm25) + 1 / (60 + rank_semantic)
        bm25_ranks = np.argsort(-bm25_scores)
        semantic_ranks = np.argsort(-semantic_scores)

        rrf_scores = np.zeros(n)
        for rank, idx in enumerate(bm25_ranks):
            if bm25_scores[idx] > 0:
                rrf_scores[idx] += 1.0 / (60.0 + rank + 1)
        for rank, idx in enumerate(semantic_ranks):
            if semantic_scores[idx] > 0.1:
                rrf_scores[idx] += 1.0 / (60.0 + rank + 1)

        # Normalize RRF scores
        max_rrf = np.max(rrf_scores) if np.max(rrf_scores) > 0 else 1.0
        norm_rrf = rrf_scores / max_rrf

        # Combined Hybrid Score
        alpha = self.semantic_weight
        hybrid_scores = (
            0.5 * (alpha * semantic_scores + (1.0 - alpha) * bm25_scores)
            + 0.5 * norm_rrf
        )

        # Collect and filter results
        results = []
        for idx in range(n):
            chunk = self.chunks[idx].copy()
            score = float(hybrid_scores[idx])

            # Apply filters
            if doc_type_filter and doc_type_filter.lower() != "all":
                if chunk.get("doc_type", "").lower() != doc_type_filter.lower():
                    continue
            if academic_year_filter and academic_year_filter.lower() != "all":
                if chunk.get("academic_year", "").lower() != academic_year_filter.lower():
                    continue

            if score < threshold:
                continue

            # Identify matching query terms in text
            chunk_text_lower = chunk.get("text", "").lower()
            matched_terms = [t for t in query_tokens if t in chunk_text_lower]

            chunk["retrieval_metrics"] = {
                "hybrid_score": round(score, 4),
                "semantic_score": round(float(semantic_scores[idx]), 4),
                "bm25_score": round(float(bm25_scores[idx]), 4),
                "rrf_score": round(float(norm_rrf[idx]), 4),
                "matched_terms": matched_terms,
            }
            results.append(chunk)

        # Sort descending by hybrid_score
        results.sort(key=lambda x: x["retrieval_metrics"]["hybrid_score"], reverse=True)
        return results[:k]
