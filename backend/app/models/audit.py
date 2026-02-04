"""Audit models for API responses."""

from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class Viewport(BaseModel):
    """Browser viewport dimensions."""
    model_config = ConfigDict(extra='ignore')
    width: int = Field(gt=0, description="Viewport width in pixels")
    height: int = Field(gt=0, description="Viewport height in pixels")


class PerformanceMetrics(BaseModel):
    """Web performance metrics."""
    model_config = ConfigDict(extra='ignore')
    lcp: Optional[float] = Field(default=None, description="Largest Contentful Paint in ms")
    fcp: Optional[float] = Field(default=None, description="First Contentful Paint in ms")
    dom_content_loaded: Optional[float] = Field(
        default=None, description="DOM Content Loaded time in ms"
    )
    load_complete: Optional[float] = Field(default=None, description="Load Complete time in ms")
    ttfb: Optional[float] = Field(default=None, description="Time to First Byte in ms")


class ConsoleErrorLocation(BaseModel):
    """Location information for a console error."""
    model_config = ConfigDict(extra='ignore')
    url: Optional[str] = Field(default=None, description="Source URL")
    lineNumber: Optional[int] = Field(default=None, description="Line number")
    columnNumber: Optional[int] = Field(default=None, description="Column number")


class ConsoleError(BaseModel):
    """A browser console error."""
    model_config = ConfigDict(extra='ignore')
    type: str = Field(default="error", description="Error type")
    text: str = Field(default="", description="Error message")
    location: Optional[ConsoleErrorLocation] = Field(
        default=None, description="Error location"
    )


class CTA(BaseModel):
    """Call-to-action element."""
    model_config = ConfigDict(extra='ignore')
    text: str = Field(default="", description="CTA text content")
    href: Optional[str] = Field(default=None, description="CTA link href")
    position: Optional[str] = Field(default=None, description="Position relative to fold")
    # Additional fields from actual audit data
    top: Optional[float] = Field(default=None, description="Top position in pixels")
    visible: Optional[bool] = Field(default=None, description="Whether CTA is visible")
    tagName: Optional[str] = Field(default=None, description="HTML tag name")


class HeroInfo(BaseModel):
    """Hero section information."""
    model_config = ConfigDict(extra='ignore')
    height: float = Field(ge=0, description="Hero section height in pixels")
    hasImage: bool = Field(default=False, description="Whether hero has an image")


class DomInfo(BaseModel):
    """DOM analysis information."""
    model_config = ConfigDict(extra='ignore')
    title: Optional[str] = Field(default=None, description="Page title")
    h1: Optional[str] = Field(default=None, description="First H1 text")
    ctas: list[CTA] = Field(default_factory=list, description="Call-to-action elements")
    ctasAboveFold: int = Field(default=0, ge=0, description="Number of CTAs above the fold")
    ctasBelowFold: int = Field(default=0, ge=0, description="Number of CTAs below the fold")
    heroInfo: Optional[HeroInfo] = Field(default=None, description="Hero section info")
    brokenImages: list[str] = Field(default_factory=list, description="Broken image URLs")
    internalLinksCount: int = Field(default=0, ge=0, description="Count of internal links")
    viewportHeight: int = Field(default=900, gt=0, description="Viewport height used")
    pageHeight: int = Field(default=900, gt=0, description="Total page height")
    foldLine: int = Field(default=900, gt=0, description="Y position of the fold line")


class LinkIssue(BaseModel):
    """A link issue found during audit."""
    model_config = ConfigDict(extra='ignore')
    url: str = Field(default="", description="Link URL")
    status_code: Optional[int] = Field(default=None, description="HTTP status code")
    issue_type: str = Field(default="", description="Type of issue (broken, redirect, etc.)")
    text: Optional[str] = Field(default=None, description="Link text")


class ViewportAudit(BaseModel):
    """Audit results for a specific viewport."""
    model_config = ConfigDict(extra='ignore')
    viewport_type: Literal["desktop", "mobile"] = Field(description="Viewport type")
    viewport: Viewport = Field(description="Viewport dimensions")
    screenshot_path: str = Field(description="Path to screenshot file")
    console_errors: list[ConsoleError] = Field(
        default_factory=list, description="Console errors captured"
    )
    performance_metrics: PerformanceMetrics = Field(
        default_factory=PerformanceMetrics, description="Performance metrics"
    )
    dom_info: Optional[DomInfo] = Field(default=None, description="DOM analysis information")
    link_issues: list[LinkIssue] = Field(
        default_factory=list, description="Link issues found"
    )
    error: Optional[str] = Field(default=None, description="Error message if audit failed")


class SiteAudit(BaseModel):
    """Complete audit results for a site."""
    model_config = ConfigDict(extra='ignore')
    url: str = Field(description="Site URL")
    audited_at: str = Field(description="ISO timestamp of audit")
    desktop: Optional[ViewportAudit] = Field(default=None, description="Desktop viewport audit")
    mobile: Optional[ViewportAudit] = Field(default=None, description="Mobile viewport audit")
    error: Optional[str] = Field(default=None, description="Error message if site audit failed")


class AuditMetadata(BaseModel):
    """Metadata about the audit process."""
    generated_at: str = Field(description="ISO timestamp of generation")
    total_sites: int = Field(ge=0, description="Total sites audited")
    successful: int = Field(ge=0, description="Successful audits")
    failed: int = Field(ge=0, description="Failed audits")


class AuditResponse(BaseModel):
    """Response from the audit endpoint."""
    metadata: AuditMetadata = Field(description="Audit process metadata")
    audits: list[SiteAudit] = Field(default_factory=list, description="Site audit results")
