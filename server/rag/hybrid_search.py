import math
import re
from collections import Counter
from rag.search import semantic_search


def _tokenize(text: str) -> list[str]:
    return re.findall(r'\b[a-z]+\b', text.lower())


def _bm25_scores(
    query_terms: list[str],
    tokenized_docs: list[list[str]],
    k1: float = 1.5,
    b: float = 0.75,
) -> list[float]:
    n = len(tokenized_docs)
    avg_dl = sum(len(t) for t in tokenized_docs) / max(n, 1)

    df: dict[str, int] = {}
    for tokens in tokenized_docs:
        for term in set(tokens):
            df[term] = df.get(term, 0) + 1

    scores = []
    for tokens in tokenized_docs:
        tf_map = Counter(tokens)
        dl = len(tokens)
        score = 0.0
        for term in query_terms:
            tf = tf_map.get(term, 0)
            if tf == 0:
                continue
            idf = math.log((n - df.get(term, 0) + 0.5) / (df.get(term, 0) + 0.5) + 1)
            tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / max(avg_dl, 1)))
            score += idf * tf_norm
        scores.append(score)
    return scores


def hybrid_search(
    query: str,
    n_results: int = 5,
    candidate_k: int = 20,
    openai_client=None,
    chroma_client=None,
) -> list[dict]:
    candidates = semantic_search(
        query,
        n_results=min(candidate_k, 100),
        openai_client=openai_client,
        chroma_client=chroma_client,
    )
    if not candidates:
        return []

    query_terms = _tokenize(query)
    if not query_terms:
        return [
            {**c, "bm25_score": 0.0, "combined_score": 1.0 - c["distance"]}
            for c in candidates[:n_results]
        ]

    tokenized_docs = [_tokenize(c["text"]) for c in candidates]
    bm25 = _bm25_scores(query_terms, tokenized_docs)

    max_bm25 = max(bm25) if max(bm25) > 0 else 1.0
    max_dist = max(c["distance"] for c in candidates) or 1.0

    scored = []
    for i, cand in enumerate(candidates):
        sem = 1.0 - cand["distance"] / max_dist
        bm = bm25[i] / max_bm25
        scored.append({
            **cand,
            "bm25_score": round(bm25[i], 4),
            "combined_score": round(0.5 * sem + 0.5 * bm, 4),
        })

    scored.sort(key=lambda x: x["combined_score"], reverse=True)
    return scored[:n_results]
