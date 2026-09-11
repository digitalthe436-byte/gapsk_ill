"""Vector Embeddings & Cosine Similarity Matching Engine.

Converts resume and job description text into TF-IDF vector representations
and calculates cosine similarity to quantify mathematical semantic alignment.
Supports Scikit-Learn TfidfVectorizer with a robust NumPy fallback.
"""

import math
import re
from typing import Dict, List, Tuple, Any
import numpy as np

from backend.parsers.text_cleaner import clean_text, STOP_WORDS


def tokenize_text(text: str) -> List[str]:
    """Tokenize text into lowercased alphanumeric tokens, stripping stop words."""
    raw_tokens = re.findall(r"\b[a-zA-Z0-9_+#.-]{2,}\b", text.lower())
    return [t for t in raw_tokens if t not in STOP_WORDS]


def compute_tf_idf_numpy(docs: List[str]) -> Tuple[np.ndarray, List[str]]:
    """Compute TF-IDF matrix using pure NumPy.

    Args:
        docs: List of text documents.

    Returns:
        (tfidf_matrix as ndarray, vocabulary as list of terms)
    """
    tokenized_docs = [tokenize_text(doc) for doc in docs]
    n_docs = len(docs)

    # Build vocabulary
    vocab_set = set()
    for tokens in tokenized_docs:
        vocab_set.update(tokens)
    vocabulary = sorted(list(vocab_set))

    if not vocabulary:
        return np.zeros((n_docs, 1)), ["dummy"]

    vocab_idx = {term: idx for idx, term in enumerate(vocabulary)}
    n_terms = len(vocabulary)

    # Document frequency: number of docs containing each term
    df = np.zeros(n_terms)
    for tokens in tokenized_docs:
        unique_tokens = set(tokens)
        for t in unique_tokens:
            if t in vocab_idx:
                df[vocab_idx[t]] += 1

    # Smooth IDF: log((1 + n_docs) / (1 + df)) + 1
    idf = np.log((1 + n_docs) / (1 + df)) + 1.0

    # TF matrix and TF-IDF
    tfidf_matrix = np.zeros((n_docs, n_terms), dtype=np.float64)

    for doc_idx, tokens in enumerate(tokenized_docs):
        if not tokens:
            continue
        # Term counts
        term_counts = {}
        for t in tokens:
            term_counts[t] = term_counts.get(t, 0) + 1

        total_words = len(tokens)
        for term, count in term_counts.items():
            if term in vocab_idx:
                t_idx = vocab_idx[term]
                # Sublinear TF scaling: 1 + log(count)
                tf = 1.0 + np.log(count)
                tfidf_matrix[doc_idx, t_idx] = tf * idf[t_idx]

        # L2 normalize row
        norm = np.linalg.norm(tfidf_matrix[doc_idx])
        if norm > 0:
            tfidf_matrix[doc_idx] = tfidf_matrix[doc_idx] / norm

    return tfidf_matrix, vocabulary


def compute_vector_similarity(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """Calculate Cosine Similarity between Resume and Job Description.

    Args:
        resume_text: Extracted plain text of resume.
        jd_text: Extracted plain text of job description.

    Returns:
        Dict containing:
          - 'cosine_similarity': float (0.0 to 1.0)
          - 'match_percentage': float (0.0 to 100.0)
          - 'top_overlapping_terms': list of top contributing keywords
    """
    clean_resume = clean_text(resume_text)
    clean_jd = clean_text(jd_text)

    docs = [clean_resume, clean_jd]

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=5000
        )
        matrix = vectorizer.fit_transform(docs)
        sim_matrix = cosine_similarity(matrix[0:1], matrix[1:2])
        sim_score = float(sim_matrix[0][0])
        feature_names = vectorizer.get_feature_names_out()

        # Find top contributing features
        v0 = matrix[0].toarray()[0]
        v1 = matrix[1].toarray()[0]
        overlap = v0 * v1
        top_indices = np.argsort(overlap)[::-1]
        top_terms = [
            feature_names[i]
            for i in top_indices[:12]
            if overlap[i] > 0.001
        ]
    except Exception:
        # NumPy fallback
        tfidf_matrix, vocab = compute_tf_idf_numpy(docs)
        dot_product = np.dot(tfidf_matrix[0], tfidf_matrix[1])
        norm0 = np.linalg.norm(tfidf_matrix[0])
        norm1 = np.linalg.norm(tfidf_matrix[1])

        if norm0 > 0 and norm1 > 0:
            sim_score = float(dot_product / (norm0 * norm1))
        else:
            sim_score = 0.0

        overlap = tfidf_matrix[0] * tfidf_matrix[1]
        top_indices = np.argsort(overlap)[::-1]
        top_terms = [
            vocab[i]
            for i in top_indices[:12]
            if overlap[i] > 0.001
        ]

    # Bound similarity score cleanly between 0.0 and 1.0
    sim_score = max(0.0, min(1.0, sim_score))
    match_pct = round(sim_score * 100.0, 1)

    return {
        "cosine_similarity": round(sim_score, 4),
        "match_percentage": match_pct,
        "top_overlapping_terms": top_terms
    }
