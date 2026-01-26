#!/usr/bin/env python3
"""
Contact Extraction Script for Shopify UI Audit MVP.

This script extracts public business contact information from
verified Shopify stores.

Features:
- Checks /contact and /pages/contact pages
- Extracts footer emails
- Finds mailto: links
- Extracts social media links (Instagram, Facebook)
- Business contacts only - no guessing or enrichment

Usage:
    python scripts/extract_contacts.py [--url "https://example.com"]
"""

import sys
import json
import time
import random
import logging
import argparse
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Set, Optional
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import (
    USER_AGENTS_FILE,
    SHOPIFY_SITES_FILE,
    CONTACTS_FILE,
    CONTACT_PAGES,
    EXCLUDED_EMAIL_PATTERNS,
    MIN_REQUEST_DELAY,
    MAX_REQUEST_DELAY,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    LOG_LEVEL,
    LOG_FORMAT,
)

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Email regex pattern
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE
)

# Social media patterns
SOCIAL_PATTERNS = {
    "instagram": re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/([^/?\s]+)", re.IGNORECASE),
    "facebook": re.compile(r"(?:https?://)?(?:www\.)?facebook\.com/([^/?\s]+)", re.IGNORECASE),
    "twitter": re.compile(r"(?:https?://)?(?:www\.)?(?:twitter|x)\.com/([^/?\s]+)", re.IGNORECASE),
    "linkedin": re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/(?:company|in)/([^/?\s]+)", re.IGNORECASE),
    "tiktok": re.compile(r"(?:https?://)?(?:www\.)?tiktok\.com/@([^/?\s]+)", re.IGNORECASE),
}


