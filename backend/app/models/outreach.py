"""Outreach models for API responses."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class IssueReference(BaseModel):
    """Reference to an issue found during audit."""
    title: str = Field(description="Issue title")
    category: str = Field(description="Issue category")
    severity: Literal["high", "medium", "low"] = Field(description="Issue severity")


class SocialLinks(BaseModel):
    """Social media links for a store."""
    instagram: Optional[str] = Field(default=None, description="Instagram URL")
    facebook: Optional[str] = Field(default=None, description="Facebook URL")
    twitter: Optional[str] = Field(default=None, description="Twitter URL")
    linkedin: Optional[str] = Field(default=None, description="LinkedIn URL")
    tiktok: Optional[str] = Field(default=None, description="TikTok URL")


class EmailDraft(BaseModel):
    """An email draft for outreach."""
    store_url: str = Field(description="Store URL")
    to_emails: list[str] = Field(default_factory=list, description="Recipient email addresses")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body text")
    issue_referenced: IssueReference = Field(description="The issue being referenced")
    social: SocialLinks = Field(default_factory=SocialLinks, description="Social media links")
    status: Literal["draft", "sent", "replied"] = Field(
        default="draft", description="Email status"
    )
    created_at: str = Field(description="ISO timestamp of creation")
    updated_at: Optional[str] = Field(default=None, description="ISO timestamp of last update")


class OutreachMetadata(BaseModel):
    """Metadata about the outreach generation."""
    generated_at: str = Field(description="ISO timestamp of generation")
    total_drafts: int = Field(ge=0, description="Total email drafts generated")
    with_emails: int = Field(ge=0, description="Drafts with email addresses")
    without_emails: int = Field(ge=0, description="Drafts without email addresses")


class OutreachResponse(BaseModel):
    """Response from the outreach endpoint."""
    metadata: OutreachMetadata = Field(description="Outreach generation metadata")
    drafts: list[EmailDraft] = Field(default_factory=list, description="Email drafts")


class EmailDraftUpdate(BaseModel):
    """Request body for updating an email draft."""
    subject: Optional[str] = Field(default=None, description="Updated subject line")
    body: Optional[str] = Field(default=None, description="Updated body text")
    status: Optional[Literal["draft", "sent", "replied"]] = Field(
        default=None, description="Updated status"
    )
