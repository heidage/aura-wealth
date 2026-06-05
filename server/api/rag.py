from fastapi import APIRouter, HTTPException, Query
from rag.search import semantic_search
from rag.ingest import ingest_documents

router = APIRouter()


@router.get("/search")
async def search_documents(
    q: str = Query(..., min_length=1),
    n: int = Query(5, ge=1, le=20),
):
    try:
        results = semantic_search(q, n_results=n)
        return {"query": q, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
async def trigger_ingest():
    try:
        total = ingest_documents()
        return {"status": "ok", "chunks_ingested": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
