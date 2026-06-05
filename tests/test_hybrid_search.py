import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../server"))

import pytest
from unittest.mock import MagicMock, patch


def _sem_result(text, distance):
    return {"text": text, "metadata": {"source": "doc.pdf", "chunk": 0}, "distance": distance}


def _mock_semantic(results):
    return MagicMock(return_value=results)


def test_hybrid_adds_bm25_and_combined_scores():
    from rag.hybrid_search import hybrid_search

    candidates = [
        _sem_result("Federal Reserve raised interest rates in 2024", 0.1),
        _sem_result("Stock market volatility increased significantly", 0.3),
    ]
    with patch("rag.hybrid_search.semantic_search", return_value=candidates):
        results = hybrid_search("interest rates", n_results=2, openai_client=MagicMock())

    assert len(results) == 2
    for r in results:
        assert "bm25_score" in r
        assert "combined_score" in r
        assert 0.0 <= r["combined_score"] <= 1.0


def test_hybrid_boosts_keyword_match_over_distant_semantic():
    from rag.hybrid_search import hybrid_search

    # doc B has worse semantic (higher distance) but exact keyword match
    candidates = [
        _sem_result("Global equity markets rose broadly", 0.05),   # close semantic, no keyword
        _sem_result("inflation rate surged to record inflation levels", 0.4),  # far semantic, exact keyword
    ]
    with patch("rag.hybrid_search.semantic_search", return_value=candidates):
        results = hybrid_search("inflation rate", n_results=2, openai_client=MagicMock())

    # keyword-rich doc should have higher bm25_score
    keyword_result = next(r for r in results if "inflation" in r["text"])
    no_keyword_result = next(r for r in results if "inflation" not in r["text"])
    assert keyword_result["bm25_score"] > no_keyword_result["bm25_score"]


def test_hybrid_falls_back_gracefully_on_empty_candidates():
    from rag.hybrid_search import hybrid_search

    with patch("rag.hybrid_search.semantic_search", return_value=[]):
        results = hybrid_search("portfolio diversification", n_results=5, openai_client=MagicMock())

    assert results == []
