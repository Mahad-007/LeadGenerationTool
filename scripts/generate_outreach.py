#!/usr/bin/env python3
"""
Outreach Email Generation Script for Shopify UI Audit MVP.

This script generates professional, copy-paste-ready email drafts
based on UI audit findings and extracted contact information.

Features:
- Plain-text email format
- Professional, consultative tone
- References one specific issue per email
- No links in email body
- Copy-paste ready for manual sending
- No automated email sending

Usage:
    python scripts/generate_outreach.py [--url "https://example.com"]
"""

import sys
import json
import logging
import argparse
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional
from urllib.parse import urlparse

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import (
    AUDIT_RESULTS_FILE,
    CONTACTS_FILE,
    DRAFTS_DIR,
    SENDER_NAME,
    SENDER_TITLE,
    MAX_EMAIL_LENGTH,
    LOG_LEVEL,
    LOG_FORMAT,
)

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


# Email templates based on issue categories (design-focused)
EMAIL_TEMPLATES = {
    "typography": {
        "subject": "Typography suggestion for {store_name}",
        "body": """Hi there,

I was browsing {store_name} and noticed a typography issue that might be affecting readability.

{evidence}

Good typography is crucial for building trust and keeping visitors engaged. When text is hard to read, shoppers often leave without making a purchase.

I have some specific recommendations that could help if you're interested.

Best regards,
{sender_name}
{sender_title}"""
    },

    "layout": {
        "subject": "Design feedback for {store_name}",
        "body": """Hi there,

I was checking out {store_name} and noticed a layout issue that might be affecting the shopping experience.

{evidence}

These kinds of visual alignment issues can make a store feel less polished and potentially reduce trust with visitors.

I have some ideas on how to address this if you'd like to hear them.

Best regards,
{sender_name}
{sender_title}"""
    },

    "images": {
        "subject": "Image issue spotted on {store_name}",
        "body": """Hi there,

I was looking at {store_name} and noticed an issue with one of your images.

{evidence}

Product and hero images are often the first thing shoppers notice. When images don't display properly, it can hurt conversions.

Would you like me to point out exactly what I found?

Best regards,
{sender_name}
{sender_title}"""
    },

    "mobile": {
        "subject": "Mobile experience feedback for {store_name}",
        "body": """Hi there,

I viewed {store_name} on mobile and noticed something that might be impacting your mobile shoppers.

{evidence}

With over 60% of e-commerce traffic now coming from mobile devices, having a smooth mobile experience is crucial.

I'd be happy to share some specific recommendations if that would be helpful.

Best regards,
{sender_name}
{sender_title}"""
    },

    "contrast": {
        "subject": "Readability suggestion for {store_name}",
        "body": """Hi there,

I was browsing {store_name} and noticed a contrast issue that might be making some content harder to read.

{evidence}

Good color contrast is important not just for readability, but also for accessibility. Improving it can help more visitors engage with your content.

Would you be interested in some specific suggestions?

Best regards,
{sender_name}
{sender_title}"""
    },

    "hierarchy": {
        "subject": "Design opportunity for {store_name}",
        "body": """Hi there,

I was looking at {store_name} and noticed an opportunity to improve the visual hierarchy of your homepage.

{evidence}

A clear visual hierarchy helps guide visitors to take action. When the layout is confusing, shoppers may leave without finding what they need.

I'd be happy to share some ideas if you're interested.

Best regards,
{sender_name}
{sender_title}"""
    },

    "generic": {
        "subject": "Design improvement opportunity for {store_name}",
        "body": """Hi there,

I was looking at {store_name} and noticed an opportunity to improve the design.

{evidence}

Small design improvements like this can often have a meaningful impact on conversions.

Would you be open to a quick conversation about it?

Best regards,
{sender_name}
{sender_title}"""
    }
}


def get_store_name(url: str) -> str:
    """Extract a readable store name from URL."""
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")

    # Remove TLD and format nicely
    name = domain.split(".")[0]
    # Convert dashes/underscores to spaces and title case
    name = name.replace("-", " ").replace("_", " ").title()

    return name


