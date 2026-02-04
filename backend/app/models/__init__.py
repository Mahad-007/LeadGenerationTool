"""Pydantic models for Shopify UI Audit API."""

from .pipeline import (
    PipelineStatus,
    PipelineStep,
    StepState,
    PipelineState,
    PipelineRunResponse,
    PipelineStopResponse,
)
from .discovery import (
    SearchMetadata,
    Discovery,
    DiscoveryMetadata,
    DiscoveryResponse,
)
from .verification import (
    ShopifySite,
    VerificationMetadata,
    VerificationResponse,
)
from .audit import (
    Viewport,
    PerformanceMetrics,
    ConsoleErrorLocation,
    ConsoleError,
    CTA,
    HeroInfo,
    DomInfo,
    LinkIssue,
    ViewportAudit,
    SiteAudit,
    AuditMetadata,
    AuditResponse,
)
from .outreach import (
    IssueReference,
    SocialLinks,
    EmailDraft,
    OutreachMetadata,
    OutreachResponse,
    EmailDraftUpdate,
)

__all__ = [
    # Pipeline
    "PipelineStatus",
    "PipelineStep",
    "StepState",
    "PipelineState",
    "PipelineRunResponse",
    "PipelineStopResponse",
    # Discovery
    "SearchMetadata",
    "Discovery",
    "DiscoveryMetadata",
    "DiscoveryResponse",
    # Verification
    "ShopifySite",
    "VerificationMetadata",
    "VerificationResponse",
    # Audit
    "Viewport",
    "PerformanceMetrics",
    "ConsoleErrorLocation",
    "ConsoleError",
    "CTA",
    "HeroInfo",
    "DomInfo",
    "LinkIssue",
    "ViewportAudit",
    "SiteAudit",
    "AuditMetadata",
    "AuditResponse",
    # Outreach
    "IssueReference",
    "SocialLinks",
    "EmailDraft",
    "OutreachMetadata",
    "OutreachResponse",
    "EmailDraftUpdate",
]
