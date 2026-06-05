import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../server"))

import pytest
from unittest.mock import MagicMock, patch


def _mock_collection(docs, metas, dists):
    col = MagicMock()
    col.query.return_value = {
        "documents": [docs],
        "metadatas": [metas],
        "distances": [dists],
    }
    return col


def _mock_openai(vector):
    client = MagicMock()
    emb = MagicMock()
    emb.embedding = vector
    client.embeddings.create.return_value = MagicMock(data=[emb])
    return client


def test_search_returns_results():
    from rag.search import semantic_search

    docs = ["Fed raised rates in 2024", "Market volatility elevated"]
    metas = [{"source": "fed.pdf", "chunk": 0}, {"source": "fed.pdf", "chunk": 1}]
    dists = [0.12, 0.25]

    with patch("rag.search.get_chroma_collection", return_value=_mock_collection(docs, metas, dists)):
        results = semantic_search("interest rates", n_results=2, openai_client=_mock_openai([0.1] * 1536))

    assert len(results) == 2
    assert results[0]["text"] == "Fed raised rates in 2024"
    assert results[1]["distance"] == pytest.approx(0.25)


def test_search_metadata_fields_present():
    from rag.search import semantic_search

    docs = ["BIS report on digital money and bigtech credit"]
    metas = [{"source": "bis_bigtech.pdf", "chunk": 5}]
    dists = [0.05]

    with patch("rag.search.get_chroma_collection", return_value=_mock_collection(docs, metas, dists)):
        results = semantic_search("digital money", n_results=1, openai_client=_mock_openai([0.0] * 1536))

    assert "metadata" in results[0]
    assert results[0]["metadata"]["source"] == "bis_bigtech.pdf"
    assert results[0]["metadata"]["chunk"] == 5
    assert "text" in results[0]
    assert "distance" in results[0]


def test_search_n_results_forwarded_to_collection():
    from rag.search import semantic_search

    docs = [f"chunk {i}" for i in range(4)]
    metas = [{"source": f"doc{i}.pdf", "chunk": i} for i in range(4)]
    dists = [0.1 * i for i in range(4)]

    mock_col = _mock_collection(docs, metas, dists)
    with patch("rag.search.get_chroma_collection", return_value=mock_col):
        results = semantic_search("portfolio risk", n_results=4, openai_client=_mock_openai([0.5] * 1536))

    call_kwargs = mock_col.query.call_args.kwargs
    assert call_kwargs["n_results"] == 4
    assert len(results) == 4
