"""
Shared imports used across the project.

Keep this file lightweight: only include dependencies that are actually used.
"""

from __future__ import annotations

import os
import re
from typing import List, Optional

# Data handling
import numpy as np
import pandas as pd

# ML / similarity
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ModuleNotFoundError:
    class TfidfVectorizer:
        def __init__(
            self,
            stop_words: str | None = None,
            ngram_range: tuple[int, int] = (1, 1),
            min_df: int = 1,
            max_features: int | None = None,
        ):
            self.stop_words = stop_words
            self.ngram_range = ngram_range
            self.min_df = min_df
            self.max_features = max_features
            self.vocabulary_: dict[str, int] = {}
            self.idf_: np.ndarray = np.array([])

        def _tokens(self, text: object) -> list[str]:
            tokens = re.findall(r"[\w'-]+", str(text).lower(), flags=re.UNICODE)
            if self.stop_words == "english":
                stop = {"a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "of", "on", "or", "the", "to", "with"}
                tokens = [token for token in tokens if token not in stop]
            return tokens

        def _terms(self, text: object) -> list[str]:
            tokens = self._tokens(text)
            terms: list[str] = []
            min_n, max_n = self.ngram_range
            for n in range(min_n, max_n + 1):
                terms.extend(" ".join(tokens[i : i + n]) for i in range(0, max(len(tokens) - n + 1, 0)))
            return terms

        def fit_transform(self, docs: object) -> np.ndarray:
            doc_terms = [self._terms(doc) for doc in list(docs)]
            document_frequency: dict[str, int] = {}
            for terms in doc_terms:
                for term in set(terms):
                    document_frequency[term] = document_frequency.get(term, 0) + 1

            terms = [term for term, count in document_frequency.items() if count >= self.min_df]
            terms = sorted(terms, key=lambda term: (-document_frequency[term], term))
            if self.max_features is not None:
                terms = terms[: self.max_features]
            self.vocabulary_ = {term: index for index, term in enumerate(terms)}
            n_docs = len(doc_terms)
            self.idf_ = np.array([
                np.log((1 + n_docs) / (1 + document_frequency[term])) + 1 for term in terms
            ], dtype=np.float32)
            return self._matrix(doc_terms)

        def transform(self, docs: object) -> np.ndarray:
            return self._matrix([self._terms(doc) for doc in list(docs)])

        def _matrix(self, doc_terms: list[list[str]]) -> np.ndarray:
            matrix = np.zeros((len(doc_terms), len(self.vocabulary_)), dtype=np.float32)
            for row_index, terms in enumerate(doc_terms):
                if not terms:
                    continue
                counts: dict[int, int] = {}
                for term in terms:
                    col_index = self.vocabulary_.get(term)
                    if col_index is not None:
                        counts[col_index] = counts.get(col_index, 0) + 1
                for col_index, count in counts.items():
                    matrix[row_index, col_index] = count * self.idf_[col_index]

            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            return matrix / norms

    def cosine_similarity(x: object, y: object | None = None) -> np.ndarray:
        x_arr = np.asarray(x, dtype=float)
        y_arr = x_arr if y is None else np.asarray(y, dtype=float)
        x_norm = np.linalg.norm(x_arr, axis=1, keepdims=True)
        y_norm = np.linalg.norm(y_arr, axis=1, keepdims=True)
        x_norm[x_norm == 0] = 1.0
        y_norm[y_norm == 0] = 1.0
        return (x_arr / x_norm) @ (y_arr / y_norm).T
