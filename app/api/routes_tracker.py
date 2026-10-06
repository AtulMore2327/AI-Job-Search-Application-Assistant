"""
API routes for Application Tracker, Status Transitions, and History.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query

from app.models.tracker import (
    TrackedApplication,
    SaveApplicationRequest,
    UpdateStatusRequest,
    TrackerStats
)
from app.database.repositories import ApplicationRepository
from app.utils.logging import get_logger

logger = get_logger("routes_tracker")

router = APIRouter(prefix="/tracker", tags=["Application Tracker"])


@router.post("/applications", response_model=TrackedApplication, status_code=status.HTTP_201_CREATED, summary="Save application to tracker")
async def save_application_endpoint(payload: SaveApplicationRequest):
    """
    Save an ApplicationPackage to the database tracker with an initial status (e.g. SAVED, APPLIED).
    """
    try:
        repo = ApplicationRepository()
        return repo.save_application(
            package=payload.package,
            status=payload.status,
            notes=payload.notes or "",
            applied_date=payload.applied_date
        )
    except Exception as e:
        logger.error(f"Failed to save application to tracker: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save application: {str(e)}"
        )


@router.get("/applications", response_model=List[TrackedApplication], summary="List tracked applications")
async def list_applications_endpoint(
    status_filter: Optional[str] = Query(default=None, description="Optional status filter (e.g. SAVED, APPLIED, INTERVIEWING)")
):
    """
    List all tracked applications ordered by most recently updated, with optional status filtering.
    """
    try:
        repo = ApplicationRepository()
        return repo.list_applications(status_filter=status_filter)
    except Exception as e:
        logger.error(f"Failed to list tracked applications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve applications: {str(e)}"
        )


@router.get("/applications/stats", response_model=TrackerStats, summary="Get application tracker summary statistics")
async def get_tracker_stats_endpoint():
    """
    Get application tracking summary statistics (total, count by status).
    """
    try:
        repo = ApplicationRepository()
        return repo.get_stats()
    except Exception as e:
        logger.error(f"Failed to get tracker stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stats: {str(e)}"
        )


@router.get("/applications/{application_id}", response_model=TrackedApplication, summary="Get application details by ID")
async def get_application_endpoint(application_id: str):
    """
    Retrieve single tracked application by application_id.
    """
    try:
        repo = ApplicationRepository()
        app_rec = repo.get_application(application_id)
        if not app_rec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application '{application_id}' not found."
            )
        return app_rec
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve application '{application_id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving application: {str(e)}"
        )


@router.patch("/applications/{application_id}/status", response_model=TrackedApplication, summary="Update application status or notes")
async def update_application_status_endpoint(application_id: str, payload: UpdateStatusRequest):
    """
    Update application tracking status (e.g. SAVED -> APPLIED -> INTERVIEWING), notes, or applied date.
    """
    try:
        repo = ApplicationRepository()
        updated = repo.update_status(
            application_id=application_id,
            status=payload.status,
            notes=payload.notes,
            applied_date=payload.applied_date
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application '{application_id}' not found."
            )
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update application status: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update status: {str(e)}"
        )


@router.delete("/applications/{application_id}", summary="Delete tracked application")
async def delete_application_endpoint(application_id: str):
    """
    Delete an application record from tracker.
    """
    try:
        repo = ApplicationRepository()
        deleted = repo.delete_application(application_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application '{application_id}' not found."
            )
        return {"status": "success", "message": f"Application '{application_id}' deleted."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete application: {str(e)}"
        )
