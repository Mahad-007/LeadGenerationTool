"""Verification models for API responses."""

from typing import Optional
from pydantic import BaseModel, Field


class ShopifySite(BaseModel):
    """A verified Shopify site."""
    url: str = Field(description="Site URL")
    is_shopify: bool = Field(description="Whether the site is a Shopify store")
    confidence: float = Field(ge=0, le=1, description="Confidence score 0-1")
    signals_found: list[str] = Field(
        default_factory=list, description="Shopify detection signals found"
    )
    verified_at: str = Field(description="ISO timestamp of verification")
    error: Optional[str] = Field(default=None, description="Error message if verification failed")


class VerificationMetadata(BaseModel):
    """Metadata about the verification process."""
    generated_at: str = Field(description="ISO timestamp of generation")
    total_verified: int = Field(ge=0, description="Total sites verified")
    shopify_count: int = Field(ge=0, description="Number of confirmed Shopify sites")
    non_shopify_count: int = Field(ge=0, description="Number of non-Shopify sites")
    min_confidence_threshold: float = Field(
        ge=0, le=1, default=0.7, description="Minimum confidence threshold used"
    )


class VerificationResponse(BaseModel):
    """Response from the verification endpoint."""
    metadata: VerificationMetadata = Field(description="Verification process metadata")
    shopify_sites: list[ShopifySite] = Field(
        default_factory=list, description="Confirmed Shopify sites"
    )
    verification_log: list[ShopifySite] = Field(
        default_factory=list, description="All verification attempts"
    )
