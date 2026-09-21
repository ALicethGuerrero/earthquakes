from fastapi import APIRouter, Query, Request

from src.metadata.schemas import ReportResponse, serialize_document

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=list[ReportResponse])
def list_reports(request: Request, limit: int = Query(50, ge=1, le=200)):
    cursor = request.app.state.database.reports.find().sort("report_date", -1).limit(limit)
    return [serialize_document(document) for document in cursor]