def format_evidence(issue: Dict) -> str:
    """Format issue evidence for email body."""
    evidence = issue.get("evidence", "")
    description = issue.get("description", "")

    # Combine description and evidence
    if evidence and description:
        return f"{description} Specifically, {evidence.lower()}"
    elif description:
        return description
    elif evidence:
        return evidence
    else:
        return "I noticed an issue that could be affecting your conversions."


def select_best_issue(issues: List[Dict]) -> Optional[Dict]:
    """Select the best issue to highlight in outreach."""
    if not issues:
        return None

    # Prioritize by severity, then by category (design-focused)
    severity_order = {"high": 0, "medium": 1, "low": 2}
    category_order = {
        "images": 0,       # Most visible/actionable
        "layout": 1,       # Clear visual issues
        "mobile": 2,       # Important for conversions
        "hierarchy": 3,    # Design clarity
        "contrast": 4,     # Readability issues
        "typography": 5,   # Text issues
    }

    def sort_key(issue):
        severity = severity_order.get(issue.get("severity", "medium"), 1)
        category = category_order.get(issue.get("category", "generic"), 6)
        return (severity, category)

    sorted_issues = sorted(issues, key=sort_key)
    return sorted_issues[0]


def generate_email(
    url: str,
    issue: Dict,
    contact_info: Dict,
    sender_name: str = SENDER_NAME,
    sender_title: str = SENDER_TITLE,
) -> Dict:
    """
    Generate an email draft for a specific issue.

    Args:
        url: Store URL
        issue: Issue dictionary from analysis
        contact_info: Contact information for the store
        sender_name: Name to use in signature
        sender_title: Title to use in signature

    Returns:
        Email draft dictionary
    """
    store_name = get_store_name(url)
    category = issue.get("category", "generic")
    evidence = format_evidence(issue)

    # Get appropriate template
    template = EMAIL_TEMPLATES.get(category, EMAIL_TEMPLATES["generic"])

    # Format email
    subject = template["subject"].format(store_name=store_name)
    body = template["body"].format(
        store_name=store_name,
        evidence=evidence,
        sender_name=sender_name,
        sender_title=sender_title,
    )

    # Truncate if too long
    if len(body) > MAX_EMAIL_LENGTH:
        body = body[:MAX_EMAIL_LENGTH - 3] + "..."

    return {
        "subject": subject,
        "body": body,
        "to_emails": contact_info.get("emails", []),
        "store_url": url,
        "issue_referenced": {
            "title": issue.get("title", ""),
            "category": category,
            "severity": issue.get("severity", "medium"),
        },
    }


def generate_safe_filename(url: str) -> str:
    """Generate safe filename from URL."""
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    safe = re.sub(r"[^\w\-]", "_", domain)
    return safe


