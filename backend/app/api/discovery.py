"""Discovery API endpoints."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter

from app.models.discovery import (
    Discovery,
    DiscoveryMetadata,
    DiscoveryResponse,
)
from app.models.common import StepRunResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/discovery", tags=["discovery"])

# Path to discovery data file
DISCOVERY_FILE = Path(__file__).parent.parent.parent.parent / "discovery" / "discovered_sites.json"


def _load_discovery_data() -> DiscoveryResponse:
    """Load discovery data from file."""
    if not DISCOVERY_FILE.exists():
        logger.info(f"Discovery file not found: {DISCOVERY_FILE}")
        return DiscoveryResponse(
            metadata=DiscoveryMetadata(
                generated_at=datetime.now(timezone.utc).isoformat(),
                total_niches=0,
                total_urls=0,
            ),
            discoveries=[],
        )

    try:
        with open(DISCOVERY_FILE, "r") as f:
            data = json.load(f)

        # Parse discoveries from file
        discoveries = []
        for d in data.get("discoveries", []):
            discoveries.append(Discovery(
                niche=d.get("niche", ""),
                discovered_at=d.get("discovered_at", datetime.now(timezone.utc).isoformat()),
                total_urls=d.get("total_urls", len(d.get("urls", []))),
                urls=d.get("urls", []),
                source=d.get("source", "database"),
            ))

        metadata = data.get("metadata", {})
        return DiscoveryResponse(
            metadata=DiscoveryMetadata(
                generated_at=metadata.get("generated_at", datetime.now(timezone.utc).isoformat()),
                total_niches=metadata.get("total_niches", len(discoveries)),
                total_urls=metadata.get("total_urls", sum(d.total_urls for d in discoveries)),
            ),
            discoveries=discoveries,
        )
    except Exception as e:
        logger.error(f"Failed to load discovery data: {e}")
        return DiscoveryResponse(
            metadata=DiscoveryMetadata(
                generated_at=datetime.now(timezone.utc).isoformat(),
                total_niches=0,
                total_urls=0,
            ),
            discoveries=[],
        )


@router.get("", response_model=DiscoveryResponse)
async def get_discovery() -> DiscoveryResponse:
    """Get discovered sites data."""
    return _load_discovery_data()


@router.post("/run", response_model=StepRunResponse)
async def run_discovery() -> StepRunResponse:
    """Run the discovery step."""
    # In a real implementation, this would trigger the discovery process
    return StepRunResponse(
        success=True,
        message="Discovery step started",
    )
