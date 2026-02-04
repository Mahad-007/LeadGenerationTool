"""Audit API endpoints."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.models.audit import (
    AuditMetadata,
    AuditResponse,
    SiteAudit,
)
from app.models.common import StepRunResponse
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["audit"])

# Path to audit results file
AUDIT_FILE = Path(__file__).parent.parent.parent.parent / "audits" / "audit_results.json"


def _transform_screenshot_path(path: str) -> str:
    """Transform filesystem path to API path."""
    if not path:
        return path
    # Extract just the filename from the full path
    filename = Path(path).name
    return f"/api/audit/screenshot/{filename}"


def _transform_viewport_data(viewport_data: dict) -> dict:
    """Transform viewport data to use API paths for screenshots."""
    if not viewport_data:
        return viewport_data
    transformed = viewport_data.copy()
    if "screenshot_path" in transformed:
        transformed["screenshot_path"] = _transform_screenshot_path(transformed["screenshot_path"])
    return transformed


def _load_audit_data() -> AuditResponse:
    """Load audit data from file."""
    if not AUDIT_FILE.exists():
        logger.info(f"Audit file not found: {AUDIT_FILE}")
        return AuditResponse(
            metadata=AuditMetadata(
                generated_at=datetime.now(timezone.utc).isoformat(),
                total_sites=0,
                successful=0,
                failed=0,
            ),
            audits=[],
        )

    try:
        with open(AUDIT_FILE, "r") as f:
            data = json.load(f)

        metadata = data.get("metadata", {})
        audits_raw = data.get("audits", [])

        # Transform and validate audits
        audits = []
        for audit in audits_raw:
            try:
                # Transform screenshot paths to API paths
                audit_copy = audit.copy()
                if audit_copy.get("desktop"):
                    audit_copy["desktop"] = _transform_viewport_data(audit_copy["desktop"])
                if audit_copy.get("mobile"):
                    audit_copy["mobile"] = _transform_viewport_data(audit_copy["mobile"])

                audits.append(SiteAudit.model_validate(audit_copy))
            except Exception as e:
                logger.warning(f"Failed to parse audit for {audit.get('url')}: {e}")
                # Create minimal audit entry on parse failure
                audits.append(SiteAudit(
                    url=audit.get("url", "unknown"),
                    audited_at=audit.get("audited_at", datetime.now(timezone.utc).isoformat()),
                    error=str(e),
                ))

        return AuditResponse(
            metadata=AuditMetadata(
                generated_at=metadata.get("generated_at", datetime.now(timezone.utc).isoformat()),
                total_sites=metadata.get("total_audited", len(audits)),
                successful=metadata.get("successful", 0),
                failed=metadata.get("failed", 0),
            ),
            audits=audits,
        )
    except Exception as e:
        logger.error(f"Failed to load audit data: {e}")
        return AuditResponse(
            metadata=AuditMetadata(
                generated_at=datetime.now(timezone.utc).isoformat(),
                total_sites=0,
                successful=0,
                failed=0,
            ),
            audits=[],
        )


@router.get("", response_model=AuditResponse)
async def get_audit() -> AuditResponse:
    """Get audit results."""
    return _load_audit_data()


@router.post("/run", response_model=StepRunResponse)
async def run_audit() -> StepRunResponse:
    """Run the audit step."""
    return StepRunResponse(
        success=True,
        message="Audit step started",
    )


ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


@router.get("/screenshot/{filename:path}")
async def get_screenshot(filename: str) -> FileResponse:
    """Get a screenshot image file."""
    # Validate file extension first
    file_ext = Path(filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=404, detail="Screenshot not found")

    # Construct the full path to the screenshot
    screenshots_dir = Path(__file__).parent.parent.parent.parent / "audits" / "screenshots"

    # Resolve paths for security check
    try:
        screenshots_dir_resolved = screenshots_dir.resolve()
        screenshot_path = (screenshots_dir / filename).resolve()

        # Security check: ensure path is within screenshots directory using is_relative_to
        if not screenshot_path.is_relative_to(screenshots_dir_resolved):
            raise HTTPException(status_code=404, detail="Screenshot not found")
    except (ValueError, OSError):
        raise HTTPException(status_code=404, detail="Screenshot not found")

    if not screenshot_path.exists() or not screenshot_path.is_file():
        raise HTTPException(status_code=404, detail="Screenshot not found")

    return FileResponse(
        path=screenshot_path,
        media_type="image/png",
        filename=screenshot_path.name,
    )
