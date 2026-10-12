"""Health endpoint used by tests, operators and deployment health checks."""

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", summary="Check whether the API process is responsive")
def health_check() -> dict[str, str]:
    """Return a minimal status payload without disclosing secrets or infrastructure."""
    settings = get_settings()
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.app_env,
    }
