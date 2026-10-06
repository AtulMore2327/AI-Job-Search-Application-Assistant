from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Optional
from app.database.repositories import DatabaseRepository

router = APIRouter(prefix="/applications", tags=["Applications & Tracker"])

@router.get("", response_model=List[Dict])
def get_all_applications():
    return DatabaseRepository.get_all_applications()

@router.patch("/{application_id}")
def update_application_status(
    application_id: str,
    status: str = Body(..., embed=True),
    notes: Optional[str] = Body(None, embed=True)
):
    try:
        DatabaseRepository.update_application_status(application_id, status, notes)
        return {"status": "success", "message": f"Updated application {application_id} to status '{status}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