def load_audit_results() -> Dict:
    """Load audit results with analysis."""
    if not AUDIT_RESULTS_FILE.exists():
        logger.error(f"Audit results file not found: {AUDIT_RESULTS_FILE}")
        return {}

    try:
        with open(AUDIT_RESULTS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse audit results: {e}")
        return {}


def load_contacts() -> Dict:
    """Load contact information indexed by URL."""
    contacts_by_url = {}

    if not CONTACTS_FILE.exists():
        logger.warning(f"Contacts file not found: {CONTACTS_FILE}")
        return contacts_by_url

    try:
        with open(CONTACTS_FILE, "r") as f:
            data = json.load(f)

        for contact in data.get("contacts", []):
            url = contact.get("url")
            if url:
                contacts_by_url[url] = contact

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse contacts file: {e}")

    return contacts_by_url


def main():
    """Main entry point for outreach generation."""
    parser = argparse.ArgumentParser(
        description="Generate outreach email drafts based on audit findings"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Generate draft for specific URL only",
    )
    parser.add_argument(
        "--sender-name",
        type=str,
        default=SENDER_NAME,
        help=f"Sender name for signature (default: {SENDER_NAME})",
    )
    parser.add_argument(
        "--sender-title",
        type=str,
        default=SENDER_TITLE,
        help=f"Sender title for signature (default: {SENDER_TITLE})",
    )
    args = parser.parse_args()

    # Load data
    audit_data = load_audit_results()
    if not audit_data:
        logger.error("No audit data available. Run audit_homepage.py and analyze_with_gemini.py first.")
        sys.exit(1)

    contacts_by_url = load_contacts()

    # Ensure output directory exists
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    # Process audits
    drafts_generated = 0
    skipped_no_issues = 0
    skipped_no_contacts = 0

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "drafts": [],
    }

    for audit in audit_data.get("audits", []):
        url = audit.get("url")

        if not url:
            continue

        # Filter by URL if specified
        if args.url and url != args.url:
            continue

        logger.info(f"Processing: {url}")

        # Get analysis results
        analysis = audit.get("analysis", {})
        issues = analysis.get("issues", [])

        if not issues:
            logger.info(f"  Skipping - no issues found")
            skipped_no_issues += 1
            continue

        # Get contact info
        contact_info = contacts_by_url.get(url, {})
        if not contact_info.get("emails") and not contact_info.get("social"):
            logger.info(f"  Skipping - no contact information")
            skipped_no_contacts += 1
            continue

        # Select best issue
        best_issue = select_best_issue(issues)
        if not best_issue:
            continue

        # Generate email
        email = generate_email(
            url=url,
            issue=best_issue,
            contact_info=contact_info,
            sender_name=args.sender_name,
            sender_title=args.sender_title,
        )

        # Save draft to file
        filename = generate_safe_filename(url)
        draft_path = DRAFTS_DIR / f"{filename}.txt"

        draft_content = f"""================================================================================
OUTREACH DRAFT
================================================================================

Store: {url}
Generated: {datetime.now(timezone.utc).isoformat()}

--------------------------------------------------------------------------------
TO: {', '.join(email['to_emails']) if email['to_emails'] else 'No email found - check social media'}
--------------------------------------------------------------------------------

SUBJECT: {email['subject']}

--------------------------------------------------------------------------------
BODY:
--------------------------------------------------------------------------------

{email['body']}

--------------------------------------------------------------------------------
ISSUE REFERENCED:
--------------------------------------------------------------------------------
Category: {email['issue_referenced']['category']}
Severity: {email['issue_referenced']['severity']}
Title: {email['issue_referenced']['title']}

--------------------------------------------------------------------------------
CONTACT INFO:
--------------------------------------------------------------------------------
Emails: {', '.join(contact_info.get('emails', [])) or 'None found'}
Social: {', '.join(f"{k}: {v}" for k, v in contact_info.get('social', {}).items()) or 'None found'}

================================================================================
"""

        with open(draft_path, "w") as f:
            f.write(draft_content)

        logger.info(f"  Draft saved: {draft_path}")
        drafts_generated += 1

        # Add to summary
        summary["drafts"].append({
            "url": url,
            "file": str(draft_path),
            "subject": email["subject"],
            "to_emails": email["to_emails"],
            "issue_category": email["issue_referenced"]["category"],
        })

    # Save summary JSON
    summary_path = DRAFTS_DIR / "drafts_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("OUTREACH GENERATION SUMMARY")
    print("=" * 60)
    print(f"  Drafts generated: {drafts_generated}")
    print(f"  Skipped (no issues): {skipped_no_issues}")
    print(f"  Skipped (no contacts): {skipped_no_contacts}")
    print(f"  Output directory: {DRAFTS_DIR}")
    print("=" * 60)

    if summary["drafts"]:
        print("\nGenerated drafts:")
        for draft in summary["drafts"]:
            print(f"\n  {draft['url']}")
            print(f"    Subject: {draft['subject']}")
            print(f"    To: {', '.join(draft['to_emails']) if draft['to_emails'] else 'Check social media'}")
            print(f"    File: {draft['file']}")

    print(f"\nSummary saved to: {summary_path}")
    print("\nIMPORTANT: Review each draft before sending. Emails require manual sending.")


if __name__ == "__main__":
    main()
