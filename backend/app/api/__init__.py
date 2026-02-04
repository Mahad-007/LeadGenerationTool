"""API routers for Shopify UI Audit."""

from .pipeline import router as pipeline_router
from .discovery import router as discovery_router
from .verification import router as verification_router
from .audit import router as audit_router
from .outreach import router as outreach_router

__all__ = [
    "pipeline_router",
    "discovery_router",
    "verification_router",
    "audit_router",
    "outreach_router",
]
