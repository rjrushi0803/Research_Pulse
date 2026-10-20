"""Health endpoint used by tests, operators and deployment health checks."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "app_name": "Research_Pulse",
        "environment": "development",
    }