class UserAgentRotator:
    """Manages rotation of user agents for requests."""

    def __init__(self, user_agents_file: Path):
        self.user_agents = self._load_user_agents(user_agents_file)
        if not self.user_agents:
            self.user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]

    def _load_user_agents(self, filepath: Path) -> List[str]:
        agents = []
        try:
            with open(filepath, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        agents.append(line)
        except FileNotFoundError:
            pass
        return agents

    def get_random(self) -> str:
        return random.choice(self.user_agents)


class RateLimiter:
    """Enforces rate limiting between requests."""

    def __init__(self, min_delay: float, max_delay: float):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0

    def wait(self):
        elapsed = time.time() - self.last_request_time
        delay = random.uniform(self.min_delay, self.max_delay)
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self.last_request_time = time.time()


class ContactExtractor:
    """Extracts contact information from websites."""

    def __init__(self, user_agent_rotator: UserAgentRotator, rate_limiter: RateLimiter):
        self.ua_rotator = user_agent_rotator
        self.rate_limiter = rate_limiter
        self.session = requests.Session()

    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch page HTML content."""
        self.rate_limiter.wait()

        headers = {
            "User-Agent": self.ua_rotator.get_random(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True,
                )
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 404:
                    return None
                response.raise_for_status()

            except requests.RequestException as e:
                logger.debug(f"Request failed for {url}: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 * (attempt + 1))

        return None

    def _is_valid_email(self, email: str) -> bool:
        """Check if email is valid and not excluded."""
        email_lower = email.lower()

        # Check against excluded patterns
        for pattern in EXCLUDED_EMAIL_PATTERNS:
            if pattern.lower() in email_lower:
                return False

        # Skip image file extensions that might match email pattern
        if email_lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
            return False

        # Skip obviously fake or placeholder emails
        fake_indicators = ['example.com', 'test.com', 'email.com', 'youremail', 'your@']
        for indicator in fake_indicators:
            if indicator in email_lower:
                return False

        # Skip technical/tracking service emails (Sentry, analytics, etc.)
        technical_domains = [
            'ingest.sentry.io',
            'sentry.io',
            'segment.io',
            'segment.com',
            'mixpanel.com',
            'amplitude.com',
            'intercom.io',
            'zendesk.com',
            'freshdesk.com',
            'klaviyo.com',
            'mailchimp.com',
            'sendgrid.net',
            'postmarkapp.com',
            'sparkpost.com',
        ]
        for domain in technical_domains:
            if domain in email_lower:
                return False

        # Skip emails with long hexadecimal strings (likely DSNs or tokens)
        # Extract the local part (before @)
        local_part = email_lower.split('@')[0] if '@' in email_lower else ''
        if len(local_part) > 20 and re.match(r'^[a-f0-9]+$', local_part):
            return False

        # Skip emails where domain contains numbers (often auto-generated)
        domain_part = email_lower.split('@')[1] if '@' in email_lower else ''
        # Allow common domains with numbers like o365.com but skip tracking pixels
        if re.match(r'o\d+\.ingest\.', domain_part):
            return False

        return True

    def _extract_emails_from_html(self, html: str) -> Set[str]:
        """Extract valid email addresses from HTML content."""
        emails = set()

        # Find all email patterns
        matches = EMAIL_PATTERN.findall(html)
        for email in matches:
            if self._is_valid_email(email):
                emails.add(email.lower())

        return emails

    def _extract_mailto_links(self, soup: BeautifulSoup) -> Set[str]:
        """Extract emails from mailto: links."""
        emails = set()

        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if href.startswith("mailto:"):
                # Extract email from mailto link
                email = href.replace("mailto:", "").split("?")[0].strip()
                if email and self._is_valid_email(email):
                    emails.add(email.lower())

        return emails

    def _extract_social_links(self, soup: BeautifulSoup, base_url: str) -> Dict[str, str]:
        """Extract social media profile links."""
        social_links = {}

        for link in soup.find_all("a", href=True):
            href = link.get("href", "")

            for platform, pattern in SOCIAL_PATTERNS.items():
                if platform in social_links:
                    continue  # Already found this platform

                match = pattern.search(href)
                if match:
                    username = match.group(1)
                    # Skip generic pages
                    if username.lower() not in ['share', 'sharer', 'intent', 'dialog']:
                        social_links[platform] = href

        return social_links

    def _extract_phone_numbers(self, html: str, soup: BeautifulSoup) -> Set[str]:
        """Extract phone numbers from page."""
        phones = set()

        # Look for tel: links
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if href.startswith("tel:"):
                phone = href.replace("tel:", "").strip()
                if phone:
                    phones.add(phone)

        # Look for common phone patterns in text
        phone_pattern = re.compile(
            r"(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}"
        )
        matches = phone_pattern.findall(html)
        for phone in matches[:5]:  # Limit to avoid false positives
            cleaned = re.sub(r"[^\d+]", "", phone)
            if len(cleaned) >= 10:
                phones.add(phone.strip())

        return phones

    def _extract_from_page(self, url: str, soup: BeautifulSoup, html: str) -> Dict:
        """Extract all contact info from a single page."""
        return {
            "emails": list(self._extract_emails_from_html(html) | self._extract_mailto_links(soup)),
            "social": self._extract_social_links(soup, url),
            "phones": list(self._extract_phone_numbers(html, soup)),
        }

    def _extract_footer_contacts(self, soup: BeautifulSoup, html: str, url: str) -> Dict:
        """Extract contact info specifically from footer section."""
        footer_info = {
            "emails": [],
            "social": {},
            "phones": [],
        }

        # Find footer element
        footer = soup.find("footer")
        if not footer:
            # Try common footer class names
            footer = soup.find(class_=re.compile(r"footer", re.IGNORECASE))

        if footer:
            footer_html = str(footer)
            footer_soup = BeautifulSoup(footer_html, "html.parser")

            info = self._extract_from_page(url, footer_soup, footer_html)
            footer_info["emails"] = info["emails"]
            footer_info["social"] = info["social"]
            footer_info["phones"] = info["phones"]

        return footer_info

    def extract(self, base_url: str) -> Dict:
        """
        Extract all contact information for a website.

        Args:
            base_url: Base URL of the website

        Returns:
            Dictionary with extracted contact information
        """
        logger.info(f"Extracting contacts from: {base_url}")

        result = {
            "url": base_url,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "emails": [],
            "phones": [],
            "social": {},
            "contact_page_found": False,
            "sources": [],
            "error": None,
        }

        all_emails = set()
        all_phones = set()
        all_social = {}

        try:
            # 1. Check homepage
            logger.info("  Checking homepage...")
            homepage_html = self._fetch_page(base_url)
            if homepage_html:
                soup = BeautifulSoup(homepage_html, "html.parser")

                # Extract from full page
                page_info = self._extract_from_page(base_url, soup, homepage_html)
                all_emails.update(page_info["emails"])
                all_phones.update(page_info["phones"])
                all_social.update(page_info["social"])

                # Extract specifically from footer
                footer_info = self._extract_footer_contacts(soup, homepage_html, base_url)
                all_emails.update(footer_info["emails"])
                all_phones.update(footer_info["phones"])
                all_social.update(footer_info["social"])

                result["sources"].append("homepage")

            # 2. Check contact pages
            for contact_path in CONTACT_PAGES:
                contact_url = urljoin(base_url, contact_path)
                logger.info(f"  Checking {contact_path}...")

                contact_html = self._fetch_page(contact_url)
                if contact_html:
                    result["contact_page_found"] = True
                    soup = BeautifulSoup(contact_html, "html.parser")

                    page_info = self._extract_from_page(contact_url, soup, contact_html)
                    all_emails.update(page_info["emails"])
                    all_phones.update(page_info["phones"])
                    all_social.update(page_info["social"])

                    result["sources"].append(contact_path)
                    break  # Found contact page, no need to check others

            # Compile results
            result["emails"] = sorted(list(all_emails))
            result["phones"] = sorted(list(all_phones))
            result["social"] = all_social

            # Log summary
            logger.info(f"  Found: {len(result['emails'])} emails, "
                       f"{len(result['phones'])} phones, "
                       f"{len(result['social'])} social profiles")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"  Error extracting contacts: {e}")

        return result


def load_shopify_sites() -> List[str]:
    """Load verified Shopify site URLs."""
    urls = []

    if not SHOPIFY_SITES_FILE.exists():
        logger.error(f"Shopify sites file not found: {SHOPIFY_SITES_FILE}")
        return urls

    try:
        with open(SHOPIFY_SITES_FILE, "r") as f:
            data = json.load(f)

        for site in data.get("shopify_sites", []):
            urls.append(site["url"])

        logger.info(f"Loaded {len(urls)} verified Shopify sites")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Shopify sites file: {e}")

    return urls


def main():
    """Main entry point for contact extraction."""
    parser = argparse.ArgumentParser(
        description="Extract contact information from Shopify stores"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Single URL to extract contacts from",
    )
    args = parser.parse_args()

    # Determine URLs to process
    if args.url:
        urls = [args.url]
        logger.info(f"Extracting contacts from single URL: {args.url}")
    else:
        urls = load_shopify_sites()
        if not urls:
            logger.error("No URLs to process. Run verify_shopify.py first.")
            sys.exit(1)

    # Initialize components
    ua_rotator = UserAgentRotator(USER_AGENTS_FILE)
    rate_limiter = RateLimiter(MIN_REQUEST_DELAY, MAX_REQUEST_DELAY)
    extractor = ContactExtractor(ua_rotator, rate_limiter)

    # Extract contacts for each URL
    results = []
    sites_with_contacts = 0

    for i, url in enumerate(urls, 1):
        logger.info(f"[{i}/{len(urls)}] Processing {url}")
        result = extractor.extract(url)
        results.append(result)

        if result["emails"] or result["social"]:
            sites_with_contacts += 1

    # Prepare output
    output = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_sites": len(results),
            "sites_with_contacts": sites_with_contacts,
            "total_emails_found": sum(len(r["emails"]) for r in results),
            "total_social_found": sum(len(r["social"]) for r in results),
        },
        "contacts": results,
    }

    # Ensure output directory exists
    CONTACTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    with open(CONTACTS_FILE, "w") as f:
        json.dump(output, f, indent=2)

    logger.info(f"Contact extraction complete. Results saved to {CONTACTS_FILE}")

    # Print summary
    print("\n" + "=" * 60)
    print("CONTACT EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"  Sites processed: {len(results)}")
    print(f"  Sites with contacts: {sites_with_contacts}")
    print(f"  Total emails found: {output['metadata']['total_emails_found']}")
    print(f"  Total social profiles: {output['metadata']['total_social_found']}")
    print("=" * 60)

    # Print individual results
    for result in results:
        url = result.get("url", "Unknown")
        emails = result.get("emails", [])
        social = result.get("social", {})
        phones = result.get("phones", [])

        print(f"\n  {url}")
        if emails:
            print(f"    Emails: {', '.join(emails[:3])}")
        if phones:
            print(f"    Phones: {', '.join(phones[:2])}")
        if social:
            platforms = ", ".join(social.keys())
            print(f"    Social: {platforms}")
        if not emails and not social and not phones:
            print("    No contacts found")

    print(f"\nOutput: {CONTACTS_FILE}")


if __name__ == "__main__":
    main()
