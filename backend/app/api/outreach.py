"""Outreach API endpoints."""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote
from fastapi import APIRouter, HTTPException

from app.models.outreach import (
    OutreachMetadata,
    OutreachResponse,
    EmailDraft,
    EmailDraftUpdate,
    IssueReference,
    SocialLinks,
)
from app.models.common import StepRunResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/outreach", tags=["outreach"])

# Path to drafts summary file
DRAFTS_SUMMARY_FILE = Path(__file__).parent.parent.parent.parent / "outreach" / "drafts" / "drafts_summary.json"
CONTACTS_FILE = Path(__file__).parent.parent.parent.parent / "contacts" / "contacts.json"


def _parse_draft_file(filepath: str) -> dict:
    """Parse a draft .txt file to extract body and issue info."""
    try:
        with open(filepath, "r") as f:
            content = f.read()

        # Extract body (between BODY: and ISSUE REFERENCED:)
        body_match = re.search(r"BODY:\s*-+\s*\n\n(.*?)\n\n-+\s*\nISSUE REFERENCED:", content, re.DOTALL)
        body = body_match.group(1).strip() if body_match else ""

        # Extract issue category
        category_match = re.search(r"Category:\s*(\w+)", content)
        category = category_match.group(1) if category_match else "generic"

        # Extract issue severity
        severity_match = re.search(r"Severity:\s*(\w+)", content)
        severity = severity_match.group(1) if severity_match else "medium"

        # Extract issue title
        title_match = re.search(r"Title:\s*(.+?)(?:\n|$)", content)
        title = title_match.group(1).strip() if title_match else ""

        return {
            "body": body,
            "category": category,
            "severity": severity,
            "title": title,
        }
    except Exception as e:
        logger.error(f"Failed to parse draft file {filepath}: {e}")
        return {"body": "", "category": "generic", "severity": "medium", "title": ""}


def _load_contacts_by_url() -> dict:
    """Load contacts indexed by URL."""
    contacts_by_url = {}
    if CONTACTS_FILE.exists():
        try:
            with open(CONTACTS_FILE, "r") as f:
                data = json.load(f)
            for contact in data.get("contacts", []):
                url = contact.get("url")
                if url:
                    contacts_by_url[url] = contact
        except Exception as e:
            logger.error(f"Failed to load contacts: {e}")
    return contacts_by_url


def _load_outreach_data() -> OutreachResponse:
    """Load outreach data from files."""
    if not DRAFTS_SUMMARY_FILE.exists():
        logger.info(f"Drafts summary file not found: {DRAFTS_SUMMARY_FILE}")
        return OutreachResponse(
            metadata=OutreachMetadata(
                generated_at=datetime.now(timezone.utc).isoformat(),
                total_drafts=0,
                with_emails=0,
                without_emails=0,
            ),
            drafts=[],
        )

    try:
        with open(DRAFTS_SUMMARY_FILE, "r") as f:
            summary = json.load(f)

        contacts_by_url = _load_contacts_by_url()
        drafts = []
        with_emails = 0
        without_emails = 0

        for draft_info in summary.get("drafts", []):
            url = draft_info.get("url", "")
            draft_file = draft_info.get("file", "")

            # Parse the draft file for body and issue info
            parsed = _parse_draft_file(draft_file) if draft_file else {}

            # Get contact info
            contact = contacts_by_url.get(url, {})
            social = contact.get("social", {})

            # Filter out invalid emails (like the JS file references)
            to_emails = [e for e in draft_info.get("to_emails", []) if "@" in e and not e.endswith(".js") and not e.endswith(".css")]

            if to_emails:
                with_emails += 1
            else:
                without_emails += 1

            drafts.append(EmailDraft(
                store_url=url,
                to_emails=to_emails,
                subject=draft_info.get("subject", ""),
                body=parsed.get("body", ""),
                issue_referenced=IssueReference(
                    title=parsed.get("title", ""),
                    category=draft_info.get("issue_category", parsed.get("category", "generic")),
                    severity=parsed.get("severity", "medium"),
                ),
                social=SocialLinks(
                    instagram=social.get("instagram"),
                    facebook=social.get("facebook"),
                    twitter=social.get("twitter"),
                    linkedin=social.get("linkedin"),
                    tiktok=social.get("tiktok"),
                ),
                status="draft",
                created_at=summary.get("generated_at", datetime.now(timezone.utc).isoformat()),
                updated_at=None,
            ))

        return OutreachResponse(
            metadata=OutreachMetadata(
                generated_at=summary.get("generated_at", datetime.now(timezone.utc).isoformat()),
                total_drafts=len(drafts),
                with_emails=with_emails,
                without_emails=without_emails,
            ),
            drafts=drafts,
        )
    except Exception as e:
        logger.error(f"Failed to load outreach data: {e}")
        return OutreachResponse(
            metadata=OutreachMetadata(
                generated_at=datetime.now(timezone.utc).isoformat(),
                total_drafts=0,
                with_emails=0,
                without_emails=0,
            ),
            drafts=[],
        )


@router.get("", response_model=OutreachResponse)
async def get_outreach() -> OutreachResponse:
    """Get email drafts."""
    return _load_outreach_data()


@router.post("/run", response_model=StepRunResponse)
async def run_outreach() -> StepRunResponse:
    """Run the outreach generation step."""
    return StepRunResponse(
        success=True,
        message="Outreach generation started",
    )


@router.put("/{url:path}", response_model=EmailDraft)
async def update_outreach(url: str, update: EmailDraftUpdate) -> EmailDraft:
    """Update an email draft for a specific store URL."""
    # Decode the URL
    decoded_url = unquote(url)

    # Load current data
    outreach_data = _load_outreach_data()

    # Find the draft
    draft = None
    for d in outreach_data.drafts:
        if d.store_url == decoded_url:
            draft = d
            break

    if draft is None:
        raise HTTPException(status_code=404, detail=f"Draft not found for URL: {decoded_url}")

    # Return updated draft (in-memory only for now, file persistence not implemented)
    updated_draft = EmailDraft(
        store_url=draft.store_url,
        to_emails=draft.to_emails,
        subject=update.subject if update.subject is not None else draft.subject,
        body=update.body if update.body is not None else draft.body,
        issue_referenced=draft.issue_referenced,
        social=draft.social,
        status=update.status if update.status is not None else draft.status,
        created_at=draft.created_at,
        updated_at=datetime.now(timezone.utc).isoformat(),
    )

    return updated_draft
