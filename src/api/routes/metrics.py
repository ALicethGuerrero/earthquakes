from fastapi import APIRouter, HTTPException, Query, Request
from src.metadata.schemas import MetricResponse, serialize_document

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_model=list[MetricResponse])
def list_metrics(request: Request, window: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}$")):
    filters = {"window": window} if window else {}
    database = request.app.state.database
    if database is None:
        raise HTTPException(status_code=503, detail="MongoDB no disponible")
    cursor = database.metrics.find(filters).sort("window", -1)
    return [serialize_document(document) for document in cursor]
