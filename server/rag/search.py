import os
from openai import OpenAI
from rag.ingest import get_chroma_collection


def semantic_search(query: str, n_results: int = 5, openai_client=None, chroma_client=None):
    if openai_client is None:
        openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=[query],
    )
    query_embedding = response.data[0].embedding

    collection = get_chroma_collection(chroma_client)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    return [
        {"text": doc, "metadata": meta, "distance": dist}
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]
