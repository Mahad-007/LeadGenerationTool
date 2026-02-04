"""Verification API endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter

from app.models.verification import (
    VerificationMetadata,
    VerificationResponse,
)
from app.models.common import StepRunResponse

router = APIRouter(prefix="/api/verification", tags=["verification"])


# In-memory storage (will be replaced with file-based storage)
_verification_data: VerificationResponse | None = None


def _get_verification_data() -> VerificationResponse:
    """Get current verification data."""
    global _verification_data
    if _verification_data is None:
        _verification_data = VerificationResponse(
            metadata=VerificationMetadata(
                generated_at=datetime.now(timezone.utc).isoformat(),
                total_verified=0,
                shopify_count=0,
                non_shopify_count=0,
            ),
            shopify_sites=[],
            verification_log=[],
        )
    return _verification_data


@router.get("", response_model=VerificationResponse)
async def get_verification() -> VerificationResponse:
    """Get verification results."""
    return _get_verification_data()


@router.post("/run", response_model=StepRunResponse)
async def run_verification() -> StepRunResponse:
    """Run the verification step."""
    return StepRunResponse(
        success=True,
        message="Verification step started",
    )
